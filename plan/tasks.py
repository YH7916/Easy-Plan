"""Task store: load/save tasks.json, CRUD operations."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import TypedDict

import plan.config as _config


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
    return _config.resolve_path("tasks")


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
    """Merge source items into tasks.json by external_id, adding new ones.

    Input items must have a "title" field. The external identifier is read
    from "external_id" (preferred, from SourceItem.to_task_dict()) or
    "ticktick_id" (fallback, for direct Task dict input). The identifier
    is stored as "ticktick_id" in tasks.json.
    """
    tasks = load_tasks()
    existing_ext_ids = {t.get("ticktick_id") for t in tasks if t.get("ticktick_id")}
    for item in items:
        ext_id = item.get("external_id") or item.get("ticktick_id")
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
