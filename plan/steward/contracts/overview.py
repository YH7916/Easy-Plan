from __future__ import annotations

from pydantic import BaseModel, Field

from plan.steward.contracts.planning import TaskDto
from plan.steward.contracts.notes import NoteDraftDto


class OverviewActionDto(BaseModel):
    id: str
    label: str
    description: str
    target_page: str
    chat_prompt: str | None = None
    can_execute: bool = False
    execute_label: str | None = None


class OverviewActionExecutionDto(BaseModel):
    summary: str
    target_page: str
    note_draft: NoteDraftDto | None = None
    created_task: TaskDto | None = None


class AppOverviewDto(BaseModel):
    open_task_count: int
    high_priority_open_count: int
    source_item_count: int
    pending_intake_count: int
    due_soon_source_count: int
    overdue_source_count: int
    notes_indexed_count: int
    has_daily_report: bool
    active_alerts: list[str]
    daily_brief: str
    focus_apps: list[str]
    recommended_next_actions: list[str]
    recommended_actions: list[OverviewActionDto] = Field(default_factory=list)
