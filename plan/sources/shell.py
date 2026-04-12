"""ShellSource: runs a CLI command and parses JSON output into SourceItems."""
from __future__ import annotations

import json
import subprocess
from datetime import date

from plan.sources import BaseSource, SourceItem


class ShellSource(BaseSource):
    """Generic source that calls an external CLI and parses its JSON output.

    The CLI must output a JSON array of objects with at least a "title" field.
    Optional fields: due (ISO date string), priority (0-3), project, external_id.
    """

    @property
    def is_writable(self) -> bool:
        return self._writable

    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.enabled = config.get("enabled", False)
        self._command: str = config["cli_command"]
        self._writable: bool = config.get("writable", False)

    def fetch(self) -> list[SourceItem]:
        try:
            raw = subprocess.check_output(
                self._command,
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"ShellSource {self.name!r} command failed (exit {exc.returncode}): "
                f"{self._command}"
            ) from exc
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"ShellSource {self.name!r} timed out after 30s: {self._command}"
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"ShellSource {self.name!r} returned non-JSON output: {raw[:200]!r}"
            ) from exc

        if not isinstance(data, list):
            raise ValueError(
                f"ShellSource {self.name!r} must return a JSON array, got {type(data).__name__}"
            )

        return [self._parse_item(item) for item in data]

    def _parse_item(self, item: dict) -> SourceItem:
        due_raw = item.get("due")
        due: date | None = None
        if due_raw:
            try:
                due = date.fromisoformat(str(due_raw)[:10])
            except ValueError:
                due = None

        return SourceItem(
            title=item["title"],
            source=self.name,
            due=due,
            project=item.get("project"),
            priority=int(item.get("priority", 0)),
            external_id=item.get("external_id"),
            raw=item,
        )
