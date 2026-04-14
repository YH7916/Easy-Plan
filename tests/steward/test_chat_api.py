from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_session_get(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.get("/chat/sessions/default", params={"today": "2026-04-14"})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "default"
    assert "history" in data
    assert "starter_prompts" in data
    assert "suggested_actions" in data
    assert data["history"] == []


def test_chat_send_message(monkeypatch, steward_env):
    settings, _, _ = steward_env

    monkeypatch.setattr(
        "plan.steward.modules.chat.chat_turn",
        lambda msg, history: (
            f"reply:{msg}",
            history + [
                {"role": "user", "content": msg},
                {"role": "assistant", "content": f"reply:{msg}"},
            ],
        ),
    )

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.post("/chat/sessions/default/messages", json={"message": "hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "reply:hello"
    assert len(data["history"]) == 2
    assert data["history"][0]["role"] == "user"
    assert data["history"][1]["role"] == "assistant"


def test_chat_action_not_available(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.post(
        "/chat/sessions/default/actions",
        json={"action_id": "nonexistent_action"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "not_found"


def test_chat_starter_prompts_reflect_open_tasks(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    # The fixture has one high-priority open task, so the session should suggest sequencing
    response = client.get("/chat/sessions/default", params={"today": "2026-04-14"})
    assert response.status_code == 200
    prompts = response.json()["starter_prompts"]
    assert len(prompts) >= 1
    assert any("high-priority" in p or "focus" in p.lower() for p in prompts)
