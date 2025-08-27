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

- **Incremental Processing**: Each candidate is saved immediately after processing to prevent data loss
- **Error Resilience**: Failed candidates are logged but don't stop the batch process  
- **Language Standardization**: All AI-processed content is translated to English
- **Metadata Preservation**: Every original Lever field is maintained in the output
- **Date Merging**: AI-processed positions are enhanced with original start/end date objects

## Location Services

The `location_utils.py` module provides geographic search capabilities:
- Geocoding: Convert location strings to coordinates using OpenStreetMap
- Radius search: Find candidates within X miles of a location
- Distance calculation: Calculate distances between candidates and office locations
- City grouping: Analyze candidate distribution by city
- Rate-limited API calls with caching for efficiency