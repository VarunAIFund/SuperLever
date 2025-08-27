# SuperLever

SuperLever is a candidate data transformation system that processes raw Lever recruiting platform data into structured profiles using OpenAI's structured outputs feature.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Data Transformation
Transform raw Lever candidate data into structured profiles:
```bash
cd transform_data
python transform.py
```

This will:
- Read candidate data from `test.json`
- Transform each candidate using OpenAI's structured outputs
- Save structured profiles to `structured_profiles.json`

### Location-based Search
Add coordinates to candidate profiles and perform geographic searches:
```bash
cd transform_data
python location_example.py
```

### Data Extraction for Testing
Extract a sample of candidates from batch data:
```bash
python test_set.py
```

## Output Format

The transformation generates structured profiles with the following fields:
- `id`: Candidate ID
- `name`: Full name
- `location`: Location
- `headline`: Professional headline
- `current_title`: Current job title
- `current_org`: Current organization
- `seniority`: Seniority level (Entry, Junior, Mid, Senior, Staff, Principal, Executive)
- `skills`: List of all skills including programming languages
- `years_experience`: Calculated years of experience
- `worked_at_startup`: Boolean indicating startup experience
- `education`: Education history with degree, field, and school
- `positions`: Work history with organization, title, and summary
- `tags`: Tags from original data
- `confidentiality`: Confidentiality level

## Architecture

The system operates on two main data formats:

### Input Data (Lever Format)
- Located in `data/output/` as batch JSON files
- Contains raw candidate information with nested `parsed_resume` sections
- Root-level fields: id, name, location, confidentiality, tags, etc.

### Output Data (Structured Format)  
- Uses Pydantic models for validation and OpenAI structured outputs
- Flattened structure optimized for analysis and querying

## Location Services

The `transform_data/location_utils.py` module provides geographic search capabilities:
- Geocoding: Convert location strings to coordinates using OpenStreetMap
- Radius search: Find candidates within X miles of a location
- Distance calculation: Calculate distances between candidates and office locations
- City grouping: Analyze candidate distribution by city
