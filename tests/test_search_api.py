from datetime import date
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import ArtistTracks, Concert, Track

client = TestClient(app)

_CONCERT = Concert(
    event_name="Test Show",
    artists=["Artist A"],
    date="2026-06-01",
    time="20:00:00",
    url="http://example.com",
)
_TRACKS = ArtistTracks(
    artist="Artist A",
    tracks=[Track(artist="Artist A", title="Song 1", album="Album 1", length="3:30", release_date="2020-01-01")],
)


def _patch_services(concerts=None, tracks=None):
    if concerts is None:
        concerts = [_CONCERT]
    if tracks is None:
        tracks = [_TRACKS]
    return (
        patch("app.main.fetch_concerts", new=AsyncMock(return_value=concerts)),
        patch("app.main.fetch_tracks_for_many", new=AsyncMock(return_value=tracks)),
    )


def test_search_passes_start_and_end_date_to_fetch_concerts():
    p1, p2 = _patch_services()
    with p1 as mock_fetch, p2:
        client.get("/api/search?postal_code=48104&start_date=2026-05-14&end_date=2026-08-12")

    _, kwargs = mock_fetch.call_args
    assert kwargs.get("start_dt") == "2026-05-14T00:00:00Z"
    assert kwargs.get("end_dt") == "2026-08-12T23:59:59Z"


def test_search_defaults_start_date_to_today():
    today = date.today().isoformat()
    p1, p2 = _patch_services()
    with p1 as mock_fetch, p2:
        client.get("/api/search?postal_code=48104")

    _, kwargs = mock_fetch.call_args
    assert kwargs.get("start_dt") == f"{today}T00:00:00Z"
    assert kwargs.get("end_dt") is None


def test_search_returns_422_when_end_before_start():
    resp = client.get("/api/search?postal_code=48104&start_date=2026-08-12&end_date=2026-05-14")
    assert resp.status_code == 422


def test_search_returns_results_with_date_params():
    p1, p2 = _patch_services()
    with p1, p2:
        resp = client.get("/api/search?postal_code=48104&start_date=2026-05-14&end_date=2026-08-12")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["concert"]["event_name"] == "Test Show"


def test_search_accepts_same_start_and_end_date():
    p1, p2 = _patch_services()
    with p1, p2:
        resp = client.get("/api/search?postal_code=48104&start_date=2026-06-01&end_date=2026-06-01")
    assert resp.status_code == 200


def test_search_returns_422_when_end_date_is_past_and_start_omitted():
    resp = client.get("/api/search?postal_code=48104&end_date=2000-01-01")
    assert resp.status_code == 422


def test_search_returns_422_for_calendar_invalid_date():
    resp = client.get("/api/search?postal_code=48104&start_date=2026-02-30")
    assert resp.status_code == 422


def test_search_inglewood_returns_concert_and_tracks():
    inglewood_concert = Concert(
        event_name="Kia Forum Night",
        artists=["Kendrick Lamar"],
        date="2026-07-04",
        time="20:00:00",
        url="http://ticketmaster.com/kia-forum",
    )
    inglewood_tracks = ArtistTracks(
        artist="Kendrick Lamar",
        tracks=[
            Track(artist="Kendrick Lamar", title="HUMBLE.", album="DAMN.", length="2:57", release_date="2017-04-14"),
            Track(artist="Kendrick Lamar", title="DNA.", album="DAMN.", length="3:05", release_date="2017-04-14"),
        ],
    )
    p1, p2 = _patch_services(concerts=[inglewood_concert], tracks=[inglewood_tracks])
    with p1 as mock_fetch, p2:
        resp = client.get("/api/search?postal_code=90301&radius=25&start_date=2026-07-01&end_date=2026-07-31")

    assert resp.status_code == 200
    args, kwargs = mock_fetch.call_args
    assert args[0] == "90301"
    assert args[1] == 25
    assert kwargs.get("start_dt") == "2026-07-01T00:00:00Z"
    assert kwargs.get("end_dt") == "2026-07-31T23:59:59Z"

    data = resp.json()
    assert len(data) == 1
    assert data[0]["concert"]["event_name"] == "Kia Forum Night"
    assert data[0]["concert"]["artists"] == ["Kendrick Lamar"]
    assert data[0]["lineups"][0]["artist"] == "Kendrick Lamar"
    assert len(data[0]["lineups"][0]["tracks"]) == 2
    assert data[0]["lineups"][0]["tracks"][0]["title"] == "HUMBLE."
