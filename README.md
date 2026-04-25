# AI Music Recommender with Internet Retrieval (RAG)

## Overview
This project extends the Module 3 Music Recommender Simulation into a prompt-driven recommender that blends:
- local catalog matching from `data/songs.csv`
- internet retrieval (Last.fm with iTunes fallback)

Given a natural-language request like "something like Metallica but a bit more mellow", the app parses user intent, retrieves candidate songs, normalizes data to one schema, scores tracks with transparent rules, and returns ranked recommendations.

## Original Project Context (Module 3)
Original project name: Music Recommender Simulation.

Module 3 focused on a transparent, content-based recommender with simple, inspectable scoring logic based on:
- genre
- mood
- energy
- acousticness preference

This version keeps that explainable scoring core and adds retrieval-augmented behavior.

## Architecture
Main components:
- CLI interface: captures free-text user prompts.
- Prompt parser: extracts seed artist + preference hints.
- Retriever:
	- Last.fm when `LASTFM_API_KEY` is available.
	- iTunes Search API fallback when no key is present or Last.fm returns nothing.
- Normalizer: maps internet tracks into the internal song schema.
- Recommender: merges local + internet songs, deduplicates, scores, ranks, and explains.
- Tests: verify parsing, retrieval routing, deduplication, ranking, and reliability behavior.

Data flow:
1. User prompt input
2. Parse prompt to query + preferences
3. Retrieve internet candidates
4. Normalize and merge with local catalog
5. Score and rank
6. Print top recommendations with source labels (`internet` or `local`)

## System Diagram
![System Diagram](assets/MuiscRecLogic.png)

## Project Structure
```text
src/
	main.py          # CLI entrypoint
	rag.py           # prompt parsing + external retrieval + normalization
	recommender.py   # scoring and recommendation logic
tests/
	test_rag.py
	test_recommender.py
	test_reliability.py
data/
	songs.csv
```

## Quickstart
### 1) Create and activate a virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 3) (Optional) Set Last.fm API key
Windows PowerShell:
```powershell
$env:LASTFM_API_KEY="your_lastfm_api_key"
```

If unset, the app uses iTunes Search API automatically.

### 4) Run the app
```bash
python -m src.main
```

### 5) Run tests
```bash
python -m pytest -q
```

Current local test status: 12 passed.

## Sample CLI Interaction
Input:
```text
something like Metallica but a bit more mellow
```

Output shape:
```text
Top recommendations (internet-augmented):

1. <title> by <artist> [internet|local]
	 Score: <number>
	 Genre: <genre>, Mood: <mood>, Energy: <value>
	 Match: <explanation>
```

Note: exact songs and scores may vary over time due to live API retrieval and fallback behavior.

## Design Decisions and Trade-offs
Why this design:
- Transparent rule-based scoring for explainability.
- RAG-style retrieval for broader candidate coverage.
- Provider fallback for resilience.

Trade-offs:
- Heuristic parsing is interpretable but less nuanced than embedding-based intent modeling.
- Internet tracks may not include full audio features, so features are inferred.
- External APIs provide freshness but can be rate-limited or return variable results.

## Testing Coverage
The test suite validates:
- prompt parsing (`parse_prompt_to_query`)
- Last.fm vs iTunes routing behavior
- fallback behavior when Last.fm has no results
- recommendation deduplication and ranking integration
- CLI reliability (empty input, quit flow, interrupt handling)

## Reflection
This project demonstrates that practical AI systems are pipelines, not just models. Output quality depends on prompt interpretation, retrieval, normalization, ranking logic, and robust fallback paths.

Keeping the scoring logic explainable while adding retrieval made the system more useful without losing debuggability.
