# Transform Data - OpenAI Structured Outputs

This script transforms raw Lever candidate data into structured profiles using OpenAI's structured outputs feature.

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

Run the transformation script:
```bash
cd transform_data
python transform.py
```

This will:
- Read candidate data from `../data/test.json`
- Transform each candidate using OpenAI's structured outputs
- Save structured profiles to `structured_profiles.json`

## Output Format

The script generates structured profiles with the following fields:
- `id`: Candidate ID
- `name`: Full name
- `location`: Location
- `current_title`: Current job title
- `current_org`: Current organization
- `past_orgs`: List of previous organizations
- `titles`: List of job titles held
- `skills`: Extracted skills
- `programming_languages`: Programming languages used
- `education`: Education history with degree, field, and school
- `years_experience`: Calculated years of experience
- `worked_at_startup`: Boolean indicating startup experience
- `job_vectors`: Job history with vector IDs for each position
- `tags`: Tags (empty by default)
- `confidentiality`: Confidentiality level