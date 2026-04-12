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
