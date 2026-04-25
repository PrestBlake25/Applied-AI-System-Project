# AI Music Recommender with Internet Retrieval (RAG)

## Overview
This project extends the Module 3 Music Recommender Simulation into a prompt-driven recommender that blends:
- local catalog matching from `data/songs.csv`
- internet retrieval (Last.fm with iTunes fallback)

Given a natural-language request like "something like Metallica but a bit more mellow", the app parses user intent, retrieves candidate songs, normalizes data to one schema, scores tracks with transparent rules, and returns ranked recommendations.

## What's New
Recent CLI improvements added to the project:
- Dynamic result count prompt: after entering a request, users are asked how many songs they want to hear.
- Post-results exit prompt: after recommendations are printed, users can choose whether to end the program.
- Input validation for result count: non-numeric or non-positive values are rejected with a retry message.
- Consistent exit shortcuts: `q`, `quit`, and `exit` are supported at prompt steps.

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
- Recommendation count input: captures desired number of returned songs.
- Prompt parser: extracts seed artist + preference hints.
- Retriever:
	- Last.fm when `LASTFM_API_KEY` is available.
	- iTunes Search API fallback when no key is present or Last.fm returns nothing.
- Normalizer: maps internet tracks into the internal song schema.
- Recommender: merges local + internet songs, deduplicates, scores, ranks, and explains.
- Tests: verify parsing, retrieval routing, deduplication, ranking, and reliability behavior.

Data flow:
1. User prompt input
2. User chooses how many songs to return
3. Parse prompt to query + preferences
4. Retrieve internet candidates
5. Normalize and merge with local catalog
6. Score and rank
7. Print top recommendations with source labels (`internet` or `local`)
8. Prompt user to continue or end program

## System Diagram
![System Diagram](assets\MusicRecLogic.png)

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
Input flow:
```text
something like Metallica but a bit more mellow
3
```

Output shape:
```text
Top recommendations (internet-augmented):

1. <title> by <artist> [internet|local]
	 Score: <number>
	 Genre: <genre>, Mood: <mood>, Energy: <value>
	 Match: <explanation>

Do you want to end the program? (yes/no):
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
1. **What are the limitations or biases in this system?**
The system uses heuristic parsing and rule-based scoring, so it can miss subtle user intent or over-weight explicit keywords. It is also biased by available catalog/API data: popular English-language artists and well-tagged songs are more likely to appear than niche or underrepresented music.

2. **Could this AI be misused, and how would we prevent that?**
It could be misused to repeatedly query external APIs at high volume or to generate spam-like recommendation outputs. Mitigations include input validation, conservative defaults, rate-limit-aware retrieval/fallback behavior, and keeping outputs bounded and human-reviewable in a CLI workflow.

3. **What surprised me while testing reliability?**
The biggest surprise was how much stability improved from simple reliability controls (fallback providers, deduplication, and quit/empty-input handling). Even when one source failed or returned sparse data, the pipeline still produced usable recommendations.

4. **How I collaborated with AI in this project**
AI was most helpful for quickly proposing testable edge cases and improving CLI flow (for example, adding robust result-count validation and clear exit prompts). One flawed suggestion was to rely too heavily on inferred metadata from sparse API responses; this occasionally produced mismatched mood/genre assumptions, so I kept explicit guardrails and transparent scoring explanations instead.

5. **Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.**
While using Copilot for this project, an instance that AI provided a suggestion was which API I should use. The API that AI suggested was Spotify API, however I need a Premium Account which I don't have. I asked Claude to provide me with more options, and it told me to use two API's (Last.fm and ITunesAPI) which I implemented in this project.
