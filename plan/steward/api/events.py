from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/events")


def _current(request: Request):
    return request.app.state.container


@router.get("/stream")
async def events_stream(request: Request):
    async def iterator():
        async for chunk in _current(request).event_bus.stream(
            is_disconnected=request.is_disconnected,
        ):
            yield chunk

    return StreamingResponse(
        iterator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
