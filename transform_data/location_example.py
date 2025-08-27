#!/usr/bin/env python3
"""
Example usage of location_utils for SuperLever candidate search

This script demonstrates how to use the location utilities to:
1. Add coordinates to candidate profiles
2. Search for candidates in a specific area
3. Filter by distance from office locations
"""

import json
from location_utils import LocationService

def main():
    location_service = LocationService()
    
    # Example 1: Add coordinates to existing structured profiles
    print("=== Adding coordinates to candidate profiles ===")
    try:
        location_service.add_coordinates_to_candidates(
            'structured_profiles.json',
            'candidates_with_locations.json'
        )
    except FileNotFoundError:
        print("structured_profiles.json not found. Run transform.py first.")
        return
    
    # Example 2: Find candidates near office locations
    print("\n=== Finding candidates near office locations ===")
    
    # Load candidates with coordinates
    try:
        with open('candidates_with_locations.json', 'r') as f:
            candidates = json.load(f)
    except FileNotFoundError:
        print("candidates_with_locations.json not found. Run the coordinate addition first.")
        return
    
    # Define office locations to search near
    office_locations = [
        "San Francisco, CA, USA",
        "New York, NY, USA", 
        "Seattle, WA, USA",
        "Austin, TX, USA"
    ]
    
    search_radius = 25  # miles
    
    for office in office_locations:
        print(f"\n--- Candidates within {search_radius} miles of {office} ---")
        nearby = location_service.find_candidates_in_radius(
            candidates, office, search_radius
        )
        
        if nearby:
            print(f"Found {len(nearby)} candidates:")
            for candidate in nearby[:5]:  # Show top 5
                print(f"  • {candidate['name']} - {candidate['distance_miles']} miles")
                print(f"    {candidate.get('current_title', 'N/A')} at {candidate.get('current_org', 'N/A')}")
        else:
            print("  No candidates found in this area")
    
    # Example 3: Analyze candidate distribution
    print("\n=== Candidate location distribution ===")
    city_groups = location_service.group_candidates_by_city(candidates)
    
    print(f"Candidates distributed across {len(city_groups)} cities:")
    for city, city_candidates in sorted(city_groups.items(), key=lambda x: len(x[1]), reverse=True):
        if len(city_candidates) > 0:
            print(f"  • {city}: {len(city_candidates)} candidates")
    
    # Example 4: Create a location-filtered search
    print("\n=== Custom location search ===")
    target_skills = ["Python", "Machine Learning", "AI"]
    target_location = "San Francisco, CA, USA"
    max_distance = 50
    
    # Find candidates with target skills near target location
    skilled_nearby = []
    nearby_candidates = location_service.find_candidates_in_radius(
        candidates, target_location, max_distance
    )
    
    for candidate in nearby_candidates:
        candidate_skills = candidate.get('skills', [])
        if any(skill in str(candidate_skills).lower() for skill in [s.lower() for s in target_skills]):
            skilled_nearby.append(candidate)
    
    print(f"Found {len(skilled_nearby)} candidates with relevant skills near {target_location}:")
    for candidate in skilled_nearby:
        print(f"  • {candidate['name']} - {candidate['distance_miles']} miles")
        print(f"    Skills: {', '.join(candidate.get('skills', [])[:3])}...")  # Show first 3 skills

if __name__ == "__main__":
    main()