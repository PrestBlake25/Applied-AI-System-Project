from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
from pathlib import Path

try:
    from .rag import retrieve_songs_for_prompt
except ImportError:
    from rag import retrieve_songs_for_prompt

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    path = Path(csv_path)

    # Handle the common typo path used in some starter prompts.
    if not path.exists() and path.name == "csongs.csv":
        fallback = path.with_name("songs.csv")
        if fallback.exists():
            path = fallback

    songs: List[Dict] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            )

    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """
    Scores a single song against user preferences.

    The function is intentionally simple and transparent:
    - genre match: +2
    - mood match: +4
    - energy close match (<= 0.15): +2
    - energy near match (<= 0.30): +1
    - acoustic preference match: +1
    - energy proximity bonus: up to +0.99 for closer matches
    """
    score = 0.0
    reasons: List[str] = []

    pref_genre = (user_prefs.get("genre") or user_prefs.get("favorite_genre") or "").strip().lower()
    song_genre = str(song.get("genre", "")).strip().lower()
    if pref_genre and song_genre == pref_genre:
        score += 2
        reasons.append("genre match")

    pref_mood = (user_prefs.get("mood") or user_prefs.get("favorite_mood") or "").strip().lower()
    song_mood = str(song.get("mood", "")).strip().lower()
    if pref_mood and song_mood == pref_mood:
        score += 4
        reasons.append("mood match")

    target_energy = user_prefs.get("energy")
    if target_energy is None:
        target_energy = user_prefs.get("target_energy")
    if target_energy is not None and "energy" in song:
        diff = abs(float(song["energy"]) - float(target_energy))
        if diff <= 0.15:
            score += 2
            reasons.append("energy very close")
        elif diff <= 0.30:
            score += 1
            reasons.append("energy close")

        # Add a small continuous bonus so ties are less frequent in output.
        if diff <= 0.30:
            proximity_bonus = (0.30 - diff) / 0.30
            score += round(proximity_bonus, 2)

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None and "acousticness" in song:
        acoustic = float(song["acousticness"])
        if bool(likes_acoustic) and acoustic >= 0.6:
            score += 1
            reasons.append("acoustic preference match")
        elif not bool(likes_acoustic) and acoustic < 0.6:
            score += 1
            reasons.append("non-acoustic preference match")

    explanation = ", ".join(reasons) if reasons else "No strong preference matches"
    return score, explanation

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []

    for song in songs:
        score, explanation = score_song(user_prefs, song)
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def recommend_songs_with_rag(
    user_prompt: str,
    local_songs: List[Dict],
    k: int = 5,
    internet_k: int = 10,
    api_key: Optional[str] = None,
) -> List[Tuple[Dict, float, str]]:
    """
    Blend local catalog scoring with internet retrieval for prompt-based requests.
    """
    internet_songs, prompt_prefs = retrieve_songs_for_prompt(
        user_prompt,
        max_results=internet_k,
        api_key=api_key,
    )

    combined: List[Dict] = []
    seen_keys = set()

    for song in [*local_songs, *internet_songs]:
        key = (str(song.get("title", "")).strip().lower(), str(song.get("artist", "")).strip().lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        combined.append(song)

    scored: List[Tuple[Dict, float, str]] = []
    for song in combined:
        score, explanation = score_song(prompt_prefs, song)
        if song.get("source") == "internet":
            explanation = f"{explanation}, retrieved from internet"
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
