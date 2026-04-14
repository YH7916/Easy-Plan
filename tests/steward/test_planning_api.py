from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


def test_today_queue_returns_prioritized_tasks(steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.get("/planning/today-queue", params={"today": "2026-04-14"})
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-04-14"
    assert "tasks" in data
    assert "time_blocks" in data
    assert "total_estimated_minutes" in data
    tasks = data["tasks"]
    if len(tasks) > 1:
        for i in range(len(tasks) - 1):
            assert tasks[i]["priority"] >= tasks[i + 1]["priority"]


def test_planning_task_lifecycle(steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    # create
    created = client.post(
        "/planning/tasks",
        json={"title": "Test task", "project": "test", "priority": 2},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["title"] == "Test task"
    assert created.json()["status"] == "open"

    # list includes new task
    tasks = client.get("/planning/tasks")
    assert tasks.status_code == 200
    assert any(t["id"] == task_id for t in tasks.json())

    # complete
    completed = client.post(f"/planning/tasks/{task_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"

    # 404 on unknown task
    not_found = client.post("/planning/tasks/nonexistent/complete")
    assert not_found.status_code == 404
    assert not_found.json()["detail"]["error"] == "not_found"


def test_planning_tasks_persisted_to_file(steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    client.post(
        "/planning/tasks",
        json={"title": "Persisted task", "project": "test", "priority": 1},
    )

    persisted = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert any(t["title"] == "Persisted task" for t in persisted)


def test_task_state_transitions(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    # create open task
    created = client.post("/planning/tasks", json={"title": "State test", "priority": 1})
    assert created.status_code == 201
    task_id = created.json()["id"]

    # open -> in_progress
    r = client.patch(f"/planning/tasks/{task_id}/status", json={"status": "in_progress"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    # in_progress -> blocked
    r = client.patch(f"/planning/tasks/{task_id}/status", json={"status": "blocked"})
    assert r.status_code == 200
    assert r.json()["status"] == "blocked"

    # blocked -> done is invalid (409)
    r = client.patch(f"/planning/tasks/{task_id}/status", json={"status": "done"})
    assert r.status_code == 409

    # invalid status (400)
    r = client.patch(f"/planning/tasks/{task_id}/status", json={"status": "invalid"})
    assert r.status_code == 400
