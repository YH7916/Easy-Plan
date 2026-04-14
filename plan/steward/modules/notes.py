from __future__ import annotations

from plan.steward.adapters.obsidian import ObsidianAdapter
from plan.steward.contracts import NoteDraftDto, NoteIndexDto, NotesDashboardDto


class NotesService:
    def __init__(self, adapter: ObsidianAdapter | None) -> None:
        self.adapter = adapter

    def index(self, limit: int = 50) -> list[NoteIndexDto]:
        if self.adapter is None:
            return []
        return [NoteIndexDto.model_validate(note) for note in self.adapter.index_notes(limit=limit)]

    def dashboard(self, limit_recent: int = 12, limit_generated: int = 8) -> NotesDashboardDto:
        if self.adapter is None:
            return NotesDashboardDto(
                vault_ready=False,
                indexed_count=0,
                generated_count=0,
                recent_notes=[],
                generated_notes=[],
            )

        snapshot = self.adapter.dashboard(
            limit_recent=limit_recent,
            limit_generated=limit_generated,
        )
        return NotesDashboardDto(
            vault_ready=snapshot.vault_ready,
            indexed_count=snapshot.indexed_count,
            generated_count=snapshot.generated_count,
            recent_notes=[
                NoteIndexDto.model_validate(note)
                for note in snapshot.recent_notes
            ],
            generated_notes=[
                NoteIndexDto.model_validate(note)
                for note in snapshot.generated_notes
            ],
        )

    def write_daily_draft(self, date: str, title: str, content: str) -> NoteDraftDto:
        if self.adapter is None:
            raise RuntimeError("Obsidian vault is not configured.")
        note = self.adapter.write_generated_note(
            note_type="daily",
            note_date=date,
            title=title,
            content=content,
        )
        return NoteDraftDto.model_validate(note)

    def find_daily_draft(self, date: str, title: str) -> NoteDraftDto | None:
        if self.adapter is None:
            return None
        note = self.adapter.find_generated_note(
            note_type="daily",
            note_date=date,
            title=title,
        )
        if note is None:
            return None
        return NoteDraftDto.model_validate(note)
