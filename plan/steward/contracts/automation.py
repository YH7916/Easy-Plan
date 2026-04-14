from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GuardrailsDto(BaseModel):
    auto_complete: bool = False
    delete_content: bool = False
    overwrite_user_notes: bool = False


class AutomationSignalDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    summary: str
    guardrails: GuardrailsDto = Field(default_factory=GuardrailsDto)


class InterventionRecordDto(BaseModel):
    timestamp: str  # ISO 8601
    signals: list[AutomationSignalDto]
    pending_count: int


class AutomationStatusDto(BaseModel):
    check_in_hours: int
    mode_summary: str
    pending_interventions_count: int
    guardrails: GuardrailsDto
    signals: list[AutomationSignalDto]
    last_run_at: str | None = None  # ISO 8601 timestamp of last recorded intervention
