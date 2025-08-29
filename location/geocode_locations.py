#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location Geocoding Script

This script reads standardized_batch_locations.json and gets latitude/longitude
coordinates for all successfully standardized locations using LocationIQ API.
Creates geographic coordinate data for location-based candidate searches.
"""

import requests
import time
import json
import csv
from pathlib import Path
from collections import defaultdict


class LocationGeocoder:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://us1.locationiq.com/v1/search.php"
        self.geocoded_locations = {}
        self.failed_geocoding = []
        
    def geocode_location(self, location_text):
        """Get latitude/longitude coordinates for a standardized location."""
        params = {
            'key': self.api_key,
            'q': location_text,
            'format': 'json',
            'limit': 1,
            'addressdetails': 0  # We don't need address details, just coordinates
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = data[0]
                
                # Extract coordinates
                lat = float(result.get('lat', 0))
                lng = float(result.get('lon', 0))
                
                return {
                    'lat': lat,
                    'lng': lng,
                    'display_name': result.get('display_name', location_text),
                    'importance': result.get('importance', 0)
                }
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API request failed for '{location_text}': {e}")
            return None
        except Exception as e:
            print(f"Error processing '{location_text}': {e}")
            return None
    
    def process_standardized_locations(self, input_file='standardized_batch_locations.json', 
                                     output_file='geocoded_locations.json', max_locations=None):
        """Process standardized locations and get coordinates for each."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: {input_file} not found!")
            return
        
        print(f"Reading standardized locations from {input_file}...")
        
        # Read standardized locations
        with open(input_path, 'r', encoding='utf-8') as f:
            standardized_data = json.load(f)
        
        print(f"Total entries in file: {len(standardized_data)}")
        
        # Filter out FAILED entries and get unique standardized locations
        successful_standardized = {}
        original_to_standardized = {}
        
        for original_location, standardized_location in standardized_data.items():
            if standardized_location != "FAILED":
                # Track which original locations map to this standardized location
                if standardized_location not in successful_standardized:
                    successful_standardized[standardized_location] = []
                successful_standardized[standardized_location].append(original_location)
                original_to_standardized[original_location] = standardized_location
        
        unique_standardized = list(successful_standardized.keys())
        print(f"Found {len(unique_standardized)} unique standardized locations to geocode")
        
        # Check if output file already exists and load existing progress
        existing_geocoded = {}
        if Path(output_file).exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_geocoded = json.load(f)
                print(f"Found existing output file with {len(existing_geocoded)} already geocoded locations")
                
                # Filter out already processed locations
                original_count = len(unique_standardized)
                unique_standardized = [loc for loc in unique_standardized if loc not in existing_geocoded]
                print(f"Remaining locations to geocode: {len(unique_standardized)}")
                
                if len(unique_standardized) == 0:
                    print("All locations already geocoded! No work to do.")
                    return
                    
            except Exception as e:
                print(f"Warning: Could not read existing output file: {e}")
                print("Starting fresh geocoding...")
        
        # Apply location limit AFTER filtering out already processed ones
        if max_locations and max_locations < len(unique_standardized):
            unique_standardized = unique_standardized[:max_locations]
            print(f"Limited to {max_locations} locations from remaining unprocessed locations")
        
        print(f"Geocoding {len(unique_standardized)} locations...")
        print("Starting geocoding process...")
        print("-" * 60)
        
        # Start with existing data
        output_data = existing_geocoded.copy()
        
        successful_geocoded = 0
        failed_geocoded = 0
        
        for i, standardized_location in enumerate(unique_standardized, 1):
            total_processed = len(existing_geocoded) + i
            remaining = len(unique_standardized) - i
            
            print(f"Geocoding {i}/{len(unique_standardized)} (Total: {total_processed}, Remaining: {remaining})")
            print(f"  Location: {standardized_location}")
            
            # Get original locations that map to this standardized location
            original_locations = successful_standardized[standardized_location]
            
            geocoded = self.geocode_location(standardized_location)
            
            if geocoded:
                location_data = {
                    'lat': geocoded['lat'],
                    'lng': geocoded['lng'],
                    'display_name': geocoded['display_name'],
                    'importance': geocoded['importance'],
                    'original_locations': original_locations,
                    'original_count': len(original_locations)
                }
                
                output_data[standardized_location] = location_data
                successful_geocoded += 1
                
                print(f"  ✅ SUCCESS → ({geocoded['lat']:.4f}, {geocoded['lng']:.4f})")
                print(f"     Covers {len(original_locations)} original location variations")
            else:
                self.failed_geocoding.append(standardized_location)
                failed_geocoded += 1
                print(f"  ❌ FAILED to geocode")
            
            # Save results after each location to prevent data loss
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Rate limiting - LocationIQ allows 2 requests/second
            time.sleep(0.5)  # 0.5 second delay = 2 requests per second
        
        # Final save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Create CSV output for easy import into mapping tools
        self._create_csv_output(output_data, output_file.replace('.json', '.csv'))
        
        # Create reverse mapping file (original → coordinates)
        self._create_reverse_mapping(output_data, original_to_standardized, 
                                   output_file.replace('.json', '_reverse_mapping.json'))
        
        # Print summary
        self._print_geocoding_summary(successful_geocoded, failed_geocoded, 
                                    len(unique_standardized), len(output_data))
    
    def _create_csv_output(self, geocoded_data, csv_file):
        """Create CSV output for easy import into mapping tools."""
        print(f"Creating CSV output: {csv_file}")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'standardized_location', 'latitude', 'longitude', 'display_name', 
                'importance', 'original_count', 'original_locations'
            ])
            
            # Write data rows
            for standardized_location, location_data in geocoded_data.items():
                writer.writerow([
                    standardized_location,
                    location_data['lat'],
                    location_data['lng'],
                    location_data['display_name'],
                    location_data['importance'],
                    location_data['original_count'],
                    '; '.join(location_data['original_locations'])
                ])
        
        print(f"CSV file created: {csv_file}")
    
    def _create_reverse_mapping(self, geocoded_data, original_to_standardized, reverse_file):
        """Create reverse mapping from original locations to coordinates."""
        print(f"Creating reverse mapping: {reverse_file}")
        
        reverse_mapping = {}
        
        for original_location, standardized_location in original_to_standardized.items():
            if standardized_location in geocoded_data:
                location_data = geocoded_data[standardized_location]
                reverse_mapping[original_location] = {
                    'standardized_location': standardized_location,
                    'lat': location_data['lat'],
                    'lng': location_data['lng'],
                    'display_name': location_data['display_name']
                }
        
        with open(reverse_file, 'w', encoding='utf-8') as f:
            json.dump(reverse_mapping, f, indent=2, ensure_ascii=False)
        
        print(f"Reverse mapping created: {reverse_file}")
    
    def _print_geocoding_summary(self, successful, failed, attempted, total_in_output):
        """Print summary of geocoding results."""
        print(f"\n{'='*60}")
        print("GEOCODING SUMMARY")
        print(f"{'='*60}")
        print(f"Locations attempted this run: {attempted}")
        print(f"Successfully geocoded this run: {successful}")
        print(f"Failed this run: {failed}")
        print(f"Total locations in output file: {total_in_output}")
        
        if attempted > 0:
            print(f"Success rate this run: {successful / attempted * 100:.1f}%")
        
        if self.failed_geocoding:
            print(f"\nFailed to geocode:")
            for failed in self.failed_geocoding[:10]:  # Show first 10
                print(f"  - {failed}")
            if len(self.failed_geocoding) > 10:
                print(f"  ... and {len(self.failed_geocoding) - 10} more")
        
        print(f"\n📁 Output files created:")
        print(f"  - geocoded_locations.json (main output)")
        print(f"  - geocoded_locations.csv (for mapping tools)")
        print(f"  - geocoded_locations_reverse_mapping.json (original → coordinates)")


def main():
    """Main function to run the location geocoder."""
    # Your LocationIQ API key
    API_KEY = "pk.7edffe53b79fbef5e4daf6771ef7cc00"
    
    print("Location Geocoder using LocationIQ API")
    print("=" * 50)
    print("This script geocodes standardized locations to get lat/lng coordinates")
    print("Enables geographic searches and location-based candidate filtering")
    print()
    
    # Get user input for location limit
    try:
        max_locations = input("Enter number of locations to geocode (or press Enter for all): ").strip()
        if max_locations:
            max_locations = int(max_locations)
            print(f"Will geocode up to {max_locations} locations")
        else:
            max_locations = None
            print("Will geocode all standardized locations")
    except ValueError:
        print("Invalid input. Will geocode all locations.")
        max_locations = None
    
    # Initialize geocoder
    geocoder = LocationGeocoder(API_KEY)
    
    # Process locations
    geocoder.process_standardized_locations(max_locations=max_locations)


if __name__ == "__main__":
    main()