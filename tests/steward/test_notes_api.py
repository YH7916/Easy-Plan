from fastapi.testclient import TestClient


def test_daily_review_draft_lookup_and_overview_handoff(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    created = client.post(
        "/notes/drafts/daily-review",
        json={"date": "2026-04-14"},
    )
    existing = client.get(
        "/notes/drafts/daily-review",
        params={"date": "2026-04-14"},
    )
    overview = client.get("/overview/summary", params={"today": "2026-04-14"})

    assert created.status_code == 201
    assert existing.status_code == 200
    assert existing.json()["path"] == created.json()["path"]
    assert existing.json()["obsidian_url"] == created.json()["obsidian_url"]
    assert all(
        action["id"] != "capture_daily_review"
        for action in overview.json()["recommended_actions"]
    )
    assert any(
        action["id"] == "open_daily_review_draft"
        and action["target_page"] == "notes"
        for action in overview.json()["recommended_actions"]
    )
