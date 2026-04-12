"""Tests for plan.agent — all Claude calls are mocked."""
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


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


def test_build_prompt_contains_profile_and_tasks():
    from plan.agent import build_prompt
    prompt_path = Path("D:/Plan/plan/prompts/analyze.txt")
    original = prompt_path.read_text(encoding="utf-8")
    try:
        prompt_path.write_text(
            "PROFILE:\n{{PROFILE}}\nCONTEXT:\n{{CONTEXT}}\nTASKS:\n{{TASKS_JSON}}\nEXTRA:\n{{EXTRA_ITEMS_JSON}}",
            encoding="utf-8"
        )
        result = build_prompt("My profile", "My context", [{"id": "1", "title": "Study"}])
        assert "My profile" in result
        assert "My context" in result
        assert "Study" in result
    finally:
        prompt_path.write_text(original, encoding="utf-8")


def test_parse_response_extracts_context_and_tasks():
    from plan.agent import parse_response
    response = """
<context>
# Updated Context
Feeling productive.
</context>

<tasks>
[{"id": "abc", "title": "Study ML", "time_block": "09:00-10:30"}]
</tasks>
"""
    ctx, tasks = parse_response(response)
    assert "Feeling productive" in ctx
    assert len(tasks) == 1
    assert tasks[0]["time_block"] == "09:00-10:30"


def test_parse_response_missing_sections():
    from plan.agent import parse_response
    ctx, tasks = parse_response("No structured output here.")
    assert ctx == ""
    assert tasks == []


def test_parse_response_bad_tasks_json():
    from plan.agent import parse_response
    response = "<context>ctx</context><tasks>not json</tasks>"
    ctx, tasks = parse_response(response)
    assert ctx == "ctx"
    assert tasks == []


def test_run_analyze_updates_time_blocks(monkeypatch):
    from plan.tasks import add_task, load_tasks
    t = add_task("Study ML")
    task_id = t["id"]

    mock_response = f"""
<context>
# Updated Context
Analyzed today.
</context>
<tasks>
[{{"id": "{task_id}", "title": "Study ML", "time_block": "09:00-10:30"}}]
</tasks>
"""
    with patch("plan.agent.call_claude", return_value=mock_response):
        from plan.agent import run_analyze
        tasks = run_analyze()

    assert tasks[0]["time_block"] == "09:00-10:30"

    from plan.memory import read_context
    assert "Analyzed today" in read_context()


def test_chat_turn_returns_reply(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Here is your plan.")]
    )
    with patch("plan.agent.anthropic.Anthropic", return_value=mock_client):
        with patch("plan.agent.api_key", return_value="fake-key"):
            from plan.agent import chat_turn
            reply, history = chat_turn("What should I do today?", [])

    assert reply == "Here is your plan."
    assert history[-1]["role"] == "assistant"
    assert history[-2]["role"] == "user"
