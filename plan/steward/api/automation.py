from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

router = APIRouter(prefix="/automation")


def _current(request: Request):
    return request.app.state.container


@router.get("/status")
def automation_status(request: Request, now: str | None = None):
    timestamp = (
        datetime.fromisoformat(now).replace(tzinfo=timezone.utc)
        if now
        else datetime.now(timezone.utc)
    )
    overview = _current(request).overview.summary(today=timestamp.date())
    status = _current(request).automation.status(timestamp, overview=overview)
    _current(request).event_bus.publish(
        "automation.status_checked",
        {"signal_count": len(status.signals)},
    )
    return status


@router.get("/automation/runner/status")
def automation_runner_status(request: Request):
    runner = _current(request).runner
    return {
        "running": runner._running,
        "interval_seconds": runner._interval,
        "has_active_task": runner._task is not None and not runner._task.done(),
    }
