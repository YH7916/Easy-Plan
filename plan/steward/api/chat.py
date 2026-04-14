from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Request

from plan.steward.api import steward_error

from plan.steward.contracts import (
    ChatActionDto,
    ChatActionExecutionDto,
    ChatSessionDto,
)

router = APIRouter(prefix="/chat")


def _current(request: Request):
    return request.app.state.container


def resolve_today(today_value: str | None = None) -> date:
    return date.fromisoformat(today_value) if today_value else date.today()


def build_chat_actions(
    session_id: str,
    request: Request,
    resolved_today: date,
) -> list[ChatActionDto]:
    actions: list[ChatActionDto] = []
    latest_task_candidate = _current(request).chat.latest_task_candidate(session_id)
    if latest_task_candidate and not _current(request).chat.latest_message_already_captured(session_id):
        actions.append(
            ChatActionDto(
                id="capture_latest_message_as_task",
                label="Capture Latest Request",
                description=(
                    f'Create a steward task in Planning from "{latest_task_candidate}".'
                ),
                target_module="planning",
            )
        )

    if (
        _current(request).notes.adapter is not None
        and _current(request).overview.get_daily_review_draft(resolved_today.isoformat()) is None
        and not _current(request).chat.has_review_draft(session_id, resolved_today.isoformat())
    ):
        actions.append(
            ChatActionDto(
                id="write_daily_review_draft",
                label="Write Today's Review Draft",
                description=(
                    "Generate today's unified review as an Obsidian draft without overwriting existing notes."
                ),
                target_module="notes",
            )
        )

    return actions


def build_chat_session(
    session: ChatSessionDto,
    request: Request,
    today_value: str | None = None,
) -> ChatSessionDto:
    resolved_today = resolve_today(today_value)
    overview = _current(request).overview.summary(today=resolved_today)
    automation = _current(request).automation.status(
        datetime.combine(
            resolved_today,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ),
        overview=overview,
    )
    prompts: list[str] = []
    if overview.pending_intake_count:
        prompts.append(
            f"Which of the {overview.pending_intake_count} pending source items should I accept into planning first?"
        )
    if overview.high_priority_open_count:
        prompts.append(
            f"Help me sequence my {overview.high_priority_open_count} high-priority tasks."
        )
    if not overview.has_daily_report:
        prompts.append("Help me capture today's daily review before I lose the context.")
    if automation.pending_interventions_count:
        prompts.append("Why is the steward asking for intervention right now?")
    generic_focus_prompt = "What should I focus on next?"
    prompts.append(generic_focus_prompt)

    deduped_prompts: list[str] = []
    for prompt in prompts:
        if prompt not in deduped_prompts:
            deduped_prompts.append(prompt)

    if len(deduped_prompts) > 4 and generic_focus_prompt in deduped_prompts:
        deduped_prompts = [
            *[prompt for prompt in deduped_prompts if prompt != generic_focus_prompt][:3],
            generic_focus_prompt,
        ]

    return ChatSessionDto(
        session_id=session.session_id,
        reply=session.reply,
        starter_prompts=deduped_prompts[:4],
        suggested_actions=build_chat_actions(
            session.session_id,
            request,
            resolved_today,
        ),
        history=session.history,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDto)
def chat_session(session_id: str, request: Request, today: str | None = None):
    session = _current(request).chat.get_session(session_id)
    return build_chat_session(session, request, today)


@router.post("/sessions/{session_id}/messages", response_model=ChatSessionDto)
def chat_send_message(session_id: str, payload: dict[str, Any], request: Request):
    session = _current(request).chat.send_message(session_id, payload["message"])
    _current(request).event_bus.publish(
        "chat.message_processed",
        {"session_id": session_id, "reply": session.reply},
    )
    return build_chat_session(session, request)


@router.post("/sessions/{session_id}/actions", response_model=ChatActionExecutionDto)
def chat_execute_action(session_id: str, payload: dict[str, Any], request: Request):
    action_id = payload["action_id"]
    resolved_today = resolve_today(payload.get("today"))
    available_actions = {
        action.id: action
        for action in build_chat_actions(session_id, request, resolved_today)
    }
    if action_id not in available_actions:
        raise steward_error(404, "not_found", f"Chat action not available: {action_id}")

    created_task = None
    note_draft = None

    if action_id == "capture_latest_message_as_task":
        title = _current(request).chat.latest_task_candidate(session_id)
        if not title:
            raise steward_error(400, "bad_request", "No actionable user message is available.")
        created_task = _current(request).planning.create_task(
            title=title,
            project="steward",
            priority=2,
            source="chat",
        )
        _current(request).chat.mark_latest_message_captured(session_id)
        summary = f'I added "{created_task.title}" to Planning.'
        _current(request).event_bus.publish("planning.task_created", created_task.model_dump())
    elif action_id == "write_daily_review_draft":
        note_draft = _current(request).overview.write_daily_review_draft(resolved_today.isoformat())
        _current(request).chat.mark_review_drafted(session_id, resolved_today.isoformat())
        summary = "I wrote today's daily review draft and queued it for Obsidian."
        _current(request).event_bus.publish(
            "notes.daily_review_draft_written",
            {
                "date": resolved_today.isoformat(),
                "path": str(note_draft.path),
                "obsidian_url": note_draft.obsidian_url,
            },
        )
    else:
        raise steward_error(400, "bad_request", f"Unsupported chat action: {action_id}")

    session = _current(request).chat.append_assistant_message(session_id, summary)
    _current(request).event_bus.publish(
        "chat.action_executed",
        {"session_id": session_id, "action_id": action_id, "summary": summary},
    )
    return ChatActionExecutionDto(
        summary=summary,
        session=build_chat_session(session, request, resolved_today.isoformat()),
        created_task=created_task,
        note_draft=note_draft,
    )
