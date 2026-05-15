import httpx
from app import cache
from app.config import settings
from app.models import Concert

_BASE = "https://app.ticketmaster.com/discovery/v2/events"
_NOMINATIM = "https://nominatim.openstreetmap.org/search"


async def _zip_to_latlong(postal_code: str, client: httpx.AsyncClient) -> str | None:
    cache_key = f"geo:{postal_code}"
    if cached := await cache.get(cache_key, 86400 * 30):  # 30-day cache for geo
        return cached

    resp = await client.get(
        _NOMINATIM,
        params={"postalcode": postal_code, "country": "US", "format": "json", "limit": "1"},
        headers={"User-Agent": "concert-finder/2.0"},
    )
    results = resp.json()
    if not results:
        return None

    latlong = f"{results[0]['lat']},{results[0]['lon']}"
    await cache.set(cache_key, latlong)
    return latlong


def _parse(event: dict) -> Concert:
    artists = [a["name"] for a in event.get("_embedded", {}).get("attractions", [])]
    start = event["dates"]["start"]
    return Concert(
        event_name=event["name"],
        artists=artists or [event["name"]],
        date=start.get("localDate", "TBA"),
        time=start.get("localTime"),
        url=event.get("url", ""),
    )


async def fetch_concerts(
    postal_code: str,
    radius: int = 50,
    limit: int = 5,
    client: httpx.AsyncClient | None = None,
) -> list[Concert]:
    cache_key = f"tm:{postal_code}:{radius}:{limit}"
    if cached := await cache.get(cache_key, settings.cache_ttl_seconds):
        return [Concert(**c) for c in cached]

    owned = client is None
    if owned:
        client = httpx.AsyncClient(timeout=10)

    try:
        latlong = await _zip_to_latlong(postal_code, client)
        if not latlong:
            return []

        params = {
            "apikey": settings.ticketmaster_api_key,
            "segmentId": "KZFzniwnSyZfZ7v7n1",  # Music (stable official ID)
            "classificationName": "Music",
            "latlong": latlong,
            "radius": str(radius),
            "unit": "miles",
            "size": str(limit * 3),  # fetch extra to survive filtering
            "sort": "date,asc",
        }

        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owned:
            await client.aclose()

    _NON_MUSIC_KEYWORDS = {"tour", "guided", "ceremony", "graduation", "exhibition", "comedy"}

    events = data.get("_embedded", {}).get("events", [])
    concerts = [
        c for e in events
        if not any(kw in e.get("name", "").lower() for kw in _NON_MUSIC_KEYWORDS)
        if (c := _parse(e))
    ][:limit]
    await cache.set(cache_key, [c.model_dump() for c in concerts])
    return concerts
