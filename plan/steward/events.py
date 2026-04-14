from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class _Subscriber:
    start_after_event_id: int
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[str]


class EventBus:
    def __init__(self) -> None:
        self._history: list[tuple[int, str]] = []
        self._next_event_id = 1
        self._subscribers: list[_Subscriber] = []

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        packet = (
            f"event: {event}\n"
            f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        )
        event_id = self._next_event_id
        self._next_event_id += 1
        self._history.append((event_id, packet))
        self._history = self._history[-50:]
        stale_subscribers: list[_Subscriber] = []

        for subscriber in self._subscribers:
            try:
                subscriber.loop.call_soon_threadsafe(
                    subscriber.queue.put_nowait,
                    packet,
                )
            except RuntimeError:
                stale_subscribers.append(subscriber)

        for subscriber in stale_subscribers:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    async def stream(
        self,
        is_disconnected=None,
        heartbeat_seconds: float = 15.0,
    ) -> AsyncIterator[str]:
        connected = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "connected",
        }
        yield (
            "event: connected\n"
            f"data: {json.dumps(connected, ensure_ascii=False)}\n\n"
        )

        subscriber = _Subscriber(
            start_after_event_id=self._next_event_id,
            loop=asyncio.get_running_loop(),
            queue=asyncio.Queue(),
        )
        self._subscribers.append(subscriber)

        try:
            for event_id, packet in list(self._history):
                if event_id < subscriber.start_after_event_id:
                    yield packet

            while True:
                if is_disconnected is not None and await is_disconnected():
                    break

                try:
                    packet = await asyncio.wait_for(
                        subscriber.queue.get(),
                        timeout=heartbeat_seconds,
                    )
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue

                yield packet
        finally:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)
