"""Source plugin interface: BaseSource ABC, SourceItem dataclass, registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plan.tasks import Task


@dataclass
class SourceItem:
    title: str
    source: str
    due: date | None = None
    project: str | None = None
    priority: int = 0          # 0=none, 1=low, 2=medium, 3=high
    external_id: str | None = None
    raw: dict = field(default_factory=dict)

    def to_task_dict(self) -> dict:
        """Convert to a dict suitable for upsert_from_source."""
        return {
            "title": self.title,
            "due": self.due.isoformat() if self.due else None,
            "project": self.project,
            "priority": self.priority,
            "source": self.source,
            "external_id": self.external_id,
        }


class BaseSource(ABC):
    """Abstract base for all data sources."""

    name: str = ""
    enabled: bool = False

    @abstractmethod
    def fetch(self) -> list[SourceItem]:
        """Pull items from the external source."""
        ...

    def push(self, tasks: list[dict]) -> None:
        """Push local tasks back to the source (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support push")

    @property
    def is_writable(self) -> bool:
        return False


# ── Registry ────────────────────────────────────────────────────────────────

_registry: dict[str, type[BaseSource]] = {}


def register(cls: type[BaseSource]) -> type[BaseSource]:
    """Class decorator to register a source by its name."""
    _registry[cls.name] = cls
    return cls


def load_sources(config: dict) -> list[BaseSource]:
    """Instantiate all enabled sources from config['sources']."""
    from plan.sources.shell import ShellSource  # noqa: F401 — triggers registration

    sources_cfg = config.get("sources", {})
    result: list[BaseSource] = []

    for name, cfg in sources_cfg.items():
        if not cfg.get("enabled", False):
            continue
        if name in _registry:
            instance = _registry[name](cfg)
            result.append(instance)
        elif cfg.get("cli_command"):
            # Generic shell source
            instance = ShellSource(name=name, config=cfg)
            result.append(instance)

    return result
