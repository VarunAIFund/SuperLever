#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Specific Problematic Location Cases

This script tests the two specific location inputs that have been causing issues:
1. "Córdoba, Capital, Córdoba, ARG" 
2. "Jammu, Jammu and Kashmir"
"""

import requests
import json
import time


def test_location(location_text, api_key):
    """Test a specific location with LocationIQ API and show detailed response."""
    print(f"\n{'='*60}")
    print(f"Testing: '{location_text}'")
    print(f"{'='*60}")
    
    params = {
        'key': api_key,
        'q': location_text,
        'format': 'json',
        'limit': 3,  # Get top 3 results to see alternatives
        'addressdetails': 1
    }
    
    try:
        response = requests.get("https://us1.locationiq.com/v1/search.php", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            print(f"API Response (Top {len(data)} results):")
            print("-" * 40)
            
            for i, result in enumerate(data, 1):
                print(f"\nResult {i}:")
                print(f"  Display Name: {result.get('display_name', 'N/A')}")
                print(f"  Type: {result.get('type', 'N/A')}")
                print(f"  Class: {result.get('class', 'N/A')}")
                print(f"  Importance: {result.get('importance', 'N/A')}")
                
                # Address components
                address = result.get('address', {})
                print(f"  Address Components:")
                print(f"    City: {address.get('city', 'N/A')}")
                print(f"    Town: {address.get('town', 'N/A')}")
                print(f"    Village: {address.get('village', 'N/A')}")
                print(f"    Suburb: {address.get('suburb', 'N/A')}")
                print(f"    State: {address.get('state', 'N/A')}")
                print(f"    Province: {address.get('province', 'N/A')}")
                print(f"    County: {address.get('county', 'N/A')}")
                print(f"    Country: {address.get('country', 'N/A')}")
                print(f"    Country Code: {address.get('country_code', 'N/A')}")
                
                # Coordinates
                print(f"  Coordinates: {result.get('lat', 'N/A')}, {result.get('lon', 'N/A')}")
                
        else:
            print("No results found")
            
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


def test_standardization_logic(location_text, api_key):
    """Test how our standardization logic would process a location."""
    print(f"\n{'='*60}")
    print(f"Testing Standardization Logic for: '{location_text}'")
    print(f"{'='*60}")
    
    params = {
        'key': api_key,
        'q': location_text,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    
    try:
        response = requests.get("https://us1.locationiq.com/v1/search.php", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            result = data[0]
            address = result.get('address', {})
            
            print("Raw API Response:")
            print(f"  Display Name: {result.get('display_name', 'N/A')}")
            print(f"  Address: {json.dumps(address, indent=2)}")
            
            # Simulate our standardization logic
            print("\nStandardization Logic:")
            parts = []
            
            # City
            city = None
            if address.get('city'):
                city = address['city']
                print(f"  City: {city}")
            elif address.get('town'):
                city = address['town']
                print(f"  Town: {city}")
            elif address.get('village'):
                city = address['village']
                print(f"  Village: {city}")
            elif address.get('suburb'):
                city = address['suburb']
                print(f"  Suburb: {city}")
            
            if city:
                parts.append(city)
            
            # State/Province
            if address.get('state'):
                state = address['state']
                parts.append(state)
                print(f"  State: {state}")
            elif address.get('province'):
                province = address['province']
                parts.append(province)
                print(f"  Province: {province}")
            elif address.get('county'):
                county = address['county']
                parts.append(county)
                print(f"  County: {county}")
            
            # Country
            if address.get('country'):
                country = address['country']
                parts.append(country)
                print(f"  Country: {country}")
            
            # Remove duplicates
            cleaned_parts = []
            for part in parts:
                if part not in cleaned_parts:
                    cleaned_parts.append(part)
            
            print(f"\nFinal Result: {', '.join(cleaned_parts)}")
            
        else:
            print("No results found")
            
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Test the two specific problematic cases."""
    # Your LocationIQ API key
    API_KEY = "pk.7edffe53b79fbef5e4daf6771ef7cc00"
    
    # Only test the two problematic cases
    test_cases = [
        "Córdoba, Capital, Córdoba, ARG",
        "Jammu, Jammu and Kashmir"
    ]
    
    print("LocationIQ API Test Script")
    print("Testing the two problematic cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"TEST CASE {i}/{len(test_cases)}")
        print(f"{'#'*80}")
        
        # Test 1: Raw API response
        test_location(test_case, API_KEY)
        
        # Test 2: Our standardization logic
        test_standardization_logic(test_case, API_KEY)
        
        # Rate limiting
        time.sleep(0.5)
    
    print(f"\n\n{'='*80}")
    print("TESTING COMPLETED")
    print(f"{'='*80}")


if __name__ == "__main__":
    main() 