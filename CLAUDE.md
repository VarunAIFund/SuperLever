# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperLever is a candidate data transformation system that processes raw Lever recruiting platform data into structured profiles using OpenAI's structured outputs feature. The system combines direct field extraction with AI inference to create comprehensive candidate profiles while preserving all original Lever metadata.

## Data Architecture

### Input Data (Lever Format)
- Located in `data/output/` as batch JSON files (`batch_XXX_no_parsed.json`, `batch_XXX_with_parsed.json`)
- Test data subset available at `data/test.json` (first 10 candidates from batch_001)
- Contains raw candidate information with nested `parsed_resume` sections including:
  - `positions[]`: Job history with org, title, summary, start/end dates
  - `schools[]`: Education with org, degree, field, start/end dates
- Root-level fields: id, contact, phones, emails, links, stage, confidentiality, tags, sources, stageChanges, owner, followers, applications, timestamps, urls, etc.

### Output Data (Hybrid Format)
- Preserves ALL original Lever fields (contact info, stage management, metadata)
- Adds AI-enhanced fields: current_title, current_org, seniority, skills, years_experience, worked_at_startup
- Structured education and positions arrays with cleaned data
- Uses `AIInferredProfile` model for OpenAI structured outputs validation
- Position objects include vector_embedding field and location information

## Key Commands

### Setup and Dependencies
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key-here"
```

### Data Transformation
```bash
cd transform_data
python transform.py
```
This processes candidates from test.json and outputs to structured_profiles.json.

### Data Extraction for Testing
```bash
python test_set.py
```
Extracts first 10 candidates from batch data to test.json.

### Location-based Search
```bash
cd transform_data
python location_example.py
```
Adds coordinates to candidate profiles and demonstrates geographic search capabilities.

## Architecture Notes

### Hybrid Processing Strategy
The system uses a two-phase approach:

**Phase 1: Direct Field Extraction**
All original Lever fields are preserved exactly as-is: id, contact, phones, emails, links, stage, confidentiality, tags, sources, stageChanges, owner, followers, applications, createdAt, updatedAt, lastInteractionAt, lastAdvancedAt, snoozedUntil, urls, isAnonymized, dataProtection.

**Phase 2: AI Enhancement (via OpenAI gpt-5-nano)**
OpenAI processes only essential candidate data:
- **Input Filter**: name, headline, location, parsed_resume (positions + schools only) 
- **AI Output**: name, headline, location, current_title, current_org, seniority, skills, years_experience, worked_at_startup, education[], positions[]
- **Data Merging**: Position start/end dates from original data are merged with AI-processed position data

### OpenAI Structured Outputs Integration
- Uses Pydantic models: `Education`, `Position`, `AIInferredProfile`  
- Model uses `client.responses.parse()` with `text_format=AIInferredProfile`
- Position model includes `vector_embedding` field (empty string) and `location` field
- All AI responses must be in English (auto-translation handled)

### Cost Optimization
Sends only ~30-50 lines of relevant data to OpenAI instead of full candidate records (~200+ lines) to minimize API costs while preserving all original information.

## Data Processing Patterns

### Transformation Pipeline
- **Incremental Processing**: Each candidate is saved immediately after processing to prevent data loss
- **Error Resilience**: Failed candidates are logged but don't stop the batch process  
- **Language Standardization**: All AI-processed content is translated to English
- **Metadata Preservation**: Every original Lever field is maintained in the output
- **Date Merging**: AI-processed positions are enhanced with original start/end date objects

### Database Import Strategy
- **Upsert Logic**: Candidates use `ON CONFLICT DO UPDATE` to update existing records
- **Replace Strategy**: Positions and education use DELETE + INSERT for clean replacement
- **Batch Processing**: 50 candidates per batch for optimal performance and memory usage
- **Transaction Safety**: All operations within transactions, rollback on failure
- **UUID Handling**: Proper type casting for UUID arrays and references

## Database Architecture

### PostgreSQL Schema (3-table design)
- **candidates**: Main table with candidate profiles, skills, experience, metadata
- **positions**: Work history linked to candidates via candidate_id
- **education**: Education history linked to candidates via candidate_id

### Database Operations
```bash
# Import structured profiles to database
cd transform_data
python import_to_db.py

# Test database connection
python -c "from db_config import test_connection; test_connection()"

# Clear all database entries (keeps table structure)
python -c "
from db_config import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('DELETE FROM education')
    cursor.execute('DELETE FROM positions') 
    cursor.execute('DELETE FROM candidates')
    conn.commit()
"
```

### Cloud Database (Railway)
- Database connection configured in `transform_data/db_config.py`
- Uses environment variable `DATABASE_URL` or falls back to Railway connection string
- SSL required for Railway connections (`sslmode=require`)
- Supports both local PostgreSQL and cloud deployment

## Natural Language Search System

### Candidate Search Interface
```bash
# Interactive search mode
cd search
python candidate_search.py

# Command line search
python candidate_search.py "Find Python developers in San Francisco"
python candidate_search.py "Senior engineers who worked at startups"

# Table output format
python candidate_search.py "React developers" --table
```

### Search Architecture
- **Input**: Natural language queries (e.g., "Find Python developers")
- **Processing**: ChatGPT (gpt-4o-mini) converts to PostgreSQL queries
- **Context**: Database schema info provided via `db_schema_info.py`
- **Output**: Candidate records with relevance ranking
- **Safety**: Read-only queries only, dangerous operations blocked

### Search Query Examples
The system converts natural language to SQL:
- "Find Python developers" → `WHERE 'Python' = ANY(skills)`
- "Senior engineers at Meta" → `JOIN positions WHERE seniority = 'Senior' AND org ILIKE '%Meta%'`
- "Computer science degrees" → `JOIN education WHERE field ILIKE '%computer science%'`

## Data Normalization Tools

### Degree Extraction and Analysis
```bash
# Extract all unique degrees from batch files
cd test
python extract_degrees.py

# Get top 10,000 most common degrees for normalization
python top_degrees.py
```

**Degree Normalization Strategy**: Extract ~150,000 unique degree variations, map top 10,000 to standardized categories using ChatGPT for improved search accuracy.

## Location Services

The `location_utils.py` module provides geographic search capabilities:
- Geocoding: Convert location strings to coordinates using OpenStreetMap
- Radius search: Find candidates within X miles of a location
- Distance calculation: Calculate distances between candidates and office locations
- City grouping: Analyze candidate distribution by city
- Rate-limited API calls with caching for efficiency