import httpx
from app import cache
from app.config import settings
from app.models import ArtistTracks, Track

_BASE = "https://itunes.apple.com/search"


def _ms_to_mmss(ms: int) -> str:
    total = ms // 1000
    return f"{total // 60}:{total % 60:02d}"


def _parse_track(raw: dict) -> Track | None:
    if "trackName" not in raw or "trackTimeMillis" not in raw:
        return None
    return Track(
        artist=raw.get("artistName", ""),
        title=raw["trackName"],
        album=raw.get("collectionName", ""),
        length=_ms_to_mmss(raw["trackTimeMillis"]),
        release_date=raw.get("releaseDate", "")[:10],
    )


async def fetch_tracks(
    artist: str,
    limit: int = 10,
    client: httpx.AsyncClient | None = None,
) -> ArtistTracks:
    cache_key = f"itunes:{artist}:{limit}"
    if cached := await cache.get(cache_key, settings.cache_ttl_seconds):
        return ArtistTracks(**cached)

    params = {
        "term": artist,
        "media": "music",
        "entity": "musicTrack",
        "limit": str(limit * 3),  # fetch extra to survive filtering
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

    tracks = [t for raw in data.get("results", []) if (t := _parse_track(raw))]
    tracks.sort(key=lambda t: t.release_date, reverse=True)
    result = ArtistTracks(artist=artist, tracks=tracks[:limit])
    await cache.set(cache_key, result.model_dump())
    return result


async def fetch_tracks_for_many(
    artists: list[str],
    limit: int = 10,
) -> list[ArtistTracks]:
    import asyncio

    async with httpx.AsyncClient(timeout=10) as client:
        return list(
            await asyncio.gather(
                *[fetch_tracks(a, limit, client) for a in artists]
            )
        )
