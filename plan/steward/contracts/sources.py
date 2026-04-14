from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SourceItemDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    source: str
    due: str | None = None
    project: str | None = None
    priority: int = 0
    external_id: str | None = None


class SourceDashboardItemDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    source: str
    due: str | None = None
    project: str | None = None
    priority: int = 0
    external_id: str | None = None
    tracking_status: str
    urgency: str
    tracked_task_id: str | None = None
    tracked_task_status: str | None = None
    recommendation: str


class SourcesDashboardDto(BaseModel):
    total_count: int
    tracked_count: int
    pending_intake_count: int
    due_soon_count: int
    overdue_count: int
    items: list[SourceDashboardItemDto]


class AdapterAvailabilityDto(BaseModel):
    name: str
    status: str  # "available" | "degraded" | "not_configured"
    reason: str | None = None
