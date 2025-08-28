#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Unique Locations from Batch Files

This script reads batch files from 001 to 121 and extracts all unique locations,
saving them to a JSON file with one location per entry.
"""

import json
import os
from pathlib import Path
from collections import Counter


def extract_locations_from_batch_file(file_path):
    """Extract all locations from a single batch file."""
    locations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract locations from candidates (data is an array of candidates)
        if isinstance(data, list):
            for candidate in data:
                location = candidate.get('location', '').strip()
                if location and location not in ['', 'N/A', 'n/a', 'NA', 'null']:
                    locations.append(location)
        # Fallback: check if it's a single candidate object
        elif isinstance(data, dict) and 'location' in data:
            location = data.get('location', '').strip()
            if location and location not in ['', 'N/A', 'n/a', 'NA', 'null']:
                locations.append(location)
        
        print(f"  Found {len(locations)} locations in {os.path.basename(file_path)}")
        return locations
        
    except FileNotFoundError:
        print(f"  File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"  Error parsing {file_path}: {e}")
        return []
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return []


def extract_all_batch_locations():
    """Extract locations from all batch files 001 to 121."""
    base_path = "/Users/varunsharma/Desktop/output copy"
    all_locations = []
    
    print("Extracting locations from batch files...")
    print("=" * 50)
    
    # Process files from 001 to 121
    for batch_num in range(1, 122):
        # Format batch number with leading zeros
        batch_str = f"batch_{batch_num:03d}_with_parsed.json"
        file_path = os.path.join(base_path, batch_str)
        
        print(f"Processing {batch_str}...")
        
        locations = extract_locations_from_batch_file(file_path)
        all_locations.extend(locations)
    
    print(f"\nTotal locations found: {len(all_locations)}")
    
    # Get unique locations and count frequency
    location_counter = Counter(all_locations)
    unique_locations = list(location_counter.keys())
    
    print(f"Unique locations: {len(unique_locations)}")
    
    # Create output data structure
    output_data = {
        "metadata": {
            "total_locations_extracted": len(all_locations),
            "unique_locations": len(unique_locations),
            "batch_files_processed": 121,
            "batch_range": "001-121"
        },
        "locations": unique_locations,
        "location_frequency": dict(location_counter.most_common())
    }
    
    # Save to JSON file
    output_file = "batch_locations_001_121.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Also save just the locations list to a simple text file
    text_file = "batch_locations_001_121.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        for location in unique_locations:
            f.write(f"{location}\n")
    
    print(f"Locations also saved to: {text_file}")
    
    # Print some statistics
    print(f"\n{'='*50}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*50}")
    print(f"Batch files processed: 001-121")
    print(f"Total locations extracted: {len(all_locations):,}")
    print(f"Unique locations found: {len(unique_locations):,}")
    print(f"Duplicate locations: {len(all_locations) - len(unique_locations):,}")
    
    # Show top 10 most frequent locations
    print(f"\nTop 10 most frequent locations:")
    for i, (location, count) in enumerate(location_counter.most_common(10), 1):
        print(f"  {i:2d}. {location} ({count} occurrences)")
    
    return output_data


def main():
    """Main function to run the location extraction."""
    print("Batch Location Extractor")
    print("Extracting locations from batch_001 to batch_121")
    print("=" * 60)
    
    try:
        result = extract_all_batch_locations()
        print(f"\n✅ Extraction completed successfully!")
        print(f"📁 Results saved to: batch_locations_001_121.json")
        print(f"📄 Text version saved to: batch_locations_001_121.txt")
        
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("Please check the file paths and permissions.")


if __name__ == "__main__":
    main() 