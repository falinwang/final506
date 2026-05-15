# Concert Finder

A web app that finds nearby music concerts and surfaces top songs for each performing artist.

Built on Ticketmaster and iTunes APIs. Originally a 2018 CLI project (SI 506), modernized to a FastAPI web service.

---

## Features

- Search concerts by US ZIP code and distance radius
- Filter results by time range: **This Week**, **This Month**, or **Next 3 Months** (default)
- Top songs for each performing artist via iTunes
- In-memory cache with manual clear endpoint

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add your Ticketmaster API key
serve                  # starts on http://localhost:8000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search` | Search concerts + artist tracks |
| `POST` | `/api/cache/clear` | Flush in-memory cache |
| `GET` | `/api/health` | Health check |

### `/api/search` parameters

| Param | Default | Description |
|-------|---------|-------------|
| `postal_code` | required | 5-digit US ZIP |
| `radius` | `50` | Search radius in miles (1–500) |
| `concerts_limit` | `3` | Max concerts returned (1–10) |
| `tracks_limit` | `10` | Max tracks per artist (1–25) |
| `start_date` | today | Start of date window (`YYYY-MM-DD`) |
| `end_date` | — | End of date window (`YYYY-MM-DD`) |

## Development

```bash
# Run tests
pytest tests/ -v

# Run dev server with auto-reload
uvicorn app.main:app --reload
```

## Stack

- **Backend:** Python 3.11+, FastAPI, httpx, Pydantic
- **Geocoding:** Nominatim (OpenStreetMap)
- **Frontend:** Vanilla JS, Tailwind CSS
- **APIs:** Ticketmaster Discovery v2, iTunes Search
