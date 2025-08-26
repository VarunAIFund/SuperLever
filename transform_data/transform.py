import json
import os
from typing import List
from openai import OpenAI
from models import PersonProfile
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_profile_data(raw_data: dict) -> PersonProfile:
    """
    Transform raw Lever candidate data into structured PersonProfile using direct extraction and OpenAI for remaining fields
    """
    
    # Extract fields directly from JSON data
    profile_data = {
        "id": raw_data.get("id"),
        "name": raw_data.get("name"),
        "location": raw_data.get("location"),
        "confidentiality": raw_data.get("confidentiality", False),
        "tags": []
    }
    
    # Extract job vectors directly from work history
    job_vectors = []
    if "work_history" in raw_data:
        for work_exp in raw_data["work_history"]:
            job_vector = {
                "vector_id": f"job_{len(job_vectors) + 1}",
                "org": work_exp.get("organization"),
                "title": work_exp.get("title"),
                "summary": work_exp.get("summary", ""),
                "start_date": work_exp.get("start_date"),
                "end_date": work_exp.get("end_date")
            }
            job_vectors.append(job_vector)
    
    profile_data["job_vectors"] = job_vectors
    
    # Extract education directly from JSON
    education = []
    if "education" in raw_data:
        for edu in raw_data["education"]:
            edu_info = {
                "school": edu.get("school"),
                "degree": edu.get("degree"),
                "field": edu.get("field"),
                "graduation_year": edu.get("graduation_year")
            }
            education.append(edu_info)
    
    profile_data["education"] = education
    
    # Use OpenAI only for fields that need inference
    prompt = f"""
    Based on the following candidate data, extract and infer the remaining profile information.
    
    Raw candidate data:
    {json.dumps(raw_data, indent=2)}
    
    Already extracted fields:
    - ID: {profile_data['id']}
    - Name: {profile_data['name']}
    - Location: {profile_data['location']}
    - Job vectors: {len(job_vectors)} positions
    - Education: {len(education)} entries
    
    Please extract:
    - Current position and organization from the most recent position
    - Past organizations from work history
    - Job titles from work history
    - Skills and programming languages (infer from experience descriptions)
    - Years of experience (calculate from work history)
    - Whether they worked at startups (infer from company types)
    """
    
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": "You are a data extraction expert. Extract structured candidate profile information from raw recruiting data."},
            {"role": "user", "content": prompt}
        ],
        text_format=PersonProfile
    )
    
    # Merge the directly extracted data with OpenAI inferred data
    openai_profile = response.output_parsed
    openai_profile.id = profile_data["id"]
    openai_profile.name = profile_data["name"]
    openai_profile.location = profile_data["location"]
    openai_profile.job_vectors = profile_data["job_vectors"]
    openai_profile.education = profile_data["education"]
    openai_profile.confidentiality = profile_data["confidentiality"]
    openai_profile.tags = profile_data["tags"]
    
    return openai_profile

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
            structured_profiles.append(profile.model_dump())
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