"""FastAPI server — WebSocket event stream + serve the React frontend."""

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api import events
from config.settings import settings

_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(title="Jarvis", docs_url=None, redoc_url=None)


@app.get("/config")
async def get_config() -> JSONResponse:
    return JSONResponse({"wakeWord": settings.WAKE_WORD.upper()})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    q = await events.subscribe()
    try:
        while True:
            msg = await q.get()
            await ws.send_text(msg)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await events.unsubscribe(q)


# Mount the built React app — must be last so /ws + /config take priority
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="static")
