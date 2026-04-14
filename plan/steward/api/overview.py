from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Request

from plan.steward.api import steward_error
from plan.steward.contracts import OverviewActionExecutionDto

router = APIRouter(prefix="/overview")


def _current(request: Request):
    return request.app.state.container


@router.get("/summary")
def overview_summary(request: Request, today: str | None = None):
    resolved_today = date.fromisoformat(today) if today else None
    return _current(request).overview.summary(today=resolved_today)


@router.post("/actions/execute", response_model=OverviewActionExecutionDto)
def overview_execute_action(payload: dict[str, Any], request: Request):
    from plan.steward.api.chat import resolve_today

    resolved_today = resolve_today(payload.get("today"))
    try:
        execution = _current(request).overview.execute_action(
            payload["action_id"],
            today=resolved_today,
        )
    except KeyError as exc:
        raise steward_error(404, "not_found", f"Overview action not available: {payload['action_id']}") from exc
    except PermissionError as exc:
        raise steward_error(409, "conflict", f"Overview action cannot execute: {payload['action_id']}") from exc

    _current(request).event_bus.publish(
        "overview.action_executed",
        {
            "action_id": payload["action_id"],
            "summary": execution.summary,
            "target_page": execution.target_page,
        },
    )
    if execution.created_task is not None:
        _current(request).event_bus.publish(
            "planning.suggestion_accepted",
            {
                "task_id": execution.created_task.id,
                "title": execution.created_task.title,
                "source": execution.created_task.source,
            },
        )
    if execution.note_draft is not None:
        _current(request).event_bus.publish(
            "notes.daily_review_draft_written",
            {
                "date": resolved_today.isoformat(),
                "path": str(execution.note_draft.path),
                "obsidian_url": execution.note_draft.obsidian_url,
            },
        )
    return execution
