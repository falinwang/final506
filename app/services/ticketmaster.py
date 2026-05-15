import httpx
from app import cache
from app.config import settings
from app.models import Concert

_BASE = "https://app.ticketmaster.com/discovery/v2/events"


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

    params = {
        "apikey": settings.ticketmaster_api_key,
        "classificationName": "music",
        "postalCode": postal_code,
        "countryCode": "US",
        "radius": str(radius),
        "unit": "miles",
        "size": str(limit),
        "sort": "date,asc",
    }

    owned = client is None
    if owned:
        client = httpx.AsyncClient(timeout=10)

    try:
        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owned:
            await client.aclose()

    events = data.get("_embedded", {}).get("events", [])
    concerts = [_parse(e) for e in events]
    await cache.set(cache_key, [c.model_dump() for c in concerts])
    return concerts
