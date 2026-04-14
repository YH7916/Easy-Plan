import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_overview_and_planning_round_trip(monkeypatch, steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.host import create_app
    from plan.steward.contracts import SourceItemDto

    monkeypatch.setattr(
        "plan.steward.adapters.lazy_zju.LazyZjuAdapter.fetch_items",
        lambda self: [
            SourceItemDto(
                title="Lab 3",
                source="lazy_zju",
                due="2026-04-17",
                project="courses",
                priority=2,
                external_id="assignment_42",
            )
        ],
    )

    client = TestClient(create_app(settings))
    overview = client.get("/overview/summary", params={"today": "2026-04-14"})
    planning = client.get("/planning/tasks")
    suggestions = client.get("/planning/suggestions")
    created = client.post(
        "/planning/tasks",
        json={"title": "Review work review adapter", "project": "plan-steward", "priority": 2},
    )
    accepted = client.post(
        "/planning/suggestions/accept",
        json={
            "title": "Lab 3",
            "source": "lazy_zju",
            "due": "2026-04-17",
            "project": "courses",
            "priority": 2,
            "external_id": "assignment_42",
            "reason": "Source item from lazy_zju is not yet tracked in the unified task pool.",
        },
    )
    suggestions_after_accept = client.get("/planning/suggestions")
    completed = client.post("/planning/tasks/task-1/complete")

    assert overview.status_code == 200
    assert overview.json()["open_task_count"] == 1
    assert overview.json()["high_priority_open_count"] == 1
    assert overview.json()["pending_intake_count"] == 1
    assert overview.json()["due_soon_source_count"] == 0
    assert overview.json()["overdue_source_count"] == 0
    assert overview.json()["focus_apps"][0] == "VS Code"
    assert "Review 1 pending source items" in overview.json()["recommended_next_actions"][0]
    assert any(
        action["id"] == "review_intake_queue"
        and action["target_page"] == "planning"
        and action["can_execute"] is True
        and action["execute_label"] == "Accept Top Item"
        for action in overview.json()["recommended_actions"]
    )
    assert any(
        action["id"] == "sequence_high_priority_tasks"
        and action["target_page"] == "chat"
        and "high-priority tasks" in action["chat_prompt"]
        for action in overview.json()["recommended_actions"]
    )
    assert any(
        action["id"] == "capture_daily_review" and action["can_execute"] is True
        for action in overview.json()["recommended_actions"]
    )
    assert "Work review data available" in overview.json()["active_alerts"]
    assert planning.status_code == 200
    assert planning.json()[0]["title"] == "Finish backend host"
    assert suggestions.status_code == 200
    assert suggestions.json()[0]["title"] == "Lab 3"
    assert created.status_code == 201
    assert created.json()["title"] == "Review work review adapter"
    assert accepted.status_code == 201
    assert accepted.json()["title"] == "Lab 3"
    assert accepted.json()["source"] == "lazy_zju"
    assert accepted.json()["ticktick_id"] == "assignment_42"
    assert suggestions_after_accept.status_code == 200
    assert suggestions_after_accept.json() == []
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"
    persisted = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert any(task["title"] == "Review work review adapter" for task in persisted)
    assert any(task["ticktick_id"] == "assignment_42" for task in persisted)


def test_overview_execute_planning_action_accepts_top_suggestion(monkeypatch, steward_env):
    settings, tasks_file, _ = steward_env

    from plan.steward.contracts import SourceItemDto
    from plan.steward.host import create_app

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
                due="2026-04-20",
                project="courses",
                priority=1,
                external_id="assignment_99",
            ),
        ],
    )

    client = TestClient(create_app(settings))

    overview = client.get("/overview/summary", params={"today": "2026-04-14"})
    execution = client.post(
        "/overview/actions/execute",
        json={"action_id": "review_intake_queue", "today": "2026-04-14"},
    )
    planning = client.get("/planning/tasks")

    assert overview.status_code == 200
    assert any(
        action["id"] == "review_intake_queue" and action["can_execute"] is True
        for action in overview.json()["recommended_actions"]
    )
    assert execution.status_code == 200
    assert "accepted" in execution.json()["summary"].lower()
    assert execution.json()["target_page"] == "planning"
    assert execution.json()["created_task"]["title"] == "Lab 3"
    assert execution.json()["created_task"]["source"] == "lazy_zju"
    assert any(task["title"] == "Lab 3" for task in planning.json())
    persisted = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert any(task["ticktick_id"] == "assignment_42" for task in persisted)


def test_insights_notes_chat_settings_routes(monkeypatch, steward_env):
    settings, _, vault_root = steward_env

    from plan.steward.host import create_app

    monkeypatch.setattr(
        "plan.steward.modules.chat.chat_turn",
        lambda user_message, history: (f"reply:{user_message}", history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": f"reply:{user_message}"}]),
    )

    client = TestClient(create_app(settings))

    report = client.get("/insights/reports/daily", params={"date": "2026-04-13"})
    notes = client.get("/notes/index")
    chat_session = client.get("/chat/sessions/default", params={"today": "2026-04-13"})
    note = client.post(
        "/notes/drafts/daily",
        json={"date": "2026-04-13", "title": "Steward Daily", "content": "# Daily\n\nMerged report."},
    )
    daily_review_note = client.post(
        "/notes/drafts/daily-review",
        json={"date": "2026-04-13"},
    )
    notes_dashboard = client.get("/notes/dashboard")
    actionable_chat = client.post(
        "/chat/sessions/default/messages",
        json={"message": "plan next lab deliverable"},
    )
    capture_action = client.post(
        "/chat/sessions/default/actions",
        json={"action_id": "capture_latest_message_as_task"},
    )
    review_action = client.post(
        "/chat/sessions/default/actions",
        json={"action_id": "write_daily_review_draft", "today": "2026-04-13"},
    )
    overview_action = client.post(
        "/overview/actions/execute",
        json={"action_id": "capture_daily_review", "today": "2026-04-14"},
    )
    health = client.get("/settings/health")

    assert report.status_code == 200
    assert "今天主要在实现后端" in report.json()["summary_markdown"]
    assert report.json()["top_apps"][0] == "VS Code"
    assert notes.status_code == 200
    assert notes.json()["notes"][0]["title"] == "Existing Note"
    assert chat_session.status_code == 200
    assert chat_session.json()["session_id"] == "default"
    assert chat_session.json()["history"] == []
    assert any(
        "high-priority tasks" in prompt
        for prompt in chat_session.json()["starter_prompts"]
    )
    assert any(
        action["id"] == "write_daily_review_draft"
        for action in chat_session.json()["suggested_actions"]
    )
    assert note.status_code == 201
    assert "obsidian://open" in note.json()["obsidian_url"]
    assert (vault_root / "Steward" / "Daily").exists()
    assert daily_review_note.status_code == 201
    assert "obsidian://open" in daily_review_note.json()["obsidian_url"]
    generated_path = Path(daily_review_note.json()["path"])
    assert generated_path.exists()
    generated_content = generated_path.read_text(encoding="utf-8")
    assert "# Plan Steward Daily Review 2026-04-13" in generated_content
    assert "今天主要在实现后端" in generated_content
    assert "VS Code" in generated_content
    assert notes_dashboard.status_code == 200
    assert notes_dashboard.json()["vault_ready"] is True
    assert notes_dashboard.json()["indexed_count"] == 3
    assert notes_dashboard.json()["generated_count"] == 2
    assert len(notes_dashboard.json()["recent_notes"]) == 3
    assert len(notes_dashboard.json()["generated_notes"]) == 2
    assert any(
        "Plan Steward Daily Review 2026-04-13" in note_item["title"]
        for note_item in notes_dashboard.json()["generated_notes"]
    )
    assert actionable_chat.status_code == 200
    assert actionable_chat.json()["reply"] == "reply:plan next lab deliverable"
    assert len(actionable_chat.json()["history"]) == 2
    assert any(
        action["id"] == "capture_latest_message_as_task"
        for action in actionable_chat.json()["suggested_actions"]
    )
    assert capture_action.status_code == 200
    assert "Planning" in capture_action.json()["summary"]
    assert capture_action.json()["created_task"]["title"] == "Plan next lab deliverable"
    assert capture_action.json()["created_task"]["source"] == "chat"
    assert any(
        message["content"].startswith("I added")
        for message in capture_action.json()["session"]["history"]
        if message["role"] == "assistant"
    )
    assert not any(
        action["id"] == "capture_latest_message_as_task"
        for action in capture_action.json()["session"]["suggested_actions"]
    )
    assert review_action.status_code == 404
    assert "not available" in review_action.json()["detail"]["message"].lower()
    planning_after_capture = client.get("/planning/tasks")
    assert any(
        task["title"] == "Plan next lab deliverable" and task["source"] == "chat"
        for task in planning_after_capture.json()
    )
    assert overview_action.status_code == 200
    assert "daily review draft" in overview_action.json()["summary"].lower()
    assert overview_action.json()["target_page"] == "insights"
    assert "obsidian://open" in overview_action.json()["note_draft"]["obsidian_url"]
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert "automation" in health.json()["modules"]
