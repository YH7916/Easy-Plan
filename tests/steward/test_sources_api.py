import json

from fastapi.testclient import TestClient


def test_sources_dashboard_classifies_pending_and_tracked_items(monkeypatch, steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.contracts import SourceItemDto
    from plan.steward.host import create_app

    tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
    tasks.append(
        {
            "id": "task-2",
            "title": "Lab 3",
            "project": "courses",
            "due": "2026-04-15",
            "priority": 2,
            "status": "open",
            "source": "lazy_zju",
            "ticktick_id": "assignment_42",
            "time_block": None,
        }
    )
    tasks_file.write_text(json.dumps(tasks), encoding="utf-8")

    monkeypatch.setattr(
        "plan.steward.adapters.lazy_zju.LazyZjuAdapter.fetch_items",
        lambda self: [
            SourceItemDto(
                title="Lab 3",
                source="lazy_zju",
                due="2026-04-15",
                project="courses",
                priority=2,
                external_id="assignment_42",
            ),
            SourceItemDto(
                title="HW 4",
                source="lazy_zju",
                due="2026-04-30",
                project="courses",
                priority=0,
                external_id="assignment_99",
            ),
        ],
    )

    client = TestClient(create_app(settings))
    dashboard = client.get("/sources/dashboard", params={"today": "2026-04-14"})

    assert dashboard.status_code == 200
    assert dashboard.json()["tracked_count"] == 1
    assert dashboard.json()["pending_intake_count"] == 1
    assert dashboard.json()["due_soon_count"] == 1
    assert dashboard.json()["items"][0]["tracking_status"] == "tracked"
    assert dashboard.json()["items"][0]["urgency"] == "due_soon"
    assert dashboard.json()["items"][0]["tracked_task_status"] == "open"
    assert dashboard.json()["items"][1]["tracking_status"] == "pending_intake"
    assert "Accept into planning" in dashboard.json()["items"][1]["recommendation"]
