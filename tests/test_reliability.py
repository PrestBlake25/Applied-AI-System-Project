from src.main import main
from src.rag import fetch_songs_from_itunes, retrieve_songs_for_prompt
from src.recommender import recommend_songs_with_rag


def test_main_handles_empty_input_then_quit(monkeypatch, capsys):
    monkeypatch.setattr("src.main.load_songs", lambda _path: [])
    monkeypatch.setattr("src.main.recommend_songs_with_rag", lambda *_args, **_kwargs: [])

    responses = iter(["", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))

    main()
    captured = capsys.readouterr().out

    assert "Please enter a music request" in captured
    assert "Goodbye." in captured


def test_main_prints_recommendations(monkeypatch, capsys):
    local_song = {
        "id": 1,
        "title": "Local Song",
        "artist": "Local Artist",
        "genre": "rock",
        "mood": "chill",
        "energy": 0.45,
        "tempo_bpm": 100,
        "valence": 0.6,
        "danceability": 0.5,
        "acousticness": 0.7,
    }

    monkeypatch.setattr("src.main.load_songs", lambda _path: [local_song])

    def fake_recommend(_prompt, _songs, k=5, internet_k=12):
        return [
            (
                {
                    "title": "Test Internet Song",
                    "artist": "Web Artist",
                    "genre": "rock",
                    "mood": "chill",
                    "energy": 0.44,
                    "source": "internet",
                },
                8.5,
                "mood match, retrieved from internet",
            )
        ]

    monkeypatch.setattr("src.main.recommend_songs_with_rag", fake_recommend)

    responses = iter(["something mellow", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))

    main()
    captured = capsys.readouterr().out

    assert "Top recommendations (internet-augmented):" in captured
    assert "Test Internet Song by Web Artist [internet]" in captured


def test_main_handles_keyboard_interrupt(monkeypatch, capsys):
    monkeypatch.setattr("src.main.load_songs", lambda _path: [])

    def raise_keyboard_interrupt(_prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)

    main()
    captured = capsys.readouterr().out

    assert "Goodbye." in captured


def test_recommend_songs_with_rag_deduplicates_same_song(monkeypatch):
    local_song = {
        "id": 1,
        "title": "Shared Song",
        "artist": "Same Artist",
        "genre": "rock",
        "mood": "chill",
        "energy": 0.45,
        "tempo_bpm": 100,
        "valence": 0.6,
        "danceability": 0.5,
        "acousticness": 0.7,
    }

    internet_duplicate = {
        "id": 999,
        "title": "Shared Song",
        "artist": "Same Artist",
        "genre": "rock",
        "mood": "chill",
        "energy": 0.46,
        "tempo_bpm": 101,
        "valence": 0.6,
        "danceability": 0.5,
        "acousticness": 0.6,
        "source": "internet",
    }

    def fake_retrieve(_prompt, max_results=10, api_key=None):
        return [internet_duplicate], {
            "genre": "rock",
            "mood": "chill",
            "energy": 0.45,
            "likes_acoustic": True,
        }

    monkeypatch.setattr("src.recommender.retrieve_songs_for_prompt", fake_retrieve)

    results = recommend_songs_with_rag("mellow rock", [local_song], k=5)

    titles = [song["title"] for song, _, _ in results]
    assert titles.count("Shared Song") == 1


def test_retrieve_falls_back_to_itunes_when_lastfm_returns_empty(monkeypatch):
    monkeypatch.setenv("LASTFM_API_KEY", "env-key")
    monkeypatch.setattr("src.rag.fetch_songs_from_lastfm", lambda *_args, **_kwargs: [])

    def fake_itunes(_terms, max_results=10, timeout=8):
        return [
            {
                "trackName": "Fallback Song",
                "artistName": "Fallback Artist",
                "primaryGenreName": "Rock",
                "trackId": 77,
            }
        ]

    monkeypatch.setattr("src.rag.fetch_songs_from_itunes", fake_itunes)

    songs, _prefs = retrieve_songs_for_prompt("like metallica", max_results=3)

    assert songs
    assert songs[0]["title"] == "Fallback Song"


def test_fetch_songs_from_itunes_returns_empty_on_request_error(monkeypatch):
    def fail_request(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.rag.requests.get", fail_request)

    results = fetch_songs_from_itunes(["metallica"], max_results=5)

    assert results == []
