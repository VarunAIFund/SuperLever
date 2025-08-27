import json
import os
from typing import List
from openai import OpenAI
from models import AIInferredProfile
from dotenv import load_dotenv
from datetime import datetime

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()

def extract_profile_data(raw_data: dict) -> dict:
    """
    Transform raw Lever candidate data into structured PersonProfile using direct extraction and OpenAI for remaining fields
    """
    
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Extract fields directly from JSON data
    direct_fields = {
        "id": raw_data.get("id"),
        "name": raw_data.get("name"),
        "location": raw_data.get("location"),
        "confidentiality": raw_data.get("confidentiality", "non-confidential"),
        "tags": raw_data.get("tags", [])
    }
    
    # Job vectors and education will be extracted and translated by GPT from parsed_resume data
    
    # Use OpenAI only for fields that need inference
    # Extract only relevant data for GPT processing
    relevant_data = {
        "name": raw_data.get("name", ""),
        "headline": raw_data.get("headline", ""),
        "location": raw_data.get("location", ""),
        "parsed_resume": {
            "positions": raw_data.get("parsed_resume", {}).get("positions", []),
            "schools": raw_data.get("parsed_resume", {}).get("schools", [])
        }
    }
    
    print(f"Sending to GPT for {direct_fields['name']}: {json.dumps(relevant_data, indent=2)}")
    
    prompt = f"""
    Based on the following candidate data, extract and infer the remaining profile information.
    IMPORTANT: All output must be in English. If any content is in any other languages, translate it to English.
    
    Candidate data:
    {json.dumps(relevant_data, indent=2)}
    
    Please extract and return a JSON object with:
    - name: Person's name (translated to English if needed)
    - headline: Professional headline or current role (translated to English if needed)
    - location: Location information (translated to English if needed)
    - current_title: Current job title from most recent position
    - current_org: Current organization from most recent position
    - seniority: Seniority level (e.g., Entry, Junior, Mid, Senior, Staff, Principal, Executive,etc.) based on titles and experience
    - skills: List of all skills including programming languages inferred from experience descriptions
    - years_experience: Total years of experience calculated from earliest date in work history up to {current_date}
    - worked_at_startup: Boolean indicating if they worked at startups
    - positions: List of position objects, one for each position in work history:
      * vector_id: Empty string ""
      * org: Organization name
      * title: Job title
      * summary: Job summary
    - education: List of education objects with properly cleaned information:
      * school: Just the university/institution name
      * degree: Just the degree level
      * field: The field of study
    """
    
    response = client.responses.parse(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "Extract the structured profile information from candidate data."},
            {"role": "user", "content": prompt}
        ],
        text_format=AIInferredProfile,
    )
    
    ai_profile = response.output_parsed
    
    # Combine direct extraction with AI inference
    return {
        "id": direct_fields["id"],
        "name": ai_profile.name,
        "location": ai_profile.location,
        "headline": ai_profile.headline,
        "confidentiality": direct_fields["confidentiality"],
        "tags": direct_fields["tags"],
        "current_title": ai_profile.current_title,
        "current_org": ai_profile.current_org,
        "seniority": ai_profile.seniority,
        "skills": ai_profile.skills,
        "years_experience": ai_profile.years_experience,
        "worked_at_startup": ai_profile.worked_at_startup,
        "positions": [pos.model_dump() for pos in ai_profile.positions],
        "education": [edu.model_dump() for edu in ai_profile.education]
    }

def process_candidates(input_file: str, output_file: str):
    """
    Process all candidates from input file and save structured profiles to output file
    """
    with open(input_file, 'r') as f:
        candidates = json.load(f)
    
    # Initialize output file with empty array
    with open(output_file, 'w') as f:
        json.dump([], f)
    
    processed_count = 0
    
    for i, candidate in enumerate(candidates):
        print(f"Processing candidate {i+1}/{len(candidates)}: {candidate.get('name', 'Unknown')}")
        
        try:
            profile = extract_profile_data(candidate)
            
            # Read existing profiles
            with open(output_file, 'r') as f:
                existing_profiles = json.load(f)
            
            # Add new profile
            existing_profiles.append(profile)
            
            # Write back to file immediately
            with open(output_file, 'w') as f:
                json.dump(existing_profiles, f, indent=2)
            
            processed_count += 1
            print(f"✓ Saved profile for {profile.get('name', 'Unknown')} ({processed_count} total)")
            
        except Exception as e:
            print(f"✗ Error processing candidate {candidate.get('id', 'unknown')}: {str(e)}")
            continue
    
    print(f"\nProcessed {processed_count} candidates successfully")
    print(f"All profiles saved to: {output_file}")

if __name__ == "__main__":
    # Process the test data
    input_file = "test.json"
    output_file = "structured_profiles.json"
    
    process_candidates(input_file, output_file)