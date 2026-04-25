from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
import os
import re

import requests


_SEED_ARTIST_PATTERN = re.compile(r"like\s+([a-z0-9 .&'\-]+?)(?:\s+but|\s+with|$)", re.IGNORECASE)


def _normalize(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def parse_prompt_to_query(prompt: str) -> Dict:
    """
    Parse a natural-language request into retrieval terms and scoring preferences.
    """
    text = _normalize(prompt)

    seed_artist: Optional[str] = None
    artist_match = _SEED_ARTIST_PATTERN.search(prompt)
    if artist_match:
        seed_artist = artist_match.group(1).strip(" .,!?")

    mood = "neutral"
    target_energy = 0.6
    likes_acoustic = False

    mellow_terms = ("mellow", "calm", "chill", "softer", "soft", "relaxed")
    intense_terms = ("intense", "aggressive", "heavy", "hard", "hype", "energetic")
    acoustic_terms = ("acoustic", "unplugged")

    if any(term in text for term in mellow_terms):
        mood = "chill"
        target_energy = 0.45
        likes_acoustic = True
    elif any(term in text for term in intense_terms):
        mood = "intense"
        target_energy = 0.85
        likes_acoustic = False

    if any(term in text for term in acoustic_terms):
        likes_acoustic = True

    genre = ""
    if "metallica" in text:
        genre = "rock"
    elif "rock" in text:
        genre = "rock"
    elif "pop" in text:
        genre = "pop"
    elif "lofi" in text:
        genre = "lofi"
    elif "jazz" in text:
        genre = "jazz"
    elif "electronic" in text or "edm" in text:
        genre = "electronic"

    query_terms: List[str] = []
    if seed_artist:
        query_terms.append(seed_artist)

    if genre == "rock" and mood == "chill":
        query_terms.append("soft rock")
    elif genre:
        query_terms.append(genre)

    if mood == "chill":
        query_terms.append("mellow songs")

    if not query_terms:
        query_terms.append(prompt)

    return {
        "seed_artist": seed_artist,
        "genre": genre,
        "mood": mood,
        "energy": target_energy,
        "likes_acoustic": likes_acoustic,
        "query_terms": query_terms,
    }


def _infer_track_features(genre_text: str, target_energy: float) -> Tuple[float, float, float, float, float]:
    """
    Infer missing audio features for internet tracks using genre keywords.
    """
    g = _normalize(genre_text)

    energy = 0.6
    acousticness = 0.35
    tempo_bpm = 118.0
    valence = 0.55
    danceability = 0.55

    if "metal" in g or "hard rock" in g:
        energy = 0.9
        acousticness = 0.1
        tempo_bpm = 140.0
        valence = 0.45
    elif "rock" in g:
        energy = 0.75
        acousticness = 0.2
        tempo_bpm = 128.0
    elif "pop" in g:
        energy = 0.7
        acousticness = 0.2
        danceability = 0.72
    elif "acoustic" in g or "folk" in g:
        energy = 0.45
        acousticness = 0.82
        tempo_bpm = 95.0
    elif "jazz" in g or "blues" in g:
        energy = 0.5
        acousticness = 0.68
        tempo_bpm = 102.0
    elif "electronic" in g or "dance" in g:
        energy = 0.82
        acousticness = 0.05
        tempo_bpm = 130.0
        danceability = 0.8

    # Bias inferred features toward the target energy from the prompt.
    energy = round((energy + target_energy) / 2.0, 2)
    return energy, tempo_bpm, valence, danceability, acousticness


def fetch_songs_from_itunes(query_terms: List[str], max_results: int = 10, timeout: int = 8) -> List[Dict]:
    """
    Retrieve song candidates from iTunes Search API.
    """
    collected: List[Dict] = []
    seen: Set[Tuple[str, str]] = set()

    per_query_limit = max(3, min(10, max_results // max(1, len(query_terms)) + 2))

    for term in query_terms:
        try:
            response = requests.get(
                "https://itunes.apple.com/search",
                params={"term": term, "media": "music", "entity": "song", "limit": per_query_limit},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            continue

        for item in payload.get("results", []):
            title = str(item.get("trackName", "")).strip()
            artist = str(item.get("artistName", "")).strip()
            if not title or not artist:
                continue

            dedup_key = (title.lower(), artist.lower())
            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            collected.append(item)
            if len(collected) >= max_results:
                return collected

    return collected


def fetch_songs_from_lastfm(
    query_terms: List[str],
    api_key: str,
    max_results: int = 10,
    timeout: int = 8,
) -> List[Dict]:
    """
    Retrieve song candidates from Last.fm using an API key.
    """
    collected: List[Dict] = []
    seen: Set[Tuple[str, str]] = set()

    per_query_limit = max(3, min(10, max_results // max(1, len(query_terms)) + 2))

    for term in query_terms:
        try:
            response = requests.get(
                "https://ws.audioscrobbler.com/2.0/",
                params={
                    "method": "track.search",
                    "track": term,
                    "api_key": api_key,
                    "format": "json",
                    "limit": per_query_limit,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            continue

        tracks = payload.get("results", {}).get("trackmatches", {}).get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        for item in tracks:
            title = str(item.get("name", "")).strip()
            artist = str(item.get("artist", "")).strip()
            if not title or not artist:
                continue

            dedup_key = (title.lower(), artist.lower())
            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            collected.append(
                {
                    "trackName": title,
                    "artistName": artist,
                    "primaryGenreName": "",
                    "trackId": abs(hash(f"{title}:{artist}")),
                }
            )
            if len(collected) >= max_results:
                return collected

    return collected


def retrieve_songs_for_prompt(
    prompt: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
) -> Tuple[List[Dict], Dict]:
    """
    RAG retrieval entry point:
    1) Parse prompt into retrieval/scoring hints.
    2) Pull matching songs from internet search.
    3) Convert remote tracks into local song schema.

    API key behavior:
    - If api_key is provided (or LASTFM_API_KEY env var exists), use Last.fm.
    - Otherwise fall back to iTunes Search API.
    """
    prompt_profile = parse_prompt_to_query(prompt)
    resolved_api_key = (api_key or os.getenv("LASTFM_API_KEY") or "").strip()
    if resolved_api_key:
        raw_tracks = fetch_songs_from_lastfm(
            prompt_profile["query_terms"],
            api_key=resolved_api_key,
            max_results=max_results,
        )
        if not raw_tracks:
            raw_tracks = fetch_songs_from_itunes(prompt_profile["query_terms"], max_results=max_results)
    else:
        raw_tracks = fetch_songs_from_itunes(prompt_profile["query_terms"], max_results=max_results)

    internet_songs: List[Dict] = []
    for idx, track in enumerate(raw_tracks, start=1):
        primary_genre = str(track.get("primaryGenreName", "unknown")).lower()
        energy, tempo_bpm, valence, danceability, acousticness = _infer_track_features(
            primary_genre,
            float(prompt_profile["energy"]),
        )

        internet_songs.append(
            {
                "id": int(track.get("trackId", 10_000_000 + idx)),
                "title": str(track.get("trackName", "Unknown Title")),
                "artist": str(track.get("artistName", "Unknown Artist")),
                "genre": prompt_profile["genre"] or primary_genre,
                "mood": prompt_profile["mood"],
                "energy": energy,
                "tempo_bpm": tempo_bpm,
                "valence": valence,
                "danceability": danceability,
                "acousticness": acousticness,
                "source": "internet",
            }
        )

    return internet_songs, {
        "genre": prompt_profile["genre"],
        "mood": prompt_profile["mood"],
        "energy": prompt_profile["energy"],
        "likes_acoustic": prompt_profile["likes_acoustic"],
    }
