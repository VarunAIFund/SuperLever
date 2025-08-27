# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperLever is a candidate data transformation system that processes raw Lever recruiting platform data into structured profiles using OpenAI's structured outputs feature.

## Data Architecture

The project operates on two main data formats:

### Input Data (Lever Format)
- Located in `data/output/` as batch JSON files (`batch_XXX_no_parsed.json`, `batch_XXX_with_parsed.json`)
- Test data subset available at `data/test.json` (first 10 candidates from batch_001)
- Contains raw candidate information with nested `parsed_resume` sections including:
  - `positions[]`: Job history with org, title, summary, dates
  - `schools[]`: Education with org, degree, field, dates
- Root-level fields: id, name, location, confidentiality, tags, etc.

### Output Data (Structured Format)
- Target structure defined in `transform_data/models.py`
- PersonProfile with flattened fields: current_title, current_org, past_orgs, education[], job_vectors[], etc.
- Uses Pydantic models for validation and OpenAI structured outputs

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

The transformation pipeline:
1. Raw Lever data → OpenAI structured outputs → Structured profiles
2. Direct field mapping possible for: id, name, location (root level), org/title/summary (positions), degree/field/school (schools)
3. AI inference needed for: skills extraction, programming languages, years of experience calculation, startup detection
4. Vector IDs are generated for each job position in job_vectors[]

## Data Processing Patterns

- Batch files contain large datasets (121 batches available)
- Test subset workflow: extract sample → transform → validate structure
- Error handling included for malformed candidate records
- Confidentiality levels preserved from source data

## Location Services

The `location_utils.py` module provides geographic search capabilities:
- Geocoding: Convert location strings to coordinates using OpenStreetMap
- Radius search: Find candidates within X miles of a location
- Distance calculation: Calculate distances between candidates and office locations
- City grouping: Analyze candidate distribution by city
- Rate-limited API calls with caching for efficiency