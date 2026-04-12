# Plan Agent CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI planning agent that uses Claude API to analyze personal context and generate daily time-blocked plans, with optional TickTick sync and pluggable data sources.

**Architecture:** Single Python package installed via `pip install -e .`. Memory stored as markdown files. Tasks stored as JSON. All external integrations are optional source plugins implementing BaseSource ABC.

**Tech Stack:** Python 3.11+, click, anthropic, ticktick-py (optional), tomllib, python-dotenv, pytest

---

### Task 1: Project Scaffold

**Files:**
- `D:/Plan/pyproject.toml` (create)
- `D:/Plan/config.toml` (create)
- `D:/Plan/.env.example` (create)
- `D:/Plan/plan/__init__.py` (create)
- `D:/Plan/plan/cli.py` (create stub)
- `D:/Plan/data/profile.md` (create)
- `D:/Plan/data/context.md` (create)
- `D:/Plan/data/tasks.json` (create)
- `D:/Plan/plan/prompts/analyze.txt` (create stub)
- `D:/Plan/plan/sources/__init__.py` (create stub)

- [ ] Create directory structure:
```bash
mkdir -p D:/Plan/plan/prompts D:/Plan/plan/sources D:/Plan/data D:/Plan/tests
```

- [ ] Create `D:/Plan/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "plan"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "anthropic>=0.25",
    "python-dotenv>=1.0",
    "tomli-w>=1.0",
]

[project.optional-dependencies]
ticktick = ["ticktick-py>=0.3"]
dev = ["pytest>=8", "pytest-mock>=3.12"]

[project.scripts]
plan = "plan.cli:cli"

[tool.setuptools.packages.find]
where = ["."]
include = ["plan*"]
```

- [ ] Create `D:/Plan/config.toml`:
```toml
[ai]
provider = "claude"
model = "claude-sonnet-4-6"
api_key_env = "ANTHROPIC_API_KEY"

[schedule]
daily_time = "08:00"
enabled = true
run_on_missed = true

[sources.ticktick]
enabled = false
writable = true
username = ""
password_env = "TICKTICK_PASSWORD"

[sources.school]
enabled = false
cli_command = "zlb homework list --json"
writable = false

[paths]
profile = "data/profile.md"
context = "data/context.md"
tasks = "data/tasks.json"

[projects]
areas = []
```

- [ ] Create `D:/Plan/.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...
TICKTICK_PASSWORD=
```

- [ ] Create `D:/Plan/plan/__init__.py`:
```python
"""plan - AI-powered personal planning agent."""
__version__ = "0.1.0"
```

- [ ] Create `D:/Plan/plan/cli.py` (stub - full implementation in Tasks 9-11):
```python
"""CLI entry point."""
import click

@click.group()
def cli():
    """AI-powered personal planning agent."""

if __name__ == "__main__":
    cli()
```

- [ ] Create `D:/Plan/data/tasks.json`:
```json
[]
```

- [ ] Create `D:/Plan/data/context.md`:
```markdown
# Daily Context

_No context yet. Run `plan chat` to add context._
```

- [ ] Create `D:/Plan/plan/sources/__init__.py` (stub):
```python
"""Source plugin interface."""
```

- [ ] Create `D:/Plan/plan/prompts/analyze.txt` (stub):
```
# Analyze prompt - see Task 8
```

- [ ] Install in editable mode and verify entry point works:
```bash
cd D:/Plan && pip install -e .
plan --help
```
Expected output:
```
Usage: plan [OPTIONS] COMMAND [ARGS]...

  AI-powered personal planning agent.

Options:
  --help  Show this message and exit.
```

- [ ] Commit:
```bash
cd D:/Plan && git init && git add pyproject.toml config.toml .env.example plan/ data/ && git commit -m "chore: project scaffold"
```

---

### Task 2: Config Loader

**Files:**
- `D:/Plan/plan/config.py` (create)
- `D:/Plan/tests/test_config.py` (create)

- [ ] Create `D:/Plan/plan/config.py`:
```python
"""Config loader: reads config.toml + .env, supports get/set/save."""
from __future__ import annotations

import os
import tomllib
import tomli_w
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config.toml"


def _load_raw() -> dict:
    load_dotenv(_ROOT / ".env")
    with open(_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


_cache: dict | None = None


def get_config(reload: bool = False) -> dict:
    global _cache
    if _cache is None or reload:
        _cache = _load_raw()
    return _cache


def get(key: str, default: Any = None) -> Any:
    """Dot-separated key lookup, e.g. get('ai.model')."""
    cfg = get_config()
    parts = key.split(".")
    node: Any = cfg
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_key(key: str, value: Any) -> None:
    """Set a dot-separated key and persist to config.toml."""
    cfg = get_config()
    parts = key.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    _save(cfg)


def _save(cfg: dict) -> None:
    with open(_CONFIG_PATH, "wb") as f:
        tomli_w.dump(cfg, f)


def resolve_path(key: str) -> Path:
    """Resolve a paths.* config key relative to project root."""
    rel = get(f"paths.{key}")
    if rel is None:
        raise KeyError(f"paths.{key} not found in config")
    return _ROOT / rel


def api_key() -> str:
    """Return the Anthropic API key from env."""
    env_var = get("ai.api_key_env", "ANTHROPIC_API_KEY")
    key = os.environ.get(env_var, "")
    if not key:
        raise EnvironmentError(
            f"Environment variable {env_var} is not set. "
            "Add it to .env or export it in your shell."
        )
    return key
```

- [ ] Create `D:/Plan/tests/test_config.py`:
```python
import pytest
from pathlib import Path
import tomllib, tomli_w

CONFIG_PATH = Path("D:/Plan/config.toml")


def test_get_ai_model(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    assert cfg.get("ai.model") == "claude-sonnet-4-6"


def test_get_missing_key(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    assert cfg.get("nonexistent.key", "fallback") == "fallback"


def test_set_and_restore(monkeypatch):
    """set_key writes to config.toml and the value is readable back."""
    monkeypatch.chdir("D:/Plan")
    backup = CONFIG_PATH.read_bytes()
    import plan.config as cfg
    cfg._cache = None
    try:
        cfg.set_key("projects.areas", ["work", "study"])
        cfg._cache = None
        assert cfg.get("projects.areas") == ["work", "study"]
    finally:
        CONFIG_PATH.write_bytes(backup)
        cfg._cache = None


def test_resolve_path(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    p = cfg.resolve_path("tasks")
    assert p.name == "tasks.json"


def test_api_key_missing(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        cfg.api_key()
```

- [ ] Run tests:
```bash
cd D:/Plan && pip install tomli-w && pytest tests/test_config.py -v
```
Expected:
```
tests/test_config.py::test_get_ai_model PASSED
tests/test_config.py::test_get_missing_key PASSED
tests/test_config.py::test_set_and_restore PASSED
tests/test_config.py::test_resolve_path PASSED
tests/test_config.py::test_api_key_missing PASSED
5 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/config.py tests/test_config.py pyproject.toml && git commit -m "feat: config loader with get/set/save and env resolution"
```

---

### Task 3: Memory Module

**Files:**
- `D:/Plan/plan/memory.py` (create)
- `D:/Plan/tests/test_memory.py` (create)

- [ ] Create `D:/Plan/plan/memory.py`:
```python
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
```

- [ ] Create `D:/Plan/tests/test_memory.py`:
```python
import pytest


@pytest.fixture(autouse=True)
def patch_paths(monkeypatch, tmp_path):
    """Redirect profile/context paths to tmp_path."""
    import plan.config as cfg
    cfg._cache = None
    profile_file = tmp_path / "profile.md"
    context_file = tmp_path / "context.md"
    original_resolve = cfg.resolve_path

    def fake_resolve(key):
        if key == "profile":
            return profile_file
        if key == "context":
            return context_file
        return original_resolve(key)

    monkeypatch.setattr(cfg, "resolve_path", fake_resolve)
    yield


def test_read_profile_missing():
    from plan.memory import read_profile
    assert read_profile() == ""


def test_write_and_read_profile():
    from plan.memory import write_profile, read_profile
    write_profile("# My Profile\n\nI am a CS student.")
    assert "CS student" in read_profile()


def test_read_context_missing():
    from plan.memory import read_context
    assert read_context() == ""


def test_write_and_read_context():
    from plan.memory import write_context, read_context
    write_context("# Daily Context\n\nFeel focused today.")
    assert "focused" in read_context()


def test_append_context_creates_timestamped_entry():
    from plan.memory import append_context, read_context, write_context
    write_context("")
    append_context("Finished ML homework.")
    result = read_context()
    assert "Finished ML homework." in result
    import re
    assert re.search(r"## \d{4}-\d{2}-\d{2}", result)


def test_append_context_accumulates():
    from plan.memory import append_context, read_context, write_context
    write_context("")
    append_context("Entry one.")
    append_context("Entry two.")
    result = read_context()
    assert "Entry one." in result
    assert "Entry two." in result
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_memory.py -v
```
Expected:
```
tests/test_memory.py::test_read_profile_missing PASSED
tests/test_memory.py::test_write_and_read_profile PASSED
tests/test_memory.py::test_read_context_missing PASSED
tests/test_memory.py::test_write_and_read_context PASSED
tests/test_memory.py::test_append_context_creates_timestamped_entry PASSED
tests/test_memory.py::test_append_context_accumulates PASSED
6 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/memory.py tests/test_memory.py && git commit -m "feat: memory module for profile and context markdown files"
```

---

### Task 4: Task Store

**Files:**
- `D:/Plan/plan/tasks.py` (create)
- `D:/Plan/tests/test_tasks.py` (create)

- [ ] Create `D:/Plan/plan/tasks.py`:
```python
"""Task store: load/save tasks.json, CRUD operations."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import TypedDict

from plan.config import resolve_path


class Task(TypedDict, total=False):
    id: str
    title: str
    project: str | None
    due: str | None
    priority: int
    status: str
    source: str
    ticktick_id: str | None
    time_block: str | None


def _path() -> Path:
    return resolve_path("tasks")


def load_tasks() -> list[Task]:
    p = _path()
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_tasks(tasks: list[Task]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def add_task(
    title: str,
    project: str | None = None,
    due: str | None = None,
    priority: int = 0,
    source: str = "local",
) -> Task:
    task: Task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "project": project,
        "due": due,
        "priority": priority,
        "status": "open",
        "source": source,
        "ticktick_id": None,
        "time_block": None,
    }
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return task


def list_tasks(status: str | None = None, project: str | None = None) -> list[Task]:
    tasks = load_tasks()
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if project:
        tasks = [t for t in tasks if t.get("project") == project]
    return tasks


def mark_done(task_id: str) -> Task | None:
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "done"
            save_tasks(tasks)
            return task
    return None


def update_task(task_id: str, **kwargs) -> Task | None:
    """Update arbitrary fields on a task by id."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task.update(kwargs)
            save_tasks(tasks)
            return task
    return None


def upsert_from_source(items: list[dict]) -> None:
    """Merge source items into tasks.json by external_id, adding new ones."""
    tasks = load_tasks()
    existing_ext_ids = {t.get("ticktick_id") for t in tasks if t.get("ticktick_id")}
    for item in items:
        ext_id = item.get("external_id")
        if ext_id and ext_id in existing_ext_ids:
            for task in tasks:
                if task.get("ticktick_id") == ext_id:
                    task["title"] = item.get("title", task["title"])
                    task["due"] = item.get("due")
                    task["priority"] = item.get("priority", 0)
        else:
            tasks.append({
                "id": str(uuid.uuid4()),
                "title": item["title"],
                "project": item.get("project"),
                "due": item.get("due"),
                "priority": item.get("priority", 0),
                "status": "open",
                "source": item.get("source", "unknown"),
                "ticktick_id": ext_id,
                "time_block": None,
            })
    save_tasks(tasks)
```

- [ ] Create `D:/Plan/tests/test_tasks.py`:
```python
import pytest


@pytest.fixture(autouse=True)
def patch_tasks_path(monkeypatch, tmp_path):
    tasks_file = tmp_path / "tasks.json"
    import plan.config as cfg
    original_resolve = cfg.resolve_path

    def fake_resolve(key):
        if key == "tasks":
            return tasks_file
        return original_resolve(key)

    monkeypatch.setattr(cfg, "resolve_path", fake_resolve)
    yield tasks_file


def test_load_tasks_empty():
    from plan.tasks import load_tasks
    assert load_tasks() == []


def test_add_task_creates_entry():
    from plan.tasks import add_task, load_tasks
    t = add_task("Write report", project="work", priority=2)
    tasks = load_tasks()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Write report"
    assert tasks[0]["status"] == "open"
    assert len(tasks[0]["id"]) == 36


def test_list_tasks_filter_status():
    from plan.tasks import add_task, list_tasks, mark_done
    t1 = add_task("Task A")
    t2 = add_task("Task B")
    mark_done(t1["id"])
    open_tasks = list_tasks(status="open")
    assert len(open_tasks) == 1
    assert open_tasks[0]["title"] == "Task B"


def test_mark_done():
    from plan.tasks import add_task, mark_done, load_tasks
    t = add_task("Finish homework")
    result = mark_done(t["id"])
    assert result["status"] == "done"
    assert load_tasks()[0]["status"] == "done"


def test_mark_done_nonexistent():
    from plan.tasks import mark_done
    assert mark_done("nonexistent-id") is None


def test_update_task_time_block():
    from plan.tasks import add_task, update_task, load_tasks
    t = add_task("Study ML")
    update_task(t["id"], time_block="09:00-10:30")
    assert load_tasks()[0]["time_block"] == "09:00-10:30"


def test_upsert_from_source_adds_new():
    from plan.tasks import upsert_from_source, load_tasks
    upsert_from_source([{
        "title": "External task", "due": "2026-04-15", "priority": 1,
        "source": "ticktick", "external_id": "tt-001", "project": "school",
    }])
    tasks = load_tasks()
    assert len(tasks) == 1
    assert tasks[0]["ticktick_id"] == "tt-001"


def test_upsert_from_source_updates_existing():
    from plan.tasks import upsert_from_source, load_tasks
    item = {"title": "Old title", "due": None, "priority": 0,
            "source": "ticktick", "external_id": "tt-002", "project": None}
    upsert_from_source([item])
    item["title"] = "New title"
    upsert_from_source([item])
    tasks = load_tasks()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "New title"
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_tasks.py -v
```
Expected:
```
tests/test_tasks.py::test_load_tasks_empty PASSED
tests/test_tasks.py::test_add_task_creates_entry PASSED
tests/test_tasks.py::test_list_tasks_filter_status PASSED
tests/test_tasks.py::test_mark_done PASSED
tests/test_tasks.py::test_mark_done_nonexistent PASSED
tests/test_tasks.py::test_update_task_time_block PASSED
tests/test_tasks.py::test_upsert_from_source_adds_new PASSED
tests/test_tasks.py::test_upsert_from_source_updates_existing PASSED
8 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/tasks.py tests/test_tasks.py && git commit -m "feat: task store with CRUD and source upsert"
```

---

### Task 5: Source Plugin Interface

**Files:**
- `D:/Plan/plan/sources/__init__.py` (implement)
- `D:/Plan/tests/test_sources.py` (create)

- [ ] Implement `D:/Plan/plan/sources/__init__.py`:
```python
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
```

- [ ] Create `D:/Plan/tests/test_sources.py`:
```python
import pytest
from dataclasses import asdict
from datetime import date
from plan.sources import SourceItem, BaseSource, register, load_sources


def test_source_item_to_task_dict():
    item = SourceItem(
        title="Do homework",
        source="school",
        due=date(2026, 4, 15),
        project="CS101",
        priority=2,
        external_id="hw-42",
    )
    d = item.to_task_dict()
    assert d["title"] == "Do homework"
    assert d["due"] == "2026-04-15"
    assert d["priority"] == 2
    assert d["external_id"] == "hw-42"


def test_source_item_no_due():
    item = SourceItem(title="Someday task", source="local")
    assert item.to_task_dict()["due"] is None


def test_base_source_push_raises():
    class DummySource(BaseSource):
        name = "dummy"
        def fetch(self):
            return []

    src = DummySource()
    with pytest.raises(NotImplementedError):
        src.push([])


def test_base_source_not_writable():
    class DummySource(BaseSource):
        name = "dummy2"
        def fetch(self):
            return []

    assert DummySource().is_writable is False


def test_register_decorator():
    @register
    class MySrc(BaseSource):
        name = "mysrc"
        def fetch(self):
            return []

    from plan.sources import _registry
    assert "mysrc" in _registry


def test_load_sources_skips_disabled():
    cfg = {"sources": {"school": {"enabled": False, "cli_command": "echo []"}}}
    sources = load_sources(cfg)
    assert sources == []


def test_load_sources_shell_source(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *a, **kw: b'[{"title":"hw1","due":null,"priority":0,"project":null,"external_id":"s1"}]')
    cfg = {"sources": {"school": {"enabled": True, "cli_command": "echo []", "writable": False}}}
    sources = load_sources(cfg)
    assert len(sources) == 1
    items = sources[0].fetch()
    assert items[0].title == "hw1"
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_sources.py -v
```
Expected:
```
tests/test_sources.py::test_source_item_to_task_dict PASSED
tests/test_sources.py::test_source_item_no_due PASSED
tests/test_sources.py::test_base_source_push_raises PASSED
tests/test_sources.py::test_base_source_not_writable PASSED
tests/test_sources.py::test_register_decorator PASSED
tests/test_sources.py::test_load_sources_skips_disabled PASSED
tests/test_sources.py::test_load_sources_shell_source PASSED
7 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/sources/__init__.py tests/test_sources.py && git commit -m "feat: BaseSource ABC, SourceItem dataclass, source registry"
```

---

### Task 6: ShellSource Adapter

**Files:**
- `D:/Plan/plan/sources/shell.py` (create)

- [ ] Create `D:/Plan/plan/sources/shell.py`:
```python
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

    Example config.toml entry:
        [sources.school]
        enabled = true
        cli_command = "zlb homework list --json"
        writable = false
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
```

- [ ] Add ShellSource tests to `D:/Plan/tests/test_sources.py` (append):
```python
# --- ShellSource tests (add to test_sources.py) ---

def test_shell_source_fetch_parses_json(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    payload = json.dumps([
        {"title": "Lab report", "due": "2026-04-20", "priority": 2,
         "project": "CS101", "external_id": "lab-1"},
    ]).encode()
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: payload)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    items = src.fetch()
    assert len(items) == 1
    assert items[0].title == "Lab report"
    assert items[0].due == date(2026, 4, 20)
    assert items[0].priority == 2
    assert items[0].external_id == "lab-1"


def test_shell_source_fetch_handles_null_due(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    payload = json.dumps([{"title": "No due", "due": None}]).encode()
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: payload)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    items = src.fetch()
    assert items[0].due is None


def test_shell_source_raises_on_bad_json(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"not json")
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(ValueError, match="non-JSON"):
        src.fetch()


def test_shell_source_raises_on_non_array(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b'{"key": "val"}')
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(ValueError, match="JSON array"):
        src.fetch()


def test_shell_source_raises_on_command_failure(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    def fail(*a, **kw):
        raise subprocess.CalledProcessError(1, "fake")
    monkeypatch.setattr(subprocess, "check_output", fail)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(RuntimeError, match="command failed"):
        src.fetch()
```

- [ ] Run all source tests:
```bash
cd D:/Plan && pytest tests/test_sources.py -v
```
Expected: 12 passed

- [ ] Commit:
```bash
cd D:/Plan && git add plan/sources/shell.py tests/test_sources.py && git commit -m "feat: ShellSource adapter for CLI-based data sources"
```

---

### Task 7: Agent Core

**Files:**
- `D:/Plan/plan/agent.py` (create)
- `D:/Plan/tests/test_agent.py` (create)

- [ ] Create `D:/Plan/plan/agent.py`:
```python
"""Agent core: build prompt, call Claude, parse response."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import anthropic

from plan import __version__
from plan.config import get, api_key
from plan.memory import read_profile, read_context, write_context
from plan.tasks import load_tasks, save_tasks, Task

_PROMPT_PATH = Path(__file__).parent / "prompts" / "analyze.txt"


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_prompt(
    profile: str,
    context: str,
    tasks: list[Task],
    extra_items: list[dict] | None = None,
) -> str:
    """Render the analyze prompt with current data."""
    template = _load_prompt_template()
    tasks_json = json.dumps(tasks, indent=2, ensure_ascii=False)
    extra_json = json.dumps(extra_items or [], indent=2, ensure_ascii=False)
    return (
        template
        .replace("{{PROFILE}}", profile)
        .replace("{{CONTEXT}}", context)
        .replace("{{TASKS_JSON}}", tasks_json)
        .replace("{{EXTRA_ITEMS_JSON}}", extra_json)
    )


def call_claude(prompt: str) -> str:
    """Send prompt to Claude and return the raw text response."""
    client = anthropic.Anthropic(api_key=api_key())
    model = get("ai.model", "claude-sonnet-4-6")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_response(response: str) -> tuple[str, list[Task]]:
    """Extract updated context and time-blocked tasks from Claude response.

    Expected response format:
        <context>
        ...updated context.md content...
        </context>

        <tasks>
        [{"id": "...", "time_block": "09:00-10:30", ...}, ...]
        </tasks>

    Returns:
        (new_context_text, list_of_task_dicts_with_time_block)
    """
    context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)
    tasks_match = re.search(r"<tasks>(.*?)</tasks>", response, re.DOTALL)

    new_context = context_match.group(1).strip() if context_match else ""

    tasks: list[Task] = []
    if tasks_match:
        try:
            tasks = json.loads(tasks_match.group(1).strip())
        except json.JSONDecodeError:
            tasks = []

    return new_context, tasks


def run_analyze(extra_items: list[dict] | None = None) -> list[Task]:
    """Full analyze cycle: read data, call Claude, write results back.

    Returns the updated task list with time_block fields set.
    """
    profile = read_profile()
    context = read_context()
    tasks = load_tasks()

    prompt = build_prompt(profile, context, tasks, extra_items)
    response = call_claude(prompt)
    new_context, updated_tasks = parse_response(response)

    if new_context:
        write_context(new_context)

    # Merge time_block values back into the main task list
    time_blocks: dict[str, str] = {
        t["id"]: t.get("time_block", "")
        for t in updated_tasks
        if t.get("id") and t.get("time_block")
    }
    for task in tasks:
        if task["id"] in time_blocks:
            task["time_block"] = time_blocks[task["id"]]

    save_tasks(tasks)
    return tasks


def chat_turn(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """Single chat turn: append user message, call Claude, return reply + updated history.

    history is a list of {"role": "user"|"assistant", "content": str} dicts.
    """
    client = anthropic.Anthropic(api_key=api_key())
    model = get("ai.model", "claude-sonnet-4-6")

    system = (
        "You are a personal planning assistant. "
        "Help the user reflect on their goals, tasks, and schedule. "
        "Be concise and actionable. "
        f"Current profile:\n{read_profile()}\n\nCurrent context:\n{read_context()}"
    )

    history = history + [{"role": "user", "content": user_message}]
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=history,
    )
    reply = message.content[0].text
    history = history + [{"role": "assistant", "content": reply}]
    return reply, history
```

- [ ] Create `D:/Plan/tests/test_agent.py`:
```python
"""Tests for plan.agent — all Claude calls are mocked."""
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


@pytest.fixture(autouse=True)
def patch_data_paths(monkeypatch, tmp_path):
    import plan.config as cfg
    cfg._cache = None
    profile_file = tmp_path / "profile.md"
    context_file = tmp_path / "context.md"
    tasks_file = tmp_path / "tasks.json"
    profile_file.write_text("# Profile\nCS student.", encoding="utf-8")
    context_file.write_text("# Context\nFeel good.", encoding="utf-8")
    tasks_file.write_text("[]", encoding="utf-8")

    original = cfg.resolve_path
    def fake(key):
        return {"profile": profile_file, "context": context_file, "tasks": tasks_file}.get(key, original(key))
    monkeypatch.setattr(cfg, "resolve_path", fake)
    yield


def test_build_prompt_contains_profile_and_tasks(tmp_path):
    from plan.agent import build_prompt
    # patch prompt template
    prompt_path = Path("D:/Plan/plan/prompts/analyze.txt")
    original = prompt_path.read_text(encoding="utf-8")
    try:
        prompt_path.write_text(
            "PROFILE:\n{{PROFILE}}\nCONTEXT:\n{{CONTEXT}}\nTASKS:\n{{TASKS_JSON}}\nEXTRA:\n{{EXTRA_ITEMS_JSON}}",
            encoding="utf-8"
        )
        result = build_prompt("My profile", "My context", [{"id": "1", "title": "Study"}])
        assert "My profile" in result
        assert "My context" in result
        assert "Study" in result
    finally:
        prompt_path.write_text(original, encoding="utf-8")


def test_parse_response_extracts_context_and_tasks():
    from plan.agent import parse_response
    response = """
<context>
# Updated Context
Feeling productive.
</context>

<tasks>
[{"id": "abc", "title": "Study ML", "time_block": "09:00-10:30"}]
</tasks>
"""
    ctx, tasks = parse_response(response)
    assert "Feeling productive" in ctx
    assert len(tasks) == 1
    assert tasks[0]["time_block"] == "09:00-10:30"


def test_parse_response_missing_sections():
    from plan.agent import parse_response
    ctx, tasks = parse_response("No structured output here.")
    assert ctx == ""
    assert tasks == []


def test_parse_response_bad_tasks_json():
    from plan.agent import parse_response
    response = "<context>ctx</context><tasks>not json</tasks>"
    ctx, tasks = parse_response(response)
    assert ctx == "ctx"
    assert tasks == []


def test_run_analyze_updates_time_blocks(monkeypatch):
    from plan.tasks import add_task, load_tasks
    t = add_task("Study ML")
    task_id = t["id"]

    mock_response = f"""
<context>
# Updated Context
Analyzed today.
</context>
<tasks>
[{{"id": "{task_id}", "title": "Study ML", "time_block": "09:00-10:30"}}]
</tasks>
"""
    with patch("plan.agent.call_claude", return_value=mock_response):
        from plan.agent import run_analyze
        tasks = run_analyze()

    assert tasks[0]["time_block"] == "09:00-10:30"

    from plan.memory import read_context
    assert "Analyzed today" in read_context()


def test_chat_turn_returns_reply(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Here is your plan.")]
    )
    with patch("plan.agent.anthropic.Anthropic", return_value=mock_client):
        with patch("plan.agent.api_key", return_value="fake-key"):
            from plan.agent import chat_turn
            reply, history = chat_turn("What should I do today?", [])

    assert reply == "Here is your plan."
    assert history[-1]["role"] == "assistant"
    assert history[-2]["role"] == "user"
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_agent.py -v
```
Expected:
```
tests/test_agent.py::test_build_prompt_contains_profile_and_tasks PASSED
tests/test_agent.py::test_parse_response_extracts_context_and_tasks PASSED
tests/test_agent.py::test_parse_response_missing_sections PASSED
tests/test_agent.py::test_parse_response_bad_tasks_json PASSED
tests/test_agent.py::test_run_analyze_updates_time_blocks PASSED
tests/test_agent.py::test_chat_turn_returns_reply PASSED
6 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/agent.py tests/test_agent.py && git commit -m "feat: agent core with build_prompt, call_claude, parse_response"
```

---

### Task 8: Analyze Prompt Template

**Files:**
- `D:/Plan/plan/prompts/analyze.txt` (implement)

- [ ] Write `D:/Plan/plan/prompts/analyze.txt`:
```
You are a personal planning assistant for a busy university student and early-career engineer.

## Your inputs

### User Profile
{{PROFILE}}

### Recent Context & Notes
{{CONTEXT}}

### Current Tasks (JSON)
{{TASKS_JSON}}

### Additional Items from External Sources (JSON)
{{EXTRA_ITEMS_JSON}}

## Your job

1. Read all inputs carefully.
2. Assign a realistic time block to every open task, fitting them into a single workday (08:00-22:00).
   - Respect due dates: overdue or due-today tasks get morning slots.
   - Respect priority: priority 3 (high) before priority 2 (medium) before priority 1 (low).
   - Leave at least 30-minute breaks between blocks.
   - Do not schedule more than 8 hours of focused work total.
   - If there are more tasks than time, leave lower-priority tasks without a time_block.
3. Write a brief updated context summary (2-4 sentences) reflecting today's plan and any important notes.

## Output format

Respond with EXACTLY this structure — no extra text before or after:

<context>
[Updated context.md content — plain markdown, 2-4 sentences summarizing today's focus and any key notes]
</context>

<tasks>
[JSON array — include ALL tasks (open and done). For open tasks, add or update the "time_block" field (e.g. "09:00-10:30"). For done tasks, keep time_block as null. Preserve all other fields exactly.]
</tasks>
```

- [ ] Verify the template renders correctly with a quick smoke test:
```bash
cd D:/Plan && python3 -c "
from plan.agent import build_prompt
p = build_prompt('# Profile', '# Context', [])
print(p[:200])
"
```
Expected: first 200 chars of the rendered prompt (shows profile/context/tasks sections).

- [ ] Commit:
```bash
cd D:/Plan && git add plan/prompts/analyze.txt && git commit -m "feat: analyze prompt template for daily time-block planning"
```

---

### Task 9: CLI Commands — Core (chat, analyze, daily, status)

**Files:**
- `D:/Plan/plan/cli.py` (implement core commands)
- `D:/Plan/tests/test_cli.py` (create)

- [ ] Implement core commands in `D:/Plan/plan/cli.py`:
```python
"""CLI entry point."""
from __future__ import annotations

import click
from plan.config import get_config


@click.group()
def cli():
    """AI-powered personal planning agent."""


@cli.command()
def chat():
    """Interactive conversation with AI. Updates context.md after each session."""
    from plan.agent import chat_turn
    from plan.memory import append_context

    click.echo("Starting chat session. Type 'exit' or Ctrl-C to quit.\n")
    history: list[dict] = []
    session_notes: list[str] = []

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip().lower() in ("exit", "quit", "q"):
            break

        reply, history = chat_turn(user_input, history)
        click.echo(f"\nAssistant: {reply}\n")
        session_notes.append(f"User: {user_input}\nAssistant: {reply}")

    if session_notes:
        summary = "\n\n".join(session_notes)
        append_context(f"Chat session summary:\n{summary}")
        click.echo("Context updated.")


@cli.command()
def analyze():
    """Analyze profile + context + tasks and generate a time-blocked daily plan."""
    from plan.agent import run_analyze
    from plan.config import get_config
    from plan.sources import load_sources
    from plan.tasks import upsert_from_source

    cfg = get_config()
    sources = load_sources(cfg)

    extra_items: list[dict] = []
    for src in sources:
        try:
            items = src.fetch()
            extra_items.extend(i.to_task_dict() for i in items)
            upsert_from_source([i.to_task_dict() for i in items])
            click.echo(f"Fetched {len(items)} items from source: {src.name}")
        except Exception as exc:
            click.echo(f"Warning: source {src.name!r} failed: {exc}", err=True)

    click.echo("Running analysis...")
    tasks = run_analyze(extra_items=extra_items)
    scheduled = [t for t in tasks if t.get("time_block")]
    click.echo(f"Done. {len(scheduled)}/{len(tasks)} tasks scheduled.")
    for t in sorted(scheduled, key=lambda x: x.get("time_block", "")):
        click.echo(f"  {t['time_block']}  {t['title']}")


@cli.command()
def daily():
    """Run analyze (called by Windows Task Scheduler for daily planning)."""
    ctx = click.get_current_context()
    ctx.invoke(analyze)


@cli.command()
def status():
    """Print today's plan and context summary."""
    from plan.memory import read_context
    from plan.tasks import list_tasks

    context = read_context()
    tasks = list_tasks(status="open")
    scheduled = [t for t in tasks if t.get("time_block")]

    click.echo("=== Context ===")
    click.echo(context[:500] if context else "(no context)")
    click.echo()
    click.echo(f"=== Today's Schedule ({len(scheduled)} tasks) ===")
    if not scheduled:
        click.echo("  No tasks scheduled. Run `plan analyze` to generate a plan.")
    else:
        for t in sorted(scheduled, key=lambda x: x.get("time_block", "")):
            done_marker = "[x]" if t.get("status") == "done" else "[ ]"
            click.echo(f"  {done_marker} {t['time_block']}  {t['title']}")


if __name__ == "__main__":
    cli()
```

- [ ] Create `D:/Plan/tests/test_cli.py`:
```python
"""CLI tests using click.testing.CliRunner."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from plan.cli import cli


@pytest.fixture(autouse=True)
def patch_data_paths(monkeypatch, tmp_path):
    import plan.config as cfg
    cfg._cache = None
    profile_file = tmp_path / "profile.md"
    context_file = tmp_path / "context.md"
    tasks_file = tmp_path / "tasks.json"
    profile_file.write_text("# Profile\nCS student.", encoding="utf-8")
    context_file.write_text("# Context\nFeel good.", encoding="utf-8")
    tasks_file.write_text("[]", encoding="utf-8")
    original = cfg.resolve_path
    def fake(key):
        return {"profile": profile_file, "context": context_file, "tasks": tasks_file}.get(key, original(key))
    monkeypatch.setattr(cfg, "resolve_path", fake)
    yield


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "planning agent" in result.output.lower()


def test_status_no_tasks():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Context" in result.output
    assert "No tasks scheduled" in result.output


def test_status_with_scheduled_task(monkeypatch, tmp_path):
    import plan.config as cfg
    tasks_file = tmp_path / "tasks2.json"
    tasks_file.write_text(json.dumps([{
        "id": "abc", "title": "Study ML", "status": "open",
        "time_block": "09:00-10:30", "priority": 2, "source": "local",
        "project": None, "due": None, "ticktick_id": None,
    }]), encoding="utf-8")
    original = cfg.resolve_path
    def fake(key):
        if key == "tasks":
            return tasks_file
        return original(key)
    monkeypatch.setattr(cfg, "resolve_path", fake)
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert "09:00-10:30" in result.output
    assert "Study ML" in result.output


def test_analyze_calls_run_analyze():
    with patch("plan.agent.run_analyze", return_value=[]) as mock_analyze:
        with patch("plan.sources.load_sources", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["analyze"])
    assert result.exit_code == 0
    mock_analyze.assert_called_once()


def test_daily_calls_analyze():
    with patch("plan.agent.run_analyze", return_value=[]) as mock_analyze:
        with patch("plan.sources.load_sources", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    mock_analyze.assert_called_once()
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_cli.py -v
```
Expected:
```
tests/test_cli.py::test_cli_help PASSED
tests/test_cli.py::test_status_no_tasks PASSED
tests/test_cli.py::test_status_with_scheduled_task PASSED
tests/test_cli.py::test_analyze_calls_run_analyze PASSED
tests/test_cli.py::test_daily_calls_analyze PASSED
5 passed
```

- [ ] Commit:
```bash
cd D:/Plan && git add plan/cli.py tests/test_cli.py && git commit -m "feat: CLI core commands — chat, analyze, daily, status"
```

---

### Task 10: CLI Commands — Tasks (task add/list/done)

**Files:**
- `D:/Plan/plan/cli.py` (add task subgroup)

- [ ] Add task subgroup to `D:/Plan/plan/cli.py` (append before `if __name__ == "__main__":`):
```python
@cli.group()
def task():
    """Manage tasks."""


@task.command("add")
@click.argument("title")
@click.option("--project", "-p", default=None, help="Project name")
@click.option("--due", "-d", default=None, help="Due date (YYYY-MM-DD)")
@click.option("--priority", "-P", default=0, type=click.IntRange(0, 3),
              help="Priority 0-3 (0=none, 3=high)")
def task_add(title, project, due, priority):
    """Add a new task."""
    from plan.tasks import add_task
    t = add_task(title, project=project, due=due, priority=priority)
    click.echo(f"Added: [{t['id'][:8]}] {t['title']}")


@task.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include done tasks")
@click.option("--project", "-p", default=None)
def task_list(show_all, project):
    """List tasks."""
    from plan.tasks import list_tasks
    status = None if show_all else "open"
    tasks = list_tasks(status=status, project=project)
    if not tasks:
        click.echo("No tasks.")
        return
    for t in tasks:
        done = "x" if t.get("status") == "done" else " "
        tb = f"  [{t['time_block']}]" if t.get("time_block") else ""
        proj = f"  ({t['project']})" if t.get("project") else ""
        click.echo(f"[{done}] {t['id'][:8]}  {t['title']}{proj}{tb}")


@task.command("done")
@click.argument("task_id_prefix")
def task_done(task_id_prefix):
    """Mark a task as done (by ID prefix)."""
    from plan.tasks import load_tasks, mark_done
    tasks = load_tasks()
    matches = [t for t in tasks if t["id"].startswith(task_id_prefix)]
    if not matches:
        click.echo(f"No task found with ID prefix: {task_id_prefix}", err=True)
        raise SystemExit(1)
    if len(matches) > 1:
        click.echo(f"Ambiguous prefix {task_id_prefix!r} matches {len(matches)} tasks.", err=True)
        raise SystemExit(1)
    result = mark_done(matches[0]["id"])
    click.echo(f"Done: {result['title']}")
```

- [ ] Add task command tests to `D:/Plan/tests/test_cli.py`:
```python
# --- task subcommand tests (add to test_cli.py) ---

def test_task_add():
    runner = CliRunner()
    result = runner.invoke(cli, ["task", "add", "Write essay", "--priority", "2"])
    assert result.exit_code == 0
    assert "Write essay" in result.output


def test_task_list_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["task", "list"])
    assert result.exit_code == 0
    assert "No tasks" in result.output


def test_task_list_shows_tasks():
    runner = CliRunner()
    runner.invoke(cli, ["task", "add", "Study ML"])
    result = runner.invoke(cli, ["task", "list"])
    assert "Study ML" in result.output


def test_task_done():
    runner = CliRunner()
    runner.invoke(cli, ["task", "add", "Finish lab"])
    from plan.tasks import load_tasks
    tasks = load_tasks()
    prefix = tasks[0]["id"][:8]
    result = runner.invoke(cli, ["task", "done", prefix])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_task_done_not_found():
    runner = CliRunner()
    result = runner.invoke(cli, ["task", "done", "nonexistent"])
    assert result.exit_code != 0
```

- [ ] Run tests:
```bash
cd D:/Plan && pytest tests/test_cli.py -v -k task
```
Expected: 5 task-related tests pass.

- [ ] Commit:
```bash
cd D:/Plan && git add plan/cli.py tests/test_cli.py && git commit -m "feat: CLI task subcommands — add, list, done"
```

---

### Task 11: CLI Commands — sync, config set, schedule install/uninstall

**Files:**
- `D:/Plan/plan/cli.py` (add sync, config, schedule commands)
- `D:/Plan/plan/scheduler.py` (create)

- [ ] Create `D:/Plan/plan/scheduler.py`:
```python
"""Windows Task Scheduler integration via schtasks.exe."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TASK_NAME = "PlanDailyAgent"


def _python_exe() -> str:
    return sys.executable


def _plan_exe() -> str:
    """Return the path to the plan CLI script."""
    scripts = Path(sys.executable).parent / "Scripts" / "plan.exe"
    if scripts.exists():
        return str(scripts)
    # fallback: python -m plan.cli
    return f"{_python_exe()} -m plan.cli"


def install(daily_time: str = "08:00") -> None:
    """Register a daily Task Scheduler entry that runs `plan daily`."""
    hour, minute = daily_time.split(":")
    plan_cmd = _plan_exe()
    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", TASK_NAME,
        "/TR", f"{plan_cmd} daily",
        "/SC", "DAILY",
        "/ST", f"{hour}:{minute}",
        "/RL", "HIGHEST",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"schtasks /Create failed:\n{result.stderr}")


def uninstall() -> None:
    """Remove the Task Scheduler entry."""
    cmd = ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"schtasks /Delete failed:\n{result.stderr}")


def is_installed() -> bool:
    """Return True if the scheduled task exists."""
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True, text=True,
    )
    return result.returncode == 0
```

- [ ] Add sync, config, schedule commands to `D:/Plan/plan/cli.py` (append before `if __name__ == "__main__":`):
```python
@cli.command()
def sync():
    """Bidirectional sync with all writable sources (e.g. TickTick)."""
    from plan.config import get_config
    from plan.sources import load_sources
    from plan.tasks import load_tasks, upsert_from_source

    cfg = get_config()
    sources = load_sources(cfg)
    writable = [s for s in sources if s.is_writable]

    if not writable:
        click.echo("No writable sources enabled. Check config.toml.")
        return

    tasks = load_tasks()
    for src in writable:
        try:
            # Pull
            items = src.fetch()
            upsert_from_source([i.to_task_dict() for i in items])
            click.echo(f"Pulled {len(items)} items from {src.name}")
            # Push
            src.push(tasks)
            click.echo(f"Pushed {len(tasks)} tasks to {src.name}")
        except NotImplementedError:
            click.echo(f"Source {src.name!r} does not support push, skipping.")
        except Exception as exc:
            click.echo(f"Sync error for {src.name!r}: {exc}", err=True)


@cli.group("config")
def config_group():
    """Manage configuration."""


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a config key (dot-separated) to a value.

    Examples:
      plan config set ai.model claude-sonnet-4-6
      plan config set schedule.daily_time 07:30
      plan config set sources.ticktick.enabled true
    """
    from plan.config import set_key

    # Coerce common types
    coerced: object = value
    if value.lower() == "true":
        coerced = True
    elif value.lower() == "false":
        coerced = False
    else:
        try:
            coerced = int(value)
        except ValueError:
            try:
                coerced = float(value)
            except ValueError:
                pass  # keep as string

    set_key(key, coerced)
    click.echo(f"Set {key} = {coerced!r}")


@cli.group()
def schedule():
    """Manage Windows Task Scheduler integration."""


@schedule.command("install")
def schedule_install():
    """Register a daily Task Scheduler entry."""
    from plan.config import get
    from plan.scheduler import install, is_installed

    daily_time = get("schedule.daily_time", "08:00")
    if is_installed():
        click.echo("Task already installed. Reinstalling...")
    install(daily_time)
    click.echo(f"Scheduled daily run at {daily_time}.")


@schedule.command("uninstall")
def schedule_uninstall():
    """Remove the Task Scheduler entry."""
    from plan.scheduler import uninstall, is_installed

    if not is_installed():
        click.echo("Task is not installed.")
        return
    uninstall()
    click.echo("Scheduled task removed.")
```

- [ ] Run full CLI test suite:
```bash
cd D:/Plan && pytest tests/test_cli.py -v
```
Expected: all tests pass.

- [ ] Commit:
```bash
cd D:/Plan && git add plan/cli.py plan/scheduler.py && git commit -m "feat: sync, config set, schedule install/uninstall commands"
```

---

### Task 12: Initial profile.md

**Files:**
- `D:/Plan/data/profile.md` (implement with real user context)

- [ ] Write `D:/Plan/data/profile.md`:
```markdown
# Personal Profile

## Identity
- ZJU (Zhejiang University) sophomore, Computer Science major
- Currently doing an AI startup internship (part-time)
- Member of a university ML research group

## Career Goals
- Land a big-tech internship (ByteDance / Alibaba / Tencent / top foreign tech) by July 2026
- Build strong ML/systems fundamentals to support research and engineering roles
- Publish or contribute to at least one ML research project this year

## Current Commitments
- **Courses:** Core CS sophomore curriculum (algorithms, OS, computer networks, linear algebra)
- **Internship:** AI startup — working on LLM-related features, ~3 days/week
- **Research:** ML research group — reading papers, running experiments, weekly meetings
- **Self-study:** LeetCode (targeting 200+ problems before interview season), ML theory

## Anxieties & Pressure Points
- Grades: worried about GPA slipping due to internship + research load
- Career timeline: July deadline for big-tech internship feels tight
- Context switching: hard to stay deep on research when internship tasks are urgent
- Energy management: tendency to overcommit and burn out

## Working Style
- Most productive in the morning (08:00-12:00)
- Needs explicit time blocks to avoid procrastination
- Prefers to batch similar tasks (all coding together, all reading together)
- Responds well to concrete daily goals rather than vague to-do lists

## Values
- Depth over breadth: would rather understand one thing deeply than skim many
- Shipping matters: wants to see tangible output from each work session
- Health: sleep 7-8h is non-negotiable; exercise 3x/week target

## Projects & Areas
- **internship:** AI startup tasks and deliverables
- **research:** ML research group experiments and paper reading
- **courses:** ZJU coursework and assignments
- **career:** LeetCode, resume, interview prep
- **personal:** health, reading, life admin
```

- [ ] Verify profile is readable:
```bash
cd D:/Plan && python3 -c "from plan.memory import read_profile; p = read_profile(); print(p[:200])"
```
Expected: first 200 chars of profile.md printed.

- [ ] Commit:
```bash
cd D:/Plan && git add data/profile.md && git commit -m "chore: initial user profile with ZJU CS student context"
```

---

### Task 13: Wire Everything Together — End-to-End Test

**Files:**
- `D:/Plan/tests/test_e2e.py` (create)

- [ ] Create `D:/Plan/tests/test_e2e.py`:
```python
"""End-to-end integration test: full analyze cycle with mocked Claude."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from plan.cli import cli


@pytest.fixture()
def populated_env(monkeypatch, tmp_path):
    """Set up a realistic data environment."""
    import plan.config as cfg
    cfg._cache = None

    profile_file = tmp_path / "profile.md"
    context_file = tmp_path / "context.md"
    tasks_file = tmp_path / "tasks.json"

    profile_file.write_text(
        "# Profile\nZJU CS sophomore. AI internship. ML research. Target big-tech by July.",
        encoding="utf-8",
    )
    context_file.write_text(
        "# Context\nFeel a bit overwhelmed. Internship deadline tomorrow.",
        encoding="utf-8",
    )
    tasks_file.write_text(json.dumps([
        {"id": "t1", "title": "Finish internship PR", "project": "internship",
         "due": "2026-04-13", "priority": 3, "status": "open",
         "source": "local", "ticktick_id": None, "time_block": None},
        {"id": "t2", "title": "Read attention paper", "project": "research",
         "due": None, "priority": 2, "status": "open",
         "source": "local", "ticktick_id": None, "time_block": None},
        {"id": "t3", "title": "LeetCode 2 problems", "project": "career",
         "due": None, "priority": 1, "status": "open",
         "source": "local", "ticktick_id": None, "time_block": None},
    ]), encoding="utf-8")

    original = cfg.resolve_path
    def fake(key):
        return {"profile": profile_file, "context": context_file, "tasks": tasks_file}.get(key, original(key))
    monkeypatch.setattr(cfg, "resolve_path", fake)
    yield {"profile": profile_file, "context": context_file, "tasks": tasks_file}


def test_full_analyze_cycle(populated_env):
    """analyze command fetches sources, calls Claude, writes time blocks back."""
    mock_response = """
<context>
Today's focus: finish internship PR first (due tomorrow), then read attention paper, then LeetCode.
</context>
<tasks>
[
  {"id": "t1", "title": "Finish internship PR", "project": "internship",
   "due": "2026-04-13", "priority": 3, "status": "open",
   "source": "local", "ticktick_id": null, "time_block": "09:00-11:30"},
  {"id": "t2", "title": "Read attention paper", "project": "research",
   "due": null, "priority": 2, "status": "open",
   "source": "local", "ticktick_id": null, "time_block": "13:00-14:30"},
  {"id": "t3", "title": "LeetCode 2 problems", "project": "career",
   "due": null, "priority": 1, "status": "open",
   "source": "local", "ticktick_id": null, "time_block": "15:00-16:00"}
]
</tasks>
"""
    with patch("plan.agent.call_claude", return_value=mock_response):
        with patch("plan.sources.load_sources", return_value=[]):
            runner = CliRunner()
            result = runner.invoke(cli, ["analyze"])

    assert result.exit_code == 0
    assert "3/3 tasks scheduled" in result.output

    tasks = json.loads(populated_env["tasks"].read_text(encoding="utf-8"))
    assert tasks[0]["time_block"] == "09:00-11:30"
    assert tasks[1]["time_block"] == "13:00-14:30"
    assert tasks[2]["time_block"] == "15:00-16:00"

    context = populated_env["context"].read_text(encoding="utf-8")
    assert "internship PR" in context


def test_status_after_analyze(populated_env):
    """status command shows scheduled tasks after analyze."""
    tasks_data = json.loads(populated_env["tasks"].read_text(encoding="utf-8"))
    tasks_data[0]["time_block"] = "09:00-11:30"
    populated_env["tasks"].write_text(json.dumps(tasks_data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "09:00-11:30" in result.output
    assert "Finish internship PR" in result.output


def test_task_add_then_list_then_done(populated_env):
    """Full task lifecycle: add -> list -> done."""
    runner = CliRunner()

    result = runner.invoke(cli, ["task", "add", "Review PR feedback", "--priority", "3"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["task", "list"])
    assert "Review PR feedback" in result.output

    import plan.tasks as t_mod
    tasks = t_mod.load_tasks()
    new_task = next(t for t in tasks if t["title"] == "Review PR feedback")
    prefix = new_task["id"][:8]

    result = runner.invoke(cli, ["task", "done", prefix])
    assert result.exit_code == 0
    assert "Done" in result.output

    tasks = t_mod.load_tasks()
    done_task = next(t for t in tasks if t["title"] == "Review PR feedback")
    assert done_task["status"] == "done"


def test_config_set_persists(populated_env, tmp_path):
    """config set writes to config.toml and is readable back."""
    from pathlib import Path
    import tomllib, tomli_w
    config_path = Path("D:/Plan/config.toml")
    backup = config_path.read_bytes()
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "set", "schedule.daily_time", "07:30"])
        assert result.exit_code == 0
        import plan.config as cfg
        cfg._cache = None
        assert cfg.get("schedule.daily_time") == "07:30"
    finally:
        config_path.write_bytes(backup)
        import plan.config as cfg
        cfg._cache = None
```

- [ ] Run full test suite:
```bash
cd D:/Plan && pytest tests/ -v --tb=short
```
Expected: all tests pass (approximately 36+ tests across all modules).

- [ ] Run a manual smoke test (requires ANTHROPIC_API_KEY set):
```bash
cd D:/Plan && plan task add "Test the plan tool" --priority 1
plan task list
plan analyze
plan status
```

- [ ] Final commit:
```bash
cd D:/Plan && git add tests/test_e2e.py && git commit -m "test: end-to-end integration tests for full analyze cycle"
```

---
