from __future__ import annotations

from fastapi.testclient import TestClient


def test_daily_report(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.get("/insights/reports/daily", params={"date": "2026-04-13"})
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-04-13"
    assert "summary_markdown" in data
    assert "top_apps" in data
    assert "open_task_count" in data
    assert data["top_apps"][0] == "VS Code"
    assert "今天主要在实现后端" in data["summary_markdown"]


def test_weekly_report(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.get("/insights/reports/weekly", params={"week_start": "2026-04-13"})
    assert response.status_code == 200
    data = response.json()
    assert "week_start" in data
    assert "week_end" in data
    assert "summary_markdown" in data
    assert "daily_reports_count" in data
    assert data["daily_reports_count"] >= 0
    assert data["week_start"] <= data["week_end"]


def test_weekly_report_includes_daily_data(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    client = TestClient(create_app(settings))

    response = client.get("/insights/reports/weekly", params={"week_start": "2026-04-13"})
    assert response.status_code == 200
    data = response.json()
    # The fixture has one activity on 2026-04-13, so at least one daily report should be found
    assert data["daily_reports_count"] >= 1
    assert "VS Code" in data["top_apps"]
