import json
import requests
import time
from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocationService:
    """
    Service for geocoding locations and performing geographic searches on candidate data
    Uses OpenStreetMap Nominatim API (free, no API key required)
    """
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'SuperLever-Candidate-Search/1.0 (contact@example.com)'
        }
        self.cache = {}
    
    def geocode_location(self, location: str) -> Optional[Dict]:
        """
        Convert a location string to coordinates using Nominatim API
        
        Args:
            location: Location string (e.g., "San Francisco, CA, USA")
            
        Returns:
            Dict with lat, lon, and formatted address or None if not found
        """
        if location in self.cache:
            return self.cache[location]
        
        try:
            params = {
                'q': location,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            # Rate limiting - be respectful to free API
            time.sleep(1)
            
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'formatted_address': data[0]['display_name'],
                    'city': data[0].get('address', {}).get('city', ''),
                    'state': data[0].get('address', {}).get('state', ''),
                    'country': data[0].get('address', {}).get('country', '')
                }
                self.cache[location] = result
                return result
            
        except Exception as e:
            logger.error(f"Error geocoding location '{location}': {str(e)}")
        
        return None
    
    def calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """
        Calculate distance between two coordinate points in miles
        
        Args:
            loc1: Dict with 'lat' and 'lon' keys
            loc2: Dict with 'lat' and 'lon' keys
            
        Returns:
            Distance in miles
        """
        try:
            point1 = (loc1['lat'], loc1['lon'])
            point2 = (loc2['lat'], loc2['lon'])
            return geodesic(point1, point2).miles
        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            return float('inf')
    
    def find_candidates_in_radius(self, candidates: List[Dict], center_location: str, radius_miles: float) -> List[Dict]:
        """
        Find candidates within a radius of a center location
        
        Args:
            candidates: List of candidate profile dictionaries
            center_location: Center location string (e.g., "New York, NY")
            radius_miles: Radius in miles
            
        Returns:
            List of candidates within the radius with distance added
        """
        center_coords = self.geocode_location(center_location)
        if not center_coords:
            logger.error(f"Could not geocode center location: {center_location}")
            return []
        
        candidates_in_radius = []
        
        for candidate in candidates:
            location = candidate.get('location', '')
            if not location:
                continue
                
            candidate_coords = self.geocode_location(location)
            if not candidate_coords:
                continue
            
            distance = self.calculate_distance(center_coords, candidate_coords)
            
            if distance <= radius_miles:
                candidate_with_distance = candidate.copy()
                candidate_with_distance['distance_miles'] = round(distance, 2)
                candidate_with_distance['coordinates'] = candidate_coords
                candidates_in_radius.append(candidate_with_distance)
        
        # Sort by distance
        candidates_in_radius.sort(key=lambda x: x['distance_miles'])
        return candidates_in_radius
    
    def group_candidates_by_city(self, candidates: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group candidates by city
        
        Args:
            candidates: List of candidate profile dictionaries
            
        Returns:
            Dict with city names as keys and list of candidates as values
        """
        city_groups = {}
        
        for candidate in candidates:
            location = candidate.get('location', '')
            if not location:
                continue
                
            coords = self.geocode_location(location)
            if coords:
                city = coords.get('city', 'Unknown')
                if city not in city_groups:
                    city_groups[city] = []
                
                candidate_with_coords = candidate.copy()
                candidate_with_coords['coordinates'] = coords
                city_groups[city].append(candidate_with_coords)
        
        return city_groups
    
    def add_coordinates_to_candidates(self, input_file: str, output_file: str):
        """
        Add coordinate data to all candidates in a file
        
        Args:
            input_file: Path to input JSON file with candidates
            output_file: Path to output JSON file with coordinates added
        """
        with open(input_file, 'r') as f:
            candidates = json.load(f)
        
        enhanced_candidates = []
        
        for i, candidate in enumerate(candidates):
            print(f"Processing candidate {i+1}/{len(candidates)}: {candidate.get('name', 'Unknown')}")
            
            location = candidate.get('location', '')
            if location:
                coords = self.geocode_location(location)
                if coords:
                    candidate['coordinates'] = coords
                    candidate['city'] = coords.get('city', '')
                    candidate['state'] = coords.get('state', '')
                    candidate['country'] = coords.get('country', '')
            
            enhanced_candidates.append(candidate)
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_candidates, f, indent=2)
        
        print(f"Enhanced {len(enhanced_candidates)} candidates with location data")
        print(f"Results saved to: {output_file}")

# Example usage functions
def search_candidates_near_location():
    """Example: Find candidates near a specific location"""
    location_service = LocationService()
    
    # Load candidates
    with open('structured_profiles.json', 'r') as f:
        candidates = json.load(f)
    
    # Find candidates within 50 miles of San Francisco
    nearby_candidates = location_service.find_candidates_in_radius(
        candidates, 
        "San Francisco, CA, USA", 
        50
    )
    
    print(f"Found {len(nearby_candidates)} candidates within 50 miles of San Francisco:")
    for candidate in nearby_candidates[:5]:  # Show first 5
        print(f"- {candidate['name']}: {candidate['distance_miles']} miles away")

def analyze_candidate_locations():
    """Example: Analyze distribution of candidates by city"""
    location_service = LocationService()
    
    # Load candidates
    with open('structured_profiles.json', 'r') as f:
        candidates = json.load(f)
    
    # Group by city
    city_groups = location_service.group_candidates_by_city(candidates)
    
    print("Candidate distribution by city:")
    for city, city_candidates in sorted(city_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"- {city}: {len(city_candidates)} candidates")

if __name__ == "__main__":
    # Add coordinates to structured profiles
    location_service = LocationService()
    location_service.add_coordinates_to_candidates(
        'structured_profiles.json',
        'structured_profiles_with_coordinates.json'
    )
    
    # Run example searches
    search_candidates_near_location()
    analyze_candidate_locations()