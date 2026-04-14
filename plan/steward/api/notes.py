from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from plan.steward.api import steward_error

from plan.steward.contracts import NoteDraftDto, NotesDashboardDto

router = APIRouter(prefix="/notes")


def _current(request: Request):
    return request.app.state.container


@router.get("/index")
def notes_index(request: Request):
    notes = _current(request).notes.index()
    return {"notes": [note.model_dump(mode="json") for note in notes]}


@router.get("/dashboard", response_model=NotesDashboardDto)
def notes_dashboard(request: Request):
    return _current(request).notes.dashboard()


@router.post("/drafts/daily", response_model=NoteDraftDto, status_code=201)
def notes_daily_draft(payload: dict[str, Any], request: Request):
    note = _current(request).notes.write_daily_draft(
        date=payload["date"],
        title=payload["title"],
        content=payload["content"],
    )
    _current(request).event_bus.publish(
        "notes.daily_draft_written",
        {"path": str(note.path), "obsidian_url": note.obsidian_url},
    )
    return note


@router.post("/drafts/daily-review", response_model=NoteDraftDto, status_code=201)
def notes_daily_review_draft(payload: dict[str, Any], request: Request):
    note = _current(request).overview.write_daily_review_draft(payload["date"])
    _current(request).event_bus.publish(
        "notes.daily_review_draft_written",
        {
            "date": payload["date"],
            "path": str(note.path),
            "obsidian_url": note.obsidian_url,
        },
    )
    return note


@router.get("/drafts/daily-review", response_model=NoteDraftDto)
def notes_existing_daily_review_draft(date: str, request: Request):
    note = _current(request).overview.get_daily_review_draft(date)
    if note is None:
        raise steward_error(404, "not_found", f"Daily review draft not found for {date}")
    return note
