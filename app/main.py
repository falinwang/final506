import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import SearchResult
from app.services.itunes import fetch_tracks_for_many
from app.services.ticketmaster import fetch_concerts

app = FastAPI(title="Concert Finder", version="2.0.0")

_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(_STATIC / "index.html")


@app.get("/api/search", response_model=list[SearchResult])
async def search(
    postal_code: str = Query(..., min_length=5, max_length=5, pattern=r"^\d{5}$"),
    radius: int = Query(50, ge=1, le=500),
    concerts_limit: int = Query(3, ge=1, le=10),
    tracks_limit: int = Query(10, ge=1, le=25),
):
    try:
        concerts = await fetch_concerts(postal_code, radius, concerts_limit)
    except Exception as e:
        raise HTTPException(502, f"Ticketmaster error: {e}")

    if not concerts:
        raise HTTPException(404, "No concerts found for this area.")

    # Flatten unique artists across all concerts, preserve order
    seen: set[str] = set()
    unique_artists: list[str] = []
    for concert in concerts:
        for artist in concert.artists:
            if artist not in seen:
                seen.add(artist)
                unique_artists.append(artist)

    try:
        all_lineups = await fetch_tracks_for_many(unique_artists, tracks_limit)
    except Exception as e:
        raise HTTPException(502, f"iTunes error: {e}")

    # Map artist → tracks for quick lookup
    tracks_by_artist = {lt.artist: lt for lt in all_lineups}

    results = []
    for concert in concerts:
        lineups = [
            tracks_by_artist[a]
            for a in concert.artists
            if a in tracks_by_artist
        ]
        results.append(SearchResult(concert=concert, lineups=lineups))

    return results


@app.get("/api/debug/ticketmaster")
async def debug_ticketmaster():
    import httpx
    from app.config import settings

    base = "https://app.ticketmaster.com/discovery/v2/events"
    key = settings.ticketmaster_api_key

    async with httpx.AsyncClient(timeout=10) as client:
        # No location — just "are there ANY events?"
        r_global = await client.get(base, params={"apikey": key, "size": "1"})
        # Keyword search instead of postal code
        r_keyword = await client.get(base, params={"apikey": key, "keyword": "concert", "size": "1"})
        # City name instead of postal code
        r_city = await client.get(base, params={"apikey": key, "city": "Los Angeles", "size": "1"})

    def summary(r: httpx.Response) -> dict:
        body = r.json()
        total = body.get("page", {}).get("totalElements", "n/a")
        first = None
        events = body.get("_embedded", {}).get("events", [])
        if events:
            first = events[0].get("name")
        return {"status": r.status_code, "total": total, "first_event": first}

    return {
        "key_used": f"{key[:6]}...{key[-4:]}",
        "global_no_filter": summary(r_global),
        "keyword_concert":  summary(r_keyword),
        "city_los_angeles": summary(r_city),
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def run():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
