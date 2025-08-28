#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location Standardization Script

This script uses LocationIQ Geocoding API to standardize location data from locations.txt
and creates a standardized version with proper formatting.
"""

import requests
import time
import json
from pathlib import Path


class LocationStandardizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://us1.locationiq.com/v1/search.php"
        self.standardized_locations = {}
        self.failed_locations = []
        
    def standardize_location(self, location_text):
        """Standardize a single location using LocationIQ API."""
        params = {
            'key': self.api_key,
            'q': location_text,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = data[0]  # LocationIQ returns array directly
                
                # Extract standardized location components
                standardized = self._extract_location_components(result)
                return standardized
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API request failed for '{location_text}': {e}")
            return None
        except Exception as e:
            print(f"Error processing '{location_text}': {e}")
            return None
    
    def _extract_location_components(self, result):
        """Extract and format location components from LocationIQ API response."""
        # Build standardized location string in format: City, State/Province, Country
        parts = []
        
        # Get address components
        address = result.get('address', {})
        
        # City (priority order)
        city = None
        if address.get('city'):
            city = address['city']
        elif address.get('town'):
            city = address['town']
        elif address.get('village'):
            city = address['village']
        elif address.get('suburb'):
            city = address['suburb']
        
        if city:
            parts.append(city)
        
        # State/Province
        if address.get('state'):
            parts.append(address['state'])
        elif address.get('province'):
            parts.append(address['province'])
        elif address.get('county'):
            parts.append(address['county'])
        
        # Country (use API's standardized country name)
        if address.get('country'):
            parts.append(address['country'])
        
        # If we have at least city and country, return the formatted string
        if len(parts) >= 2:
            # Remove duplicate city/state names
            cleaned_parts = []
            for part in parts:
                if part not in cleaned_parts:
                    cleaned_parts.append(part)
            
            return ', '.join(cleaned_parts)
        
        # Fallback: use display_name if available, but clean it up
        if result.get('display_name'):
            display_name = result['display_name']
            # Remove zip codes, postal codes, and other unnecessary details
            # This is a simple cleanup - remove anything that looks like a postal code
            import re
            # Remove postal codes (5 digits, or 5+4 format)
            display_name = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', display_name)
            # Remove extra commas and clean up
            display_name = re.sub(r',\s*,', ',', display_name)
            display_name = display_name.strip(' ,')
            return display_name
        
        return None
    
    def process_locations_file(self, input_file='batch_locations_001_121.json', output_file='standardized_batch_locations.json', max_locations=None):
        """Process locations from batch JSON file and save standardized versions."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: {input_file} not found!")
            return
        
        print(f"Reading locations from {input_file}...")
        
        # Read JSON file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract locations from JSON
        if isinstance(data, dict) and 'locations' in data:
            locations = data['locations']
            print(f"Found {len(locations)} unique locations in JSON")
        elif isinstance(data, list):
            locations = data
            print(f"Found {len(locations)} locations in JSON array")
        else:
            print("Error: Invalid JSON format. Expected 'locations' key or array.")
            return
        
        # Check if output file already exists and load existing progress
        existing_data = {}
        if Path(output_file).exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                print(f"Found existing output file with {len(existing_data)} already processed locations")
                
                # Filter out already processed locations
                original_count = len(locations)
                locations = [loc for loc in locations if loc not in existing_data]
                print(f"Remaining locations to process: {len(locations)}")
                
                if len(locations) == 0:
                    print("All locations already processed! No work to do.")
                    return
                    
            except Exception as e:
                print(f"Warning: Could not read existing output file: {e}")
                print("Starting fresh processing...")
        
        # Apply location limit AFTER filtering out already processed ones
        if max_locations and max_locations < len(locations):
            locations = locations[:max_locations]
            print(f"Limited to {max_locations} locations from remaining unprocessed locations")
        
        print(f"Processing {len(locations)} locations...")
        print("Starting standardization process...")
        
        # Start with existing data
        output_data = existing_data.copy()
        
        for i, location in enumerate(locations, 1):
            total_processed = len(existing_data) + i
            total_remaining = len(locations) - i
            print(f"Processing {i}/{len(locations)} (Total: {total_processed}, Remaining: {total_remaining}): {location}")
            
            standardized = self.standardize_location(location)
            
            if standardized:
                self.standardized_locations[location] = standardized
                output_data[location] = standardized  # Simple key-value format
                print(f"  → {standardized}")
            else:
                self.failed_locations.append(location)
                output_data[location] = "FAILED"  # Mark failed locations
                print(f"  → Failed to standardize")
            
            # Save results after each location to prevent data loss
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Rate limiting - LocationIQ allows 2 requests/second
            # Adding delay to respect the rate limit
            time.sleep(0.5)  # 0.5 second delay = 2 requests per second
        
        # Save results to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Also save to text file for easy reading
        text_output = output_file.replace('.json', '.txt')
        with open(text_output, 'w', encoding='utf-8') as f:
            f.write("Original Location → Standardized Location\n")
            f.write("=" * 50 + "\n\n")
            
            for original, standardized in output_data.items():
                if standardized != "FAILED":
                    f.write(f"{original} → {standardized}\n")
                else:
                    f.write(f"{original} → FAILED\n")
        
        print(f"Text version saved to: {text_output}")
        
        # Print summary
        self._print_summary()
    
    def _write_summary_to_file(self, output_file):
        """Write summary information to the output file."""
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*50}\n")
            f.write("SUMMARY\n")
            f.write(f"{'='*50}\n")
            f.write(f"Total locations processed: {len(self.standardized_locations) + len(self.failed_locations)}\n")
            f.write(f"Successfully standardized: {len(self.standardized_locations)}\n")
            f.write(f"Failed to standardize: {len(self.failed_locations)}\n")
            
            if self.failed_locations:
                f.write(f"\nFailed locations:\n")
                f.write("-" * 30 + "\n")
                for failed in self.failed_locations:
                    f.write(f"{failed}\n")
        
        print(f"\nResults written to: {output_file}")
    
    def _print_summary(self):
        """Print summary of standardization results."""
        print(f"\n{'='*50}")
        print("STANDARDIZATION SUMMARY")
        print(f"{'='*50}")
        print(f"Total locations processed: {len(self.standardized_locations) + len(self.failed_locations)}")
        print(f"Successfully standardized: {len(self.standardized_locations)}")
        print(f"Failed to standardize: {len(self.failed_locations)}")
        print(f"Success rate: {len(self.standardized_locations) / (len(self.standardized_locations) + len(self.failed_locations)) * 100:.1f}%")
        
        if self.failed_locations:
            print(f"\nFailed locations:")
            for failed in self.failed_locations[:10]:  # Show first 10
                print(f"  - {failed}")
            if len(self.failed_locations) > 10:
                print(f"  ... and {len(self.failed_locations) - 10} more")


def main():
    """Main function to run the location standardizer."""
    # Your LocationIQ API key
    API_KEY =  "pk.7edffe53b79fbef5e4daf6771ef7cc00" #"pk.d8a8d156dc65648819343335849bc40c"   #
    
    print("Location Standardizer using LocationIQ API")
    print("=" * 40)
    
    # Get user input for location limit
    try:
        max_locations = input("Enter number of locations to standardize (or press Enter for all): ").strip()
        if max_locations:
            max_locations = int(max_locations)
            print(f"Will standardize up to {max_locations} locations")
        else:
            max_locations = None
            print("Will standardize all locations")
    except ValueError:
        print("Invalid input. Will standardize all locations.")
        max_locations = None
    
    # Initialize standardizer
    standardizer = LocationStandardizer(API_KEY)
    
    # Process locations with limit
    standardizer.process_locations_file(max_locations=max_locations)


if __name__ == "__main__":
    main() 