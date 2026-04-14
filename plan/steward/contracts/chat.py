from __future__ import annotations

from pydantic import BaseModel, Field

from plan.steward.contracts.planning import TaskDto
from plan.steward.contracts.notes import NoteDraftDto


class ChatMessageDto(BaseModel):
    role: str
    content: str


class ChatActionDto(BaseModel):
    id: str
    label: str
    description: str
    target_module: str


class ChatSessionDto(BaseModel):
    session_id: str
    reply: str
    starter_prompts: list[str] = Field(default_factory=list)
    suggested_actions: list[ChatActionDto] = Field(default_factory=list)
    history: list[ChatMessageDto]


class ChatActionExecutionDto(BaseModel):
    summary: str
    session: ChatSessionDto
    created_task: TaskDto | None = None
    note_draft: NoteDraftDto | None = None
