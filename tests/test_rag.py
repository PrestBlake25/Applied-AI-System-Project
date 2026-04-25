from src.rag import parse_prompt_to_query, retrieve_songs_for_prompt
from src.recommender import recommend_songs_with_rag


def test_parse_prompt_detects_seed_and_mellow_preferences():
    parsed = parse_prompt_to_query("something like Metallica but a bit more mellow")

    assert parsed["seed_artist"] == "Metallica"
    assert parsed["mood"] == "chill"
    assert parsed["energy"] <= 0.5
    assert parsed["genre"] == "rock"


def test_recommend_with_rag_includes_internet_song(monkeypatch):
    local_songs = [
        {
            "id": 1,
            "title": "Loud Track",
            "artist": "Local Band",
            "genre": "rock",
            "mood": "intense",
            "energy": 0.9,
            "tempo_bpm": 140,
            "valence": 0.5,
            "danceability": 0.5,
            "acousticness": 0.1,
        }
    ]

    internet_song = {
        "id": 999,
        "title": "Mellow-ish Rock",
        "artist": "Web Artist",
        "genre": "rock",
        "mood": "chill",
        "energy": 0.45,
        "tempo_bpm": 108,
        "valence": 0.6,
        "danceability": 0.52,
        "acousticness": 0.7,
        "source": "internet",
    }

    def fake_retrieve(_prompt, max_results=10, api_key=None):
        return [internet_song], {
            "genre": "rock",
            "mood": "chill",
            "energy": 0.45,
            "likes_acoustic": True,
        }

    monkeypatch.setattr("src.recommender.retrieve_songs_for_prompt", fake_retrieve)

    results = recommend_songs_with_rag(
        "something like Metallica but a bit more mellow",
        local_songs,
        k=3,
        internet_k=5,
    )

    assert any(song.get("source") == "internet" for song, _, _ in results)


def test_retrieve_songs_uses_lastfm_when_api_key_provided(monkeypatch):
    def fake_lastfm(_terms, api_key, max_results=10, timeout=8):
        assert api_key == "test-key"
        return [
            {
                "trackName": "Fade to Black",
                "artistName": "Metallica",
                "primaryGenreName": "",
                "trackId": 123,
            }
        ]

    def fake_itunes(_terms, max_results=10, timeout=8):
        raise AssertionError("iTunes should not be called when Last.fm succeeds")

    monkeypatch.setattr("src.rag.fetch_songs_from_lastfm", fake_lastfm)
    monkeypatch.setattr("src.rag.fetch_songs_from_itunes", fake_itunes)

    songs, _prefs = retrieve_songs_for_prompt(
        "something like Metallica but a bit more mellow",
        max_results=5,
        api_key="test-key",
    )

    assert songs
    assert songs[0]["artist"] == "Metallica"


def test_retrieve_songs_falls_back_to_itunes_when_no_api_key(monkeypatch):
    def fake_itunes(_terms, max_results=10, timeout=8):
        return [
            {
                "trackName": "Nothing Else Matters",
                "artistName": "Metallica",
                "primaryGenreName": "Rock",
                "trackId": 456,
            }
        ]

    monkeypatch.setattr("src.rag.fetch_songs_from_itunes", fake_itunes)

    songs, _prefs = retrieve_songs_for_prompt(
        "something like Metallica but a bit more mellow",
        max_results=5,
        api_key=None,
    )

    assert songs
    assert songs[0]["source"] == "internet"
