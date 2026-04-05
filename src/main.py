"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

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
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
