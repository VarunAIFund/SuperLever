#!/usr/bin/env python3
"""
Extract all unique degrees from batch JSON files in data/output directory.

This script scans for files matching pattern batch_*_with_parsed.json
and extracts all degree names from education data to create a unique list.
"""

import json
import os
import glob
from collections import Counter
from typing import Set, List, Dict, Any

def extract_degrees_from_candidate(candidate: Dict[str, Any]) -> List[str]:
    """Extract degree names from a single candidate's education data"""
    degrees = []
    
    # Check if candidate has parsed_resume data
    parsed_resume = candidate.get('parsed_resume', {})
    schools = parsed_resume.get('schools', [])
    
    for school in schools:
        # Extract degree information from the degree field
        degree = school.get('degree', '')
        if isinstance(degree, str) and degree.strip():
            degrees.append(degree.strip())
        
        # Also check field if it exists and is different from degree
        field = school.get('field', '')
        if isinstance(field, str) and field.strip() and field.strip() != degree.strip():
            degrees.append(field.strip())
    
    return degrees

def process_batch_file(file_path: str) -> List[str]:
    """Process a single batch JSON file and extract all degrees"""
    print(f"Processing {os.path.basename(file_path)}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        
        all_degrees = []
        candidate_count = len(candidates) if isinstance(candidates, list) else 0
        
        if isinstance(candidates, list):
            for candidate in candidates:
                degrees = extract_degrees_from_candidate(candidate)
                all_degrees.extend(degrees)
        
        print(f"  Found {len(all_degrees)} degree entries from {candidate_count} candidates")
        return all_degrees
        
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return []

def main():
    """Main function to extract degrees from all batch files"""
    
    # Look for data/output directory (from test directory, go back to root then to data/output)
    data_dir = os.path.join("..", "data", "output")
    if not os.path.exists(data_dir):
        print(f"❌ Directory {data_dir} not found")
        print("Please ensure the script is run from the test directory")
        return
    
    # Find all batch files matching the pattern
    pattern = os.path.join(data_dir, "batch_*_with_parsed.json")
    batch_files = glob.glob(pattern)
    
    if not batch_files:
        print(f"❌ No files found matching pattern: {pattern}")
        return
    
    print(f"🔍 Found {len(batch_files)} batch files to process")
    print()
    
    # Process all files and collect degrees
    all_degrees = []
    
    for batch_file in sorted(batch_files):
        degrees = process_batch_file(batch_file)
        all_degrees.extend(degrees)
    
    # Count and deduplicate degrees
    degree_counter = Counter(all_degrees)
    unique_degrees = sorted(degree_counter.keys())
    
    print(f"\n📊 Statistics:")
    print(f"  Total degree entries: {len(all_degrees):,}")
    print(f"  Unique degrees: {len(unique_degrees):,}")
    
    # Save unique degrees to text file
    output_file = "unique_degrees.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unique Degrees Extracted from Candidate Data\n")
        f.write(f"# Total entries: {len(all_degrees):,}\n")
        f.write(f"# Unique degrees: {len(unique_degrees):,}\n")
        f.write("# Format: degree_name (count)\n\n")
        
        for degree in unique_degrees:
            count = degree_counter[degree]
            f.write(f"{degree} ({count})\n")
    
    print(f"\n✅ Saved {len(unique_degrees)} unique degrees to: {output_file}")
    
    # Show top 20 most common degrees
    print(f"\n🎓 Top 20 most common degrees:")
    for degree, count in degree_counter.most_common(20):
        print(f"  {count:3d}x {degree}")

if __name__ == "__main__":
    main()