from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class NoteIndexDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    path: Path
    obsidian_url: str
    modified_at: float


class NoteDraftDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path: Path
    obsidian_url: str


class NotesDashboardDto(BaseModel):
    vault_ready: bool
    indexed_count: int
    generated_count: int
    recent_notes: list[NoteIndexDto]
    generated_notes: list[NoteIndexDto]
