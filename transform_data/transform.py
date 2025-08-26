import json
import os
from typing import List
from openai import OpenAI
from models import AIInferredProfile
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()

def extract_profile_data(raw_data: dict) -> dict:
    """
    Transform raw Lever candidate data into structured PersonProfile using direct extraction and OpenAI for remaining fields
    """
    
    # Extract fields directly from JSON data
    direct_fields = {
        "id": raw_data.get("id"),
        "name": raw_data.get("name"),
        "location": raw_data.get("location"),
        "confidentiality": raw_data.get("confidentiality", "non-confidential"),
        "tags": raw_data.get("tags", [])
    }
    
    # Extract job vectors directly from parsed_resume positions
    job_vectors = []
    if "parsed_resume" in raw_data and "positions" in raw_data["parsed_resume"]:
        for i, position in enumerate(raw_data["parsed_resume"]["positions"]):
            job_vector = {
                "vector_id": "",
                "org": position.get("org", ""),
                "title": position.get("title", ""),
                "summary": position.get("summary", "")
            }
            job_vectors.append(job_vector)
    
    # Education will be extracted by GPT from schools data
    
    # Use OpenAI only for fields that need inference
    prompt = f"""
    Based on the following candidate data, extract and infer the remaining profile information.
    
    Raw candidate data:
    {json.dumps(raw_data, indent=2)}
    
    Please extract and return a JSON object with:
    - current_title: Current job title from most recent position
    - current_org: Current organization from most recent position  
    - seniority: Seniority level (e.g., Entry, Junior, Mid, Senior, Staff, Principal, Executive,etc.) based on titles and experience
    - skills: List of all skills including programming languages inferred from experience descriptions
    - years_experience: Total years of experience calculated from work history
    - worked_at_startup: Boolean indicating if they worked at startups
    - education: List of education objects with properly cleaned:
      * school: Just the university/institution name (e.g., "Stanford" not "Stanford University Department of Computer Science")
      * degree: Just the degree level (e.g., "Bachelor of Engineering" not "Bachelor of Engineering, Computer Engineering")  
      * field: The field of study (e.g., "Computer Engineering" extracted from degree or field data)
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
        "name": direct_fields["name"],
        "location": direct_fields["location"],
        "confidentiality": direct_fields["confidentiality"],
        "tags": direct_fields["tags"],
        "job_vectors": job_vectors,
        "current_title": ai_profile.current_title,
        "current_org": ai_profile.current_org,
        "seniority": ai_profile.seniority,
        "skills": ai_profile.skills,
        "years_experience": ai_profile.years_experience,
        "worked_at_startup": ai_profile.worked_at_startup,
        "education": [edu.model_dump() for edu in ai_profile.education]
    }

def process_candidates(input_file: str, output_file: str):
    """
    Process all candidates from input file and save structured profiles to output file
    """
    with open(input_file, 'r') as f:
        candidates = json.load(f)
    
    structured_profiles = []
    
    for i, candidate in enumerate(candidates):
        print(f"Processing candidate {i+1}/{len(candidates)}: {candidate.get('name', 'Unknown')}")
        
        try:
            profile = extract_profile_data(candidate)
            structured_profiles.append(profile)
        except Exception as e:
            print(f"Error processing candidate {candidate.get('id', 'unknown')}: {str(e)}")
            continue
    
    # Save structured profiles
    with open(output_file, 'w') as f:
        json.dump(structured_profiles, f, indent=2)
    
    print(f"Processed {len(structured_profiles)} candidates successfully")
    print(f"Structured profiles saved to: {output_file}")

if __name__ == "__main__":
    # Process the test data
    input_file = "test.json"
    output_file = "structured_profiles.json"
    
    process_candidates(input_file, output_file)