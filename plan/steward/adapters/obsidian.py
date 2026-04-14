from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


@dataclass(slots=True)
class IndexedNote:
    title: str
    path: Path
    obsidian_url: str
    modified_at: float


@dataclass(slots=True)
class WrittenNote:
    path: Path
    obsidian_url: str


@dataclass(slots=True)
class NotesDashboardSnapshot:
    vault_ready: bool
    indexed_count: int
    generated_count: int
    recent_notes: list[IndexedNote]
    generated_notes: list[IndexedNote]


class ObsidianAdapter:
    def __init__(self, vault_root: Path, generated_dir: Path) -> None:
        self.vault_root = Path(vault_root)
        self.generated_dir = Path(generated_dir)

    @staticmethod
    def _slugify(title: str) -> str:
        return title.lower().replace(" ", "-")

    def _url_for(self, path: Path) -> str:
        return f"obsidian://open?path={quote(str(path.resolve()))}"

    def _note_title(self, note: Path) -> str:
        title = note.stem
        content = note.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return title

    def _index_paths(self, notes: list[Path]) -> list[IndexedNote]:
        indexed: list[IndexedNote] = []
        for note in notes:
            indexed.append(
                IndexedNote(
                    title=self._note_title(note),
                    path=note,
                    obsidian_url=self._url_for(note),
                    modified_at=note.stat().st_mtime,
                )
            )
        return indexed

    def _all_markdown_notes(self) -> list[Path]:
        if not self.vault_root.exists():
            return []
        return sorted(
            self.vault_root.rglob("*.md"),
            key=lambda note: note.stat().st_mtime,
            reverse=True,
        )

    def _is_generated_note(self, note: Path) -> bool:
        generated_root = self.vault_root / self.generated_dir
        try:
            note.relative_to(generated_root)
        except ValueError:
            return False
        return True

    def _generated_note_path(self, note_type: str, note_date: str, title: str) -> Path:
        target_dir = self.vault_root / self.generated_dir
        slug = self._slugify(title)
        return target_dir / f"{note_date}-{note_type}-{slug}.md"

    def availability(self) -> dict[str, str | None]:
        """Returns {"status": "available"|"degraded", "reason": str|None}"""
        if not self.vault_root.exists():
            return {"status": "degraded", "reason": f"Vault root not found: {self.vault_root}"}
        return {"status": "available", "reason": None}

    def index_notes(self, limit: int = 100) -> list[IndexedNote]:
        return self._index_paths(self._all_markdown_notes()[:limit])

    def dashboard(
        self,
        limit_recent: int = 12,
        limit_generated: int = 8,
    ) -> NotesDashboardSnapshot:
        notes = self._all_markdown_notes()
        generated_notes = [note for note in notes if self._is_generated_note(note)]
        return NotesDashboardSnapshot(
            vault_ready=self.vault_root.exists(),
            indexed_count=len(notes),
            generated_count=len(generated_notes),
            recent_notes=self._index_paths(notes[:limit_recent]),
            generated_notes=self._index_paths(generated_notes[:limit_generated]),
        )

    def write_generated_note(
        self,
        note_type: str,
        note_date: str,
        title: str,
        content: str,
    ) -> WrittenNote:
        target_dir = self.vault_root / self.generated_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        path = self._generated_note_path(note_type, note_date, title)
        path.write_text(content, encoding="utf-8")
        return WrittenNote(path=path, obsidian_url=self._url_for(path))

    def find_generated_note(
        self,
        note_type: str,
        note_date: str,
        title: str,
    ) -> WrittenNote | None:
        path = self._generated_note_path(note_type, note_date, title)
        if not path.exists():
            return None
        return WrittenNote(path=path, obsidian_url=self._url_for(path))
