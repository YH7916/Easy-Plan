"""Memory module: read/write profile.md and context.md."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from plan.config import resolve_path


def _path(key: str) -> Path:
    return resolve_path(key)


def read_profile() -> str:
    """Return full text of profile.md."""
    p = _path("profile")
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def write_profile(content: str) -> None:
    p = _path("profile")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_context() -> str:
    """Return full text of context.md."""
    p = _path("context")
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def write_context(content: str) -> None:
    """Overwrite context.md with new content."""
    p = _path("context")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def append_context(entry: str) -> None:
    """Append a timestamped entry to context.md."""
    existing = read_context()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    separator = "\n\n" if existing.strip() else ""
    updated = existing + separator + f"## {ts}\n\n{entry.strip()}"
    write_context(updated)
