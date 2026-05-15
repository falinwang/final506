import asyncio
from datetime import date as _date
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import cache as _cache
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
    start_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
    try:
        if start_date:
            _date.fromisoformat(start_date)
        if end_date:
            _date.fromisoformat(end_date)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    resolved_start = start_date or _date.today().isoformat()
    if end_date and end_date < resolved_start:
        raise HTTPException(422, "end_date must not be before start_date")

    start_dt = f"{resolved_start}T00:00:00Z"
    end_dt = f"{end_date}T23:59:59Z" if end_date else None

    try:
        concerts = await fetch_concerts(
            postal_code, radius, concerts_limit, start_dt=start_dt, end_dt=end_dt
        )
    except Exception as e:
        raise HTTPException(502, f"Ticketmaster error: {e}")

    if not concerts:
        raise HTTPException(404, "No concerts found for this area.")

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

    tracks_by_artist = {lt.artist: lt for lt in all_lineups}

    results = []
    for concert in concerts:
        lineups = [tracks_by_artist[a] for a in concert.artists if a in tracks_by_artist]
        results.append(SearchResult(concert=concert, lineups=lineups))

    return results


@app.post("/api/cache/clear")
async def clear_cache():
    count = await _cache.clear()
    return {"cleared": count}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def run():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
