# Time Range Filter — Design Spec

**Date:** 2026-05-14
**Branch:** claude/modernize-legacy-project-3KWec

## Overview

Add a preset time range filter to the Concert Finder search UI so users can narrow results to upcoming events within a chosen window. The frontend computes concrete dates from the selected preset and passes them to the existing `/api/search` endpoint, which forwards them to Ticketmaster.

## Presets

| Label | JS offset from today | Default |
|---|---|---|
| This Week | +7 days | |
| This Month | +30 days | |
| Next 3 Months | +90 days | ✓ |

"Next 3 Months" is pre-selected on page load.

## Backend Changes

### `app/services/ticketmaster.py`

`fetch_concerts` gains two optional string parameters:

```python
async def fetch_concerts(
    postal_code: str,
    radius: int = 50,
    limit: int = 5,
    start_dt: str | None = None,
    end_dt: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[Concert]:
```

When provided, `start_dt` and `end_dt` are added to the Ticketmaster API call as `startDateTime` and `endDateTime` respectively.

**Cache key format:**

```
tm:{postal_code}:{radius}:{limit}:{start_dt or 'none'}:{end_dt or 'none'}
```

Using the literal string `"none"` as placeholder when a date is absent keeps key length consistent and avoids parsing ambiguity.

**Geocoding guard:** if `_zip_to_latlong` returns `None`, the function returns `[]` immediately — before any date params are applied.

### `app/main.py`

Two optional query params added to `/api/search`:

```python
start_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
end_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
```

**Default:** if `start_date` is omitted, it defaults to today (`date.today().isoformat()`) so past events are never returned.

**Validation:** if both are provided and `end_date < start_date`, raise `HTTPException(422, "end_date must not be before start_date")`.

**ISO 8601 conversion before passing to `fetch_concerts`:**

- `start_date` → `{start_date}T00:00:00Z` (start of day)
- `end_date` → `{end_date}T23:59:59Z` (end of day, captures evening shows)

## Frontend Changes

### `app/static/index.html`

**Preset toggle UI** — a row of three buttons inserted between the radius dropdown and the Search button:

- Unselected: `bg-zinc-800 border border-zinc-700`
- Selected: `bg-violet-600` (matches existing Search button)
- Clicking a preset button deselects the others and updates the active visual state

**JS date computation on submit:**

```js
const PRESETS = { week: 7, month: 30, '3months': 90 };

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10); // YYYY-MM-DD
}
```

`start_date` = today's date; `end_date` = today + preset offset.

Both are appended as query params to the fetch URL.

**Context-aware empty-state message:**

When the API returns 0 results and the active preset is "This Week" or "This Month", the error message appends:

> "Try switching to Next 3 Months to see more upcoming events."

When the preset is already "Next 3 Months", show only the standard no-results message.

## Error Handling

| Scenario | Response |
|---|---|
| `end_date < start_date` | HTTP 422 from `main.py` |
| Geocoding returns no result | `fetch_concerts` returns `[]` → HTTP 404 |
| Ticketmaster API error | HTTP 502 (existing behavior, unchanged) |
| 0 results with narrow preset | Frontend hint to widen the time range |

## Out of Scope

- Custom date picker (no free-form date input)
- Server-side preset name mapping (dates are always computed on the frontend)
- Persisting the selected preset across page reloads
