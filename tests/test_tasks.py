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
