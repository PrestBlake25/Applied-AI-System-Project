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
    from .recommender import load_songs, recommend_songs_with_rag
except ImportError:
    # Supports direct script execution: python src/main.py
    from recommender import load_songs, recommend_songs_with_rag


def main() -> None:
    songs = load_songs("data/songs.csv")
    print("\nTell me what kind of music you want.")
    print("Example: something like Metallica but a bit more mellow")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            prompt = input("What do you want to hear? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not prompt:
            print("Please enter a music request, or type 'quit' to exit.\n")
            continue

        if prompt.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            break

        try:
            count_input = input("How many songs do you want to hear? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if count_input.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            break

        try:
            result_count = int(count_input)
            if result_count <= 0:
                raise ValueError
        except ValueError:
            print("Please enter a positive number for how many songs to return.\n")
            continue

        print(f"\n{'='*70}")
        print(f"Request: {prompt}")
        print(f"{'='*70}\n")

        rag_recommendations = recommend_songs_with_rag(prompt, songs, k=result_count, internet_k=12)

        if not rag_recommendations:
            print("No recommendations found. Try another prompt.\n")
            continue

        print("Top recommendations (internet-augmented):\n")
        for rank, rec in enumerate(rag_recommendations, start=1):
            song, score, explanation = rec
            source = song.get("source", "local")
            print(f"{rank}. {song['title']} by {song['artist']} [{source}]")
            print(f"   Score: {score}")
            print(f"   Genre: {song['genre']}, Mood: {song['mood']}, Energy: {song['energy']}")
            print(f"   Match: {explanation}")
            print()

        try:
            end_program = input("Do you want to end the program? (yes/no): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if end_program in {"y", "yes", "q", "quit", "exit"}:
            print("Goodbye.")
            break


if __name__ == "__main__":
    main()
