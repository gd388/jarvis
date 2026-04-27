"""Thread-safe event bus: Jarvis (sync thread) → FastAPI WebSocket (async loop)."""

import asyncio
import json
from typing import Any

_loop: asyncio.AbstractEventLoop | None = None
_queues: list[asyncio.Queue] = []


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


async def subscribe() -> "asyncio.Queue[str]":
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    _queues.append(q)
    return q


async def unsubscribe(q: "asyncio.Queue[str]") -> None:
    if q in _queues:
        _queues.remove(q)


def emit(event_type: str, **kwargs: Any) -> None:
    """Broadcast an event from any thread — thread-safe, never raises."""
    if _loop is None or _loop.is_closed() or not _queues:
        return
    payload = json.dumps({"type": event_type, **kwargs})

    def _put() -> None:
        for q in list(_queues):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    try:
        _loop.call_soon_threadsafe(_put)
    except RuntimeError:
        pass
