from __future__ import annotations

from collections.abc import Callable

from plan.config import get_config
from plan.sources import load_sources
from plan.steward.contracts import SourceItemDto


class LazyZjuAdapter:
    def __init__(self, loader: Callable[[], list] | None = None) -> None:
        self._loader = loader or (lambda: load_sources(get_config()))

    def availability(self) -> dict[str, str | None]:
        """Returns {"status": "available"|"degraded", "reason": str|None}"""
        try:
            self._loader()
            return {"status": "available", "reason": None}
        except Exception as exc:
            return {"status": "degraded", "reason": str(exc)}

    def fetch_items(self) -> list[SourceItemDto]:
        items: list[SourceItemDto] = []
        for source in self._loader():
            if getattr(source, "name", "") != "lazy_zju":
                continue
            for entry in source.fetch():
                items.append(
                    SourceItemDto(
                        title=entry.title,
                        source=entry.source,
                        due=entry.due.isoformat() if entry.due else None,
                        project=entry.project,
                        priority=entry.priority,
                        external_id=entry.external_id,
                    )
                )
        return items

