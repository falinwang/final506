# Time Range Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a preset time range filter (This Week / This Month / Next 3 Months) to Concert Finder so users can narrow results to upcoming events within a chosen window.

**Architecture:** The frontend computes `start_date` and `end_date` from the selected preset and passes them as `YYYY-MM-DD` query params to `/api/search`. The backend converts these to ISO 8601 datetimes (`T00:00:00Z` / `T23:59:59Z`), validates ordering, and forwards them to `fetch_concerts`, which passes them to the Ticketmaster API. The cache key is extended to include both date values.

**Tech Stack:** Python 3.11+, FastAPI, httpx, pytest, pytest-asyncio; vanilla JS + Tailwind CSS frontend.

---

### Task 1: Add dev test dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `pytest.ini`

- [ ] **Step 1: Add dev optional dependencies to pyproject.toml**

Add this section at the end of `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "anyio[trio]>=4.0.0",
]
```

- [ ] **Step 2: Install dev dependencies**

```bash
pip install -e ".[dev]"
```

Expected: pytest, pytest-asyncio, anyio installed into the venv with no errors.

- [ ] **Step 3: Verify pytest is available**

```bash
pytest --version
```

Expected output like: `pytest 8.x.x`

- [ ] **Step 4: Create tests directory and pytest config**

Create `tests/__init__.py` as an empty file.

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/__init__.py pytest.ini
git commit -m "chore: add pytest dev dependencies and test scaffold"
```

---

### Task 2: Extend fetch_concerts with date params and updated cache key

**Files:**
- Modify: `app/services/ticketmaster.py`
- Create: `tests/test_ticketmaster.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ticketmaster.py`:

```python
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

    call_params = client.get.call_args[1]["params"]
    assert call_params["startDateTime"] == "2026-05-14T00:00:00Z"
    assert call_params["endDateTime"] == "2026-08-12T23:59:59Z"


@pytest.mark.asyncio
async def test_fetch_concerts_omits_date_params_when_none():
    client = _make_client({"_embedded": {"events": []}})
    with patch("app.services.ticketmaster.cache.get", return_value=None), \
         patch("app.services.ticketmaster.cache.set"), \
         patch("app.services.ticketmaster._zip_to_latlong", return_value="42.28,-83.74"):
        await fetch_concerts("48104", client=client)

    call_params = client.get.call_args[1]["params"]
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ticketmaster.py -v
```

Expected: 4 failures — `fetch_concerts` does not yet accept `start_dt` / `end_dt`.

- [ ] **Step 3: Update fetch_concerts in app/services/ticketmaster.py**

Replace the entire `fetch_concerts` function with:

```python
async def fetch_concerts(
    postal_code: str,
    radius: int = 50,
    limit: int = 5,
    start_dt: str | None = None,
    end_dt: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[Concert]:
    start_key = start_dt or "none"
    end_key = end_dt or "none"
    cache_key = f"tm:{postal_code}:{radius}:{limit}:{start_key}:{end_key}"
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
            "segmentId": "KZFzniwnSyZfZ7v7n1",
            "classificationName": "Music",
            "latlong": latlong,
            "radius": str(radius),
            "unit": "miles",
            "size": str(limit * 3),
            "sort": "date,asc",
        }
        if start_dt:
            params["startDateTime"] = start_dt
        if end_dt:
            params["endDateTime"] = end_dt

        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if owned:
            await client.aclose()

    events = data.get("_embedded", {}).get("events", [])
    concerts = [
        c for e in events
        if not any(kw in e.get("name", "").lower() for kw in _NON_MUSIC_KEYWORDS)
        if (c := _parse(e))
    ][:limit]
    await cache.set(cache_key, [c.model_dump() for c in concerts])
    return concerts
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ticketmaster.py -v
```

Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/services/ticketmaster.py tests/test_ticketmaster.py
git commit -m "feat: extend fetch_concerts with start_dt/end_dt params and updated cache key"
```

---

### Task 3: Add start_date / end_date query params to /api/search

**Files:**
- Modify: `app/main.py`
- Create: `tests/test_search_api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_search_api.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_search_api.py -v
```

Expected: failures — `start_date` / `end_date` params not defined, `fetch_concerts` not called with `start_dt` / `end_dt`.

- [ ] **Step 3: Update app/main.py**

Add the import near the top of `app/main.py` (after existing imports):

```python
from datetime import date as _date
```

Replace the entire `search` endpoint with:

```python
@app.get("/api/search", response_model=list[SearchResult])
async def search(
    postal_code: str = Query(..., min_length=5, max_length=5, pattern=r"^\d{5}$"),
    radius: int = Query(50, ge=1, le=500),
    concerts_limit: int = Query(3, ge=1, le=10),
    tracks_limit: int = Query(10, ge=1, le=25),
    start_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_search_api.py -v
```

Expected: 4 PASSED.

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_search_api.py
git commit -m "feat: add start_date/end_date query params to /api/search with ISO conversion and validation"
```

---

### Task 4: Add preset toggle UI to the frontend

**Files:**
- Modify: `app/static/index.html`

- [ ] **Step 1: Insert the preset button group into the form**

In `app/static/index.html`, locate this line inside `<form id="searchForm">`:

```html
      <button
        type="submit"
```

Insert the following **before** that `<button type="submit">` block:

```html
      <div id="presetGroup" class="flex gap-1">
        <button type="button" data-days="7"
          class="preset-btn rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-3 text-sm transition hover:bg-zinc-700">
          This Week
        </button>
        <button type="button" data-days="30"
          class="preset-btn rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-3 text-sm transition hover:bg-zinc-700">
          This Month
        </button>
        <button type="button" data-days="90"
          class="preset-btn rounded-xl border border-zinc-700 bg-violet-600 px-3 py-3 text-sm font-semibold transition hover:bg-violet-500">
          Next 3 Months
        </button>
      </div>
```

- [ ] **Step 2: Add preset state tracking and isoDate helper to the script**

In the `<script>` block, immediately after the line `const resultsEl = document.getElementById('results');`, add:

```js
    let activePresetDays = 90;

    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        activePresetDays = parseInt(btn.dataset.days, 10);
        document.querySelectorAll('.preset-btn').forEach(b => {
          b.classList.remove('bg-violet-600', 'font-semibold', 'hover:bg-violet-500');
          b.classList.add('bg-zinc-800', 'hover:bg-zinc-700');
        });
        btn.classList.remove('bg-zinc-800', 'hover:bg-zinc-700');
        btn.classList.add('bg-violet-600', 'font-semibold', 'hover:bg-violet-500');
      });
    });

    function isoDate(offsetDays) {
      const d = new Date();
      d.setDate(d.getDate() + offsetDays);
      return d.toISOString().slice(0, 10);
    }
```

- [ ] **Step 3: Wire start_date and end_date into the fetch call**

In the `form.addEventListener('submit', ...)` handler, replace:

```js
        const res = await fetch(`/api/search?postal_code=${zip}&radius=${radius}&concerts_limit=3&tracks_limit=10`);
```

with:

```js
        const startDate = isoDate(0);
        const endDate = isoDate(activePresetDays);
        const res = await fetch(
          `/api/search?postal_code=${zip}&radius=${radius}&concerts_limit=3&tracks_limit=10&start_date=${startDate}&end_date=${endDate}`
        );
```

- [ ] **Step 4: Verify visually in the browser**

Start the dev server:

```bash
source venv/bin/activate && uvicorn app.main:app --reload
```

Open `http://localhost:8000`. Confirm:
- Three preset buttons appear between the radius dropdown and the Search button
- "Next 3 Months" is highlighted in violet on load
- Clicking "This Week" moves the violet highlight to that button
- After submitting a search, open DevTools → Network → click the `/api/search` request and confirm `start_date` and `end_date` appear in the query string

- [ ] **Step 5: Commit**

```bash
git add app/static/index.html
git commit -m "feat: add preset time range toggle UI to search form"
```

---

### Task 5: Context-aware empty-state message

**Files:**
- Modify: `app/static/index.html`

- [ ] **Step 1: Update the 404 error handler to include a hint for narrow presets**

In the `form.addEventListener('submit', ...)` handler, replace:

```js
        if (res.status === 404) throw new Error('No concerts found near this ZIP code. Try a larger radius.');
```

with:

```js
        if (res.status === 404) {
          const hint = activePresetDays < 90
            ? ' Try switching to Next 3 Months to see more upcoming events.'
            : '';
          throw new Error(`No concerts found near this ZIP code. Try a larger radius.${hint}`);
        }
```

- [ ] **Step 2: Update the empty data-array check to include the same hint**

In the same handler, replace:

```js
        if (!data.length) {
          showError('No concerts found near this ZIP code.');
          return;
        }
```

with:

```js
        if (!data.length) {
          const hint = activePresetDays < 90
            ? ' Try switching to Next 3 Months to see more upcoming events.'
            : '';
          showError(`No concerts found near this ZIP code.${hint}`);
          return;
        }
```

- [ ] **Step 3: Verify visually**

With the dev server running, search a rural ZIP (e.g. `59901`) with "This Week" selected. Confirm the error message says:
> "No concerts found near this ZIP code. Try a larger radius. Try switching to Next 3 Months to see more upcoming events."

Then switch to "Next 3 Months" and search again. Confirm no hint appears.

- [ ] **Step 4: Commit**

```bash
git add app/static/index.html
git commit -m "feat: show wider-range hint when no concerts found for narrow preset"
```
