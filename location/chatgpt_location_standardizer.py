#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT Location Standardizer

This script takes locations that failed with LocationIQ API and uses ChatGPT
to standardize them. ChatGPT can handle messy, ambiguous, or non-standard 
location formats better than strict geocoding APIs.
"""

import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ChatGPTLocationStandardizer:
    def __init__(self):
        self.client = OpenAI()
        self.standardized_locations = {}
        self.failed_locations = []
    
    def standardize_locations_batch(self, locations_list):
        """Send a batch of locations to ChatGPT for standardization."""
        
        # Create the prompt with all locations
        locations_text = "\n".join([f"- {loc}" for loc in locations_list])
        
        prompt = f"""
You are a location standardization expert. I have {len(locations_list)} location strings that failed to be standardized by geocoding APIs. Please standardize each location to the format "City, State/Province, Country".

Rules for standardization:
1. Convert to proper "City, State/Province, Country" format
2. Use full country names (not abbreviations like "USA" → "United States of America")  
3. Use full state names (not abbreviations like "CA" → "California")
4. Remove extraneous information (citizenship notes, area descriptions, etc.)
5. For metropolitan areas, choose the primary city
6. For unclear locations, make your best guess based on context
7. If a location is genuinely impossible to determine, output "UNKNOWN"

Original locations to standardize:
{locations_text}

Please return a JSON object with this exact format:
{{
  "original_location_1": "standardized_location_1",
  "original_location_2": "standardized_location_2",
  ...
}}

Return ONLY the JSON object, no other text.
        """
        
        try:
            print(f"Sending {len(locations_list)} locations to ChatGPT for standardization...")
            
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a location standardization expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for consistent results
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                standardized_dict = json.loads(response_text)
                print("✅ ChatGPT response received and parsed successfully")
                return standardized_dict
            except json.JSONDecodeError:
                print("❌ Failed to parse ChatGPT response as JSON")
                print("Response received:")
                print(response_text)
                return None
                
        except Exception as e:
            print(f"❌ Error calling ChatGPT API: {e}")
            return None
    
    def process_failed_locations(self, input_file='standardized_batch_locations.json', 
                               output_file='chatgpt_standardized_locations.json'):
        """Find failed locations and process them with ChatGPT."""
        
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: {input_file} not found!")
            return
        
        print(f"Reading failed locations from {input_file}...")
        
        # Read the standardized locations file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find all FAILED entries
        failed_locations = [location for location, status in data.items() if status == "FAILED"]
        
        print(f"Found {len(failed_locations)} FAILED locations")
        
        if len(failed_locations) == 0:
            print("No failed locations found!")
            return
        
        print("Failed locations to process:")
        for i, location in enumerate(failed_locations, 1):
            print(f"  {i:2d}. {location}")
        
        print(f"\n📤 Sending all {len(failed_locations)} locations to ChatGPT in one batch...")
        
        # Send all locations to ChatGPT (89 should be fine for GPT-4)
        standardized_dict = self.standardize_locations_batch(failed_locations)
        
        if standardized_dict is None:
            print("❌ Failed to get standardized locations from ChatGPT")
            return
        
        # Process the results
        successful_standardizations = 0
        unknown_locations = 0
        
        chatgpt_results = {}
        
        for original_location in failed_locations:
            if original_location in standardized_dict:
                standardized = standardized_dict[original_location]
                chatgpt_results[original_location] = standardized
                
                if standardized == "UNKNOWN":
                    unknown_locations += 1
                    print(f"  ❓ UNKNOWN: {original_location}")
                else:
                    successful_standardizations += 1
                    print(f"  ✅ {original_location} → {standardized}")
            else:
                # ChatGPT didn't provide a result for this location
                chatgpt_results[original_location] = "MISSING_FROM_RESPONSE"
                print(f"  ⚠️  MISSING: {original_location}")
        
        # Save ChatGPT results to separate file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chatgpt_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 ChatGPT results saved to: {output_file}")
        
        # Also create a text file for easy review
        text_file = output_file.replace('.json', '.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("ChatGPT Location Standardization Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("SUCCESSFUL STANDARDIZATIONS:\n")
            f.write("-" * 30 + "\n")
            for original, standardized in chatgpt_results.items():
                if standardized not in ["UNKNOWN", "MISSING_FROM_RESPONSE"]:
                    f.write(f"{original} → {standardized}\n")
            
            f.write(f"\nUNKNOWN LOCATIONS:\n")
            f.write("-" * 30 + "\n")
            for original, standardized in chatgpt_results.items():
                if standardized == "UNKNOWN":
                    f.write(f"{original}\n")
            
            if any(v == "MISSING_FROM_RESPONSE" for v in chatgpt_results.values()):
                f.write(f"\nMISSING FROM RESPONSE:\n")
                f.write("-" * 30 + "\n")
                for original, standardized in chatgpt_results.items():
                    if standardized == "MISSING_FROM_RESPONSE":
                        f.write(f"{original}\n")
        
        print(f"📄 Text summary saved to: {text_file}")
        
        # Print summary
        self._print_summary(len(failed_locations), successful_standardizations, 
                          unknown_locations, len(chatgpt_results))
        
        return chatgpt_results
    
    def _print_summary(self, total_attempted, successful, unknown, total_processed):
        """Print summary of ChatGPT standardization results."""
        missing = total_attempted - total_processed
        
        print(f"\n{'='*60}")
        print("CHATGPT STANDARDIZATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total locations sent to ChatGPT: {total_attempted}")
        print(f"Successfully standardized: {successful}")
        print(f"Marked as UNKNOWN: {unknown}")
        print(f"Missing from response: {missing}")
        print(f"Success rate: {successful / total_attempted * 100:.1f}%")
        
        print(f"\n📁 Output files:")
        print(f"  - chatgpt_standardized_locations.json (machine readable)")
        print(f"  - chatgpt_standardized_locations.txt (human readable)")
        print(f"\n💡 Review the results and decide which ChatGPT standardizations to accept!")


def main():
    """Main function to run ChatGPT location standardization."""
    
    print("ChatGPT Location Standardizer")
    print("=" * 40)
    print("This script uses ChatGPT to standardize locations that failed with LocationIQ API")
    print("ChatGPT can handle messy, ambiguous, and non-standard location formats")
    print()
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize standardizer
    standardizer = ChatGPTLocationStandardizer()
    
    # Process failed locations
    try:
        results = standardizer.process_failed_locations()
        if results:
            print("\n✅ ChatGPT standardization completed!")
            print("Review the output files to see the results.")
        else:
            print("\n❌ ChatGPT standardization failed.")
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")


if __name__ == "__main__":
    main()