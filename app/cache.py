import asyncio
import time
from typing import Any

_store: dict[str, tuple[Any, float]] = {}
_lock = asyncio.Lock()


async def get(key: str, ttl: int) -> Any | None:
    async with _lock:
        entry = _store.get(key)
        if entry and time.monotonic() - entry[1] < ttl:
            return entry[0]
        return None


async def set(key: str, value: Any) -> None:
    async with _lock:
        _store[key] = (value, time.monotonic())
