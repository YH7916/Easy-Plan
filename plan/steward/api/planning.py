from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Request

from plan.steward.api import steward_error
from plan.steward.contracts import TaskDto, TaskSuggestionDto, TaskStatusUpdateDto, TodayQueueDto

router = APIRouter(prefix="/planning")


def _current(request: Request):
    return request.app.state.container


@router.get("/tasks", response_model=list[TaskDto])
def planning_tasks(request: Request):
    return _current(request).planning.list_tasks()


@router.get("/suggestions", response_model=list[TaskSuggestionDto])
def planning_suggestions(request: Request):
    source_items = _current(request).sources.list_items()
    return _current(request).planning.list_suggestions(source_items)


@router.post("/tasks", response_model=TaskDto, status_code=201)
def planning_create_task(payload: dict[str, Any], request: Request):
    task = _current(request).planning.create_task(
        title=payload["title"],
        project=payload.get("project"),
        due=payload.get("due"),
        priority=payload.get("priority", 0),
    )
    _current(request).event_bus.publish("planning.task_created", task.model_dump())
    return task


@router.post("/suggestions/accept", response_model=TaskDto, status_code=201)
def planning_accept_suggestion(payload: dict[str, Any], request: Request):
    suggestion = TaskSuggestionDto.model_validate(payload)
    task = _current(request).planning.accept_suggestion(suggestion)
    _current(request).event_bus.publish(
        "planning.suggestion_accepted",
        {
            "task_id": task.id,
            "title": task.title,
            "source": task.source,
        },
    )
    return task


@router.post("/tasks/{task_id}/complete", response_model=TaskDto)
def planning_complete_task(task_id: str, request: Request):
    try:
        task = _current(request).planning.complete_task(task_id)
    except KeyError as exc:
        raise steward_error(404, "not_found", f"Task not found: {task_id}") from exc
    _current(request).event_bus.publish("planning.task_completed", task.model_dump())
    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskDto)
def planning_update_task_status(task_id: str, payload: TaskStatusUpdateDto, request: Request):
    try:
        task = _current(request).planning.transition_task(task_id, payload.status)
    except KeyError as exc:
        raise steward_error(404, "not_found", f"Task not found: {task_id}") from exc
    except ValueError as exc:
        raise steward_error(400, "bad_request", str(exc)) from exc
    except PermissionError as exc:
        raise steward_error(409, "conflict", str(exc)) from exc
    _current(request).event_bus.publish("planning.task_status_updated", {
        "task_id": task_id,
        "new_status": payload.status,
    })
    return task


@router.get("/today-queue", response_model=TodayQueueDto)
def planning_today_queue(request: Request, today: str | None = None):
    resolved_today = date.fromisoformat(today) if today else None
    return _current(request).planning.today_queue(today=resolved_today)
