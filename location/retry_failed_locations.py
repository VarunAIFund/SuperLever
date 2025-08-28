#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry Failed Location Standardization Script

This script reads the standardized_batch_locations.json file, finds all entries
marked as "FAILED", and retries standardization using the exact same logic
as the original standardize_location.py script.
"""

import requests
import time
import json
from pathlib import Path


class FailedLocationRetrier:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://us1.locationiq.com/v1/search.php"
        self.standardized_locations = {}
        self.failed_locations = []
        
    def standardize_location(self, location_text):
        """Standardize a single location using LocationIQ API - same logic as original."""
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
        """Extract and format location components from LocationIQ API response - same logic as original."""
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
    
    def retry_failed_locations(self, input_file='standardized_batch_locations.json', max_retries=None):
        """Read the file, find FAILED entries, and retry standardization."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: {input_file} not found!")
            return
        
        print(f"Reading failed locations from {input_file}...")
        
        # Read JSON file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Total entries in file: {len(data)}")
        
        # Find all FAILED entries
        failed_entries = {location: status for location, status in data.items() if status == "FAILED"}
        print(f"Found {len(failed_entries)} FAILED entries")
        
        if len(failed_entries) == 0:
            print("No failed entries found! Nothing to retry.")
            return
        
        # Convert to list for processing
        failed_locations = list(failed_entries.keys())
        
        # Apply retry limit if specified
        if max_retries and max_retries < len(failed_locations):
            failed_locations = failed_locations[:max_retries]
            print(f"Limited to {max_retries} retry attempts")
        
        print(f"Retrying {len(failed_locations)} failed locations...")
        print("Starting retry process...")
        print("-" * 60)
        
        # Keep track of successful retries
        successful_retries = 0
        still_failed = 0
        
        for i, location in enumerate(failed_locations, 1):
            print(f"Retry {i}/{len(failed_locations)}: {location}")
            
            standardized = self.standardize_location(location)
            
            if standardized:
                self.standardized_locations[location] = standardized
                data[location] = standardized  # Update in the main data structure
                successful_retries += 1
                print(f"  ✅ SUCCESS → {standardized}")
            else:
                self.failed_locations.append(location)
                # Keep as FAILED in the data
                still_failed += 1
                print(f"  ❌ STILL FAILED")
            
            # Save results after each location to prevent data loss
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Rate limiting - LocationIQ allows 2 requests/second
            time.sleep(0.5)  # 0.5 second delay = 2 requests per second
        
        # Final save
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved back to: {input_file}")
        
        # Also update the text file
        text_output = input_file.replace('.json', '.txt')
        with open(text_output, 'w', encoding='utf-8') as f:
            f.write("Original Location → Standardized Location\n")
            f.write("=" * 50 + "\n\n")
            
            for original, standardized in data.items():
                if standardized != "FAILED":
                    f.write(f"{original} → {standardized}\n")
                else:
                    f.write(f"{original} → FAILED\n")
        
        print(f"Text version updated: {text_output}")
        
        # Print summary
        self._print_retry_summary(successful_retries, still_failed, len(failed_locations))
    
    def _print_retry_summary(self, successful_retries, still_failed, total_attempted):
        """Print summary of retry results."""
        print(f"\n{'='*60}")
        print("RETRY SUMMARY")
        print(f"{'='*60}")
        print(f"Total retry attempts: {total_attempted}")
        print(f"Successful retries: {successful_retries}")
        print(f"Still failed: {still_failed}")
        print(f"Success rate: {successful_retries / total_attempted * 100:.1f}%")
        
        if self.failed_locations:
            print(f"\nStill failing locations:")
            for failed in self.failed_locations[:10]:  # Show first 10
                print(f"  - {failed}")
            if len(self.failed_locations) > 10:
                print(f"  ... and {len(self.failed_locations) - 10} more")


def main():
    """Main function to run the failed location retrier."""
    # Your LocationIQ API key - same as original
    API_KEY = "pk.7edffe53b79fbef5e4daf6771ef7cc00"
    
    print("Failed Location Retrier using LocationIQ API")
    print("=" * 50)
    print("This script retries all FAILED entries from standardized_batch_locations.json")
    print()
    
    # Get user input for retry limit
    try:
        max_retries = input("Enter number of failed locations to retry (or press Enter for all): ").strip()
        if max_retries:
            max_retries = int(max_retries)
            print(f"Will retry up to {max_retries} failed locations")
        else:
            max_retries = None
            print("Will retry all failed locations")
    except ValueError:
        print("Invalid input. Will retry all failed locations.")
        max_retries = None
    
    # Initialize retrier
    retrier = FailedLocationRetrier(API_KEY)
    
    # Retry failed locations
    retrier.retry_failed_locations(max_retries=max_retries)


if __name__ == "__main__":
    main()