import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ticketmaster import fetch_concerts


def _make_client(json_response: dict) -> AsyncMock:
    resp = MagicMock()
    resp.json.return_value = json_response
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    client.get = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_fetch_concerts_passes_start_and_end_dt():
    client = _make_client({"_embedded": {"events": []}})
    with patch("app.services.ticketmaster.cache.get", return_value=None), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts(
            "48104",
            start_dt="2026-05-14T00:00:00Z",
            end_dt="2026-08-12T23:59:59Z",
            client=client,
        )

    call_params = client.get.call_args.kwargs["params"]
    assert call_params["startDateTime"] == "2026-05-14T00:00:00Z"
    assert call_params["endDateTime"] == "2026-08-12T23:59:59Z"


@pytest.mark.asyncio
async def test_fetch_concerts_omits_date_params_when_none():
    client = _make_client({"_embedded": {"events": []}})
    with patch("app.services.ticketmaster.cache.get", return_value=None), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts("48104", client=client)

    call_params = client.get.call_args.kwargs["params"]
    assert "startDateTime" not in call_params
    assert "endDateTime" not in call_params


@pytest.mark.asyncio
async def test_fetch_concerts_cache_key_includes_dates():
    client = _make_client({"_embedded": {"events": []}})
    captured_keys = []

    async def mock_cache_get(key, ttl):
        captured_keys.append(key)
        return None

    with patch("app.services.ticketmaster.cache.get", side_effect=mock_cache_get), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts(
            "48104",
            start_dt="2026-05-14T00:00:00Z",
            end_dt="2026-08-12T23:59:59Z",
            client=client,
        )

    concert_keys = [k for k in captured_keys if k.startswith("tm:")]
    assert len(concert_keys) == 1
    assert "2026-05-14T00:00:00Z" in concert_keys[0]
    assert "2026-08-12T23:59:59Z" in concert_keys[0]


@pytest.mark.asyncio
async def test_fetch_concerts_passes_only_start_dt():
    client = _make_client({"_embedded": {"events": []}})
    with patch("app.services.ticketmaster.cache.get", return_value=None), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts(
            "48104",
            start_dt="2026-05-14T00:00:00Z",
            client=client,
        )

    call_params = client.get.call_args.kwargs["params"]
    assert call_params["startDateTime"] == "2026-05-14T00:00:00Z"
    assert "endDateTime" not in call_params


@pytest.mark.asyncio
async def test_fetch_concerts_cache_key_uses_none_placeholder_when_no_dates():
    client = _make_client({"_embedded": {"events": []}})
    captured_keys = []

    async def mock_cache_get(key, ttl):
        captured_keys.append(key)
        return None

    with patch("app.services.ticketmaster.cache.get", side_effect=mock_cache_get), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts("48104", client=client)

    concert_keys = [k for k in captured_keys if k.startswith("tm:")]
    assert len(concert_keys) == 1
    assert concert_keys[0].endswith(":none:none")
