"""LazyZJUSource: fetches assignments and rollcalls from 学在浙大 via lazy CLI."""
from __future__ import annotations

import re
import subprocess
from datetime import date

from plan.sources import BaseSource, SourceItem, register


def _run(cmd: str) -> str:
    """Run a lazy CLI command and return decoded output (GBK on Windows)."""
    raw = subprocess.check_output(
        cmd,
        shell=True,
        stderr=subprocess.DEVNULL,
        timeout=60,
    )
    try:
        return raw.decode("gbk")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _parse_assignments(text: str) -> list[SourceItem]:
    """Parse `lazy assignment todo -A` text output into SourceItems."""
    items: list[SourceItem] = []

    # Each block is separated by +---...---+
    # Extract blocks between the box borders
    blocks = re.split(r"\+[-]+\+", text)

    for block in blocks:
        lines = [l.strip().strip("|").strip() for l in block.splitlines() if l.strip().strip("|").strip()]
        if not lines:
            continue

        title = None
        course = None
        due: date | None = None
        ext_id: str | None = None

        for line in lines:
            # Title line: "Lab2（实验代码） [ID: 1122204]"
            m = re.match(r"^(.+?)\s+\[ID:\s*(\d+)\]$", line)
            if m:
                title = m.group(1).strip()
                ext_id = m.group(2)
                continue

            # Due line: "截止时间: 2026-04-17 14:19:00 ..."
            m = re.search(r"截止时间[：:]\s*(\d{4}-\d{2}-\d{2})", line)
            if m:
                try:
                    due = date.fromisoformat(m.group(1))
                except ValueError:
                    pass
                continue

            # Course line: just a name + course_id, e.g. "数据结构 95869"
            m = re.match(r"^(.+?)\s+(\d{4,6})$", line)
            if m and title is None:
                # This appears before title in some blocks — skip
                pass
            elif m and course is None and title is not None:
                course = m.group(1).strip()

        if title and ext_id:
            # Compute priority based on urgency
            priority = 0
            if due:
                days_left = (due - date.today()).days
                if days_left <= 1:
                    priority = 3
                elif days_left <= 3:
                    priority = 2
                elif days_left <= 7:
                    priority = 1

            items.append(SourceItem(
                title=title,
                source="lazy_zju",
                due=due,
                project="courses",
                priority=priority,
                external_id=f"assignment_{ext_id}",
                raw={"course": course, "assignment_id": ext_id},
            ))

    return items



@register
class LazyZJUSource(BaseSource):
    """Fetches assignments and rollcalls from 学在浙大 via the lazy CLI."""

    name = "lazy_zju"

    def __init__(self, config: dict) -> None:
        self.enabled = config.get("enabled", False)
        self._fetch_assignments: bool = config.get("assignments", True)

    @property
    def is_writable(self) -> bool:
        return False

    def fetch(self) -> list[SourceItem]:
        items: list[SourceItem] = []

        if self._fetch_assignments:
            try:
                text = _run("lazy assignment todo -A")
                items.extend(_parse_assignments(text))
            except Exception as exc:
                raise RuntimeError(f"lazy assignment todo failed: {exc}") from exc

        return items
