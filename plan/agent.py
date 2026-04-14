"""Agent core: build prompt, call Claude, parse response."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import anthropic

from plan.config import get, api_key
from plan.memory import read_profile, read_context, write_context
from plan.tasks import load_tasks, save_tasks, Task

_PROMPT_PATH = Path(__file__).parent / "prompts" / "analyze.txt"


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_prompt(
    profile: str,
    context: str,
    tasks: list[Task],
    extra_items: list[dict] | None = None,
) -> str:
    """Render the analyze prompt with current data."""
    template = _load_prompt_template()
    tasks_json = json.dumps(tasks, indent=2, ensure_ascii=False)
    extra_json = json.dumps(extra_items or [], indent=2, ensure_ascii=False)
    return (
        template
        .replace("{{PROFILE}}", profile)
        .replace("{{CONTEXT}}", context)
        .replace("{{TASKS_JSON}}", tasks_json)
        .replace("{{EXTRA_ITEMS_JSON}}", extra_json)
    )


def _parse_sse_text(raw: str) -> str:
    """Parse SSE stream response into plain text (for proxy endpoints that return SSE)."""
    text = []
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = line[5:].strip()
            try:
                obj = json.loads(data)
                if obj.get("type") == "content_block_delta":
                    delta = obj.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text.append(delta.get("text", ""))
            except (json.JSONDecodeError, AttributeError):
                continue
    return "".join(text)


def call_claude(prompt: str) -> str:
    """Send prompt to Claude and return the raw text response."""
    client = anthropic.Anthropic(api_key=api_key())
    model = get("ai.model", "claude-sonnet-4-6")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    # Some proxy endpoints return SSE as a plain string instead of a Message object
    if isinstance(message, str):
        return _parse_sse_text(message)
    return message.content[0].text


def parse_response(response: str) -> tuple[str, list[Task]]:
    """Extract updated context and time-blocked tasks from Claude response.

    Expected response format:
        <context>
        ...updated context.md content...
        </context>

        <tasks>
        [{"id": "...", "time_block": "09:00-10:30", ...}, ...]
        </tasks>

    Returns:
        (new_context_text, list_of_task_dicts_with_time_block)
    """
    context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)
    tasks_match = re.search(r"<tasks>(.*?)</tasks>", response, re.DOTALL)

    new_context = context_match.group(1).strip() if context_match else ""

    tasks: list[Task] = []
    if tasks_match:
        try:
            tasks = json.loads(tasks_match.group(1).strip())
        except json.JSONDecodeError:
            tasks = []

    return new_context, tasks


def run_analyze(extra_items: list[dict] | None = None) -> list[Task]:
    """Full analyze cycle: read data, call Claude, write results back.

    Returns the updated task list with time_block fields set.
    """
    profile = read_profile()
    context = read_context()
    tasks = load_tasks()

    prompt = build_prompt(profile, context, tasks, extra_items)
    response = call_claude(prompt)
    new_context, updated_tasks = parse_response(response)

    if new_context:
        write_context(new_context)

    # Merge time_block values back into the main task list
    time_blocks: dict[str, str] = {
        t["id"]: t.get("time_block", "")
        for t in updated_tasks
        if t.get("id") and t.get("time_block")
    }
    for task in tasks:
        if task["id"] in time_blocks:
            task["time_block"] = time_blocks[task["id"]]

    save_tasks(tasks)
    return tasks


def chat_turn(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """Single chat turn: append user message, call Claude, return reply + updated history.

    history is a list of {"role": "user"|"assistant", "content": str} dicts.
    """
    client = anthropic.Anthropic(api_key=api_key())
    model = get("ai.model", "claude-sonnet-4-6")

    system = (
        "You are a personal planning assistant. "
        "Help the user reflect on their goals, tasks, and schedule. "
        "Be concise and actionable. "
        f"Current profile:\n{read_profile()}\n\nCurrent context:\n{read_context()}"
    )

    history = history + [{"role": "user", "content": user_message}]
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=history,
    )
    reply = _parse_sse_text(message) if isinstance(message, str) else message.content[0].text
    history = history + [{"role": "assistant", "content": reply}]
    return reply, history


_REVIEW_PROMPT_PATH = Path(__file__).parent / "prompts" / "review.txt"
_PLAN_PROMPT_PATH = Path(__file__).parent / "prompts" / "plan.txt"
_GOALS_PATH = Path(__file__).parent.parent / "data" / "goals.md"
_LAB_TASKS_PATH = Path(__file__).parent.parent / "data" / "lab_tasks.md"


def read_goals() -> str:
    if not _GOALS_PATH.exists():
        return ""
    return _GOALS_PATH.read_text(encoding="utf-8")


def read_lab_tasks() -> str:
    if not _LAB_TASKS_PATH.exists():
        return ""
    return _LAB_TASKS_PATH.read_text(encoding="utf-8")


def write_goals(content: str) -> None:
    _GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _GOALS_PATH.write_text(content, encoding="utf-8")


def run_review() -> str:
    """Generate/update goals.md from profile + context using the review prompt.

    Returns the new goals content.
    """
    from datetime import date
    today = date.today().isoformat()

    template = _REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{{PROFILE}}", read_profile())
        .replace("{{CONTEXT}}", read_context())
        .replace("{{GOALS}}", read_goals())
        .replace("{{LAB_TASKS}}", read_lab_tasks())
        .replace("{{TODAY}}", today)
    )

    response = call_claude(prompt)

    goals_match = re.search(r"<goals>(.*?)</goals>", response, re.DOTALL)
    context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)

    goals = goals_match.group(1).strip() if goals_match else response.strip()
    write_goals(goals)

    if context_match:
        write_context(context_match.group(1).strip())

    return goals


def run_plan() -> list[Task]:
    """Generate today's tasks from goals + context using the plan prompt.

    Adds new tasks to tasks.json and returns the full task list.
    """
    from datetime import date
    today = date.today().isoformat()

    tasks = load_tasks()
    open_tasks = [t for t in tasks if t.get("status") == "open"]

    template = _PLAN_PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{{PROFILE}}", read_profile())
        .replace("{{CONTEXT}}", read_context())
        .replace("{{GOALS}}", read_goals())
        .replace("{{LAB_TASKS}}", read_lab_tasks())
        .replace("{{TASKS_JSON}}", json.dumps(open_tasks, indent=2, ensure_ascii=False))
        .replace("{{TODAY}}", today)
    )

    response = call_claude(prompt)

    tasks_match = re.search(r"<tasks>(.*?)</tasks>", response, re.DOTALL)
    context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)

    if context_match:
        write_context(context_match.group(1).strip())

    new_tasks: list[dict] = []
    if tasks_match:
        try:
            new_tasks = json.loads(tasks_match.group(1).strip())
        except json.JSONDecodeError:
            new_tasks = []

    import uuid
    for t in new_tasks:
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": t.get("title", ""),
            "project": t.get("project"),
            "due": t.get("due"),
            "priority": t.get("priority", 1),
            "status": "open",
            "source": "local",
            "ticktick_id": None,
            "time_block": None,
        })

    save_tasks(tasks)
    return tasks
