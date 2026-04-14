from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDto(BaseModel):
    error: str
    message: str
    detail: str | None = None


class CapabilityDto(BaseModel):
    version: str
    api_version: str
    modules: list[str]
    adapters: list[str]
    features: list[str]


class SettingsHealthDto(BaseModel):
    status: str
    backend_url: str
    modules: list[str]
    work_review_root: str
    obsidian_vault_root: str | None = None
    adapter_states: dict[str, str] = Field(default_factory=dict)


class SettingsConfigDto(BaseModel):
    work_review_root: str
    obsidian_vault_root: str | None = None
    obsidian_generated_dir: str
    automation_check_in_hours: int = Field(ge=1, le=24)


class HostLifecycleDto(BaseModel):
    status: str  # "starting" | "running" | "stopping"
    version: str
    started_at: str | None = None  # ISO 8601
