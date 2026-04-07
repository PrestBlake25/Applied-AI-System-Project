"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    # Supports module execution: python -m src.main
    from .recommender import load_songs, recommend_songs
except ImportError:
    # Supports direct script execution: python src/main.py
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 
    print(f"Loaded {len(songs)} songs.")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    my_taste = {
        "preferred_genres": ["hip-hop", "rock", "lofi"],
        "target": {
            "energy": 0.75,
            "tempo_bpm": 115,
            "valence": 0.60,
            "danceability": 0.70,
            "acousticness": 0.25
        },
        "weights": {
            "genre": 0.25,
            "mood": 0.10,
            "energy": 0.25,
            "tempo_bpm": 0.15,
            "valence": 0.10,
            "danceability": 0.10,
            "acousticness": 0.05
        }
    }
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    for rank, rec in enumerate(recommendations, start=1):
        # The recommender returns (song, score, explanation).
        song, score, explanation = rec
        reasons = [] if explanation == "No strong preference matches" else [r.strip() for r in explanation.split(",")]

        print(f"{rank}. {song['title']}")
        print(f"   Final Score: {score:.2f}")
        if reasons:
            print("   Reasons:")
            for reason in reasons:
                print(f"   - {reason}")
        else:
            print("   Reasons: No strong preference matches")
        print()


if __name__ == "__main__":
    main()
