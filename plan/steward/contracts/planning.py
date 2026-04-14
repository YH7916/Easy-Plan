from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TaskDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    project: str | None = None
    due: str | None = None
    priority: int = 0
    status: str
    source: str
    ticktick_id: str | None = None
    time_block: str | None = None


class TaskSuggestionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    source: str
    due: str | None = None
    project: str | None = None
    priority: int = 0
    external_id: str | None = None
    reason: str


class TimeBlockDto(BaseModel):
    start_time: str
    end_time: str
    task_id: str
    task_title: str
    estimated_minutes: int


class TaskStatusUpdateDto(BaseModel):
    status: str


class TodayQueueDto(BaseModel):
    date: str
    tasks: list[TaskDto]
    time_blocks: list[TimeBlockDto]
    total_estimated_minutes: int
