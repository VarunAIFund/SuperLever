#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Location Script

This script directly reads test.json and extracts locations with their frequency,
outputting only the locations sorted by frequency.
"""

import json
from collections import Counter


def extract_location():
    """Extract locations from test.json and output frequency list."""
    
    print("Reading locations from test.json...")
    
    # Load test data
    try:
        with open('test.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        print(f"Loaded {len(test_data)} candidates from test.json")
    except FileNotFoundError:
        print("ERROR: test.json not found.")
        return
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing test.json: {e}")
        return
    
    # Extract locations and count frequency
    location_frequency = Counter()
    candidates_with_location = 0
    candidates_without_location = 0
    
    for candidate in test_data:
        location = candidate.get('location', '').strip()
        
        if location and location not in ['', 'N/A', 'n/a', 'NA', 'null']:
            location_frequency[location] += 1
            candidates_with_location += 1
        else:
            candidates_without_location += 1
    
    print(f"Found {len(location_frequency)} unique locations")
    print(f"Candidates with location: {candidates_with_location}")
    print(f"Candidates without location: {candidates_without_location}")
    
    # Write locations by frequency to text file
    output_file = 'locations_by_frequency.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for location, count in location_frequency.most_common():
            f.write(f"{location} ({count} candidates)\n")
    
    print(f"Created: {output_file}")
    
    # Write unique locations to locations.txt
    locations_file = 'locations.txt'
    with open(locations_file, 'w', encoding='utf-8') as f:
        for location in sorted(location_frequency.keys()):
            f.write(f"{location}\n")
    
    print(f"Created: {locations_file}")


if __name__ == "__main__":
    extract_location()