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
    # memory.py uses `from plan.config import resolve_path` so patch its local binding too
    import plan.memory as mem_mod
    monkeypatch.setattr(mem_mod, "resolve_path", fake)
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

    assert result.exit_code == 0, f"analyze failed: {result.output}"
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


def test_config_set_persists(populated_env):
    """config set writes to config.toml and is readable back."""
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
