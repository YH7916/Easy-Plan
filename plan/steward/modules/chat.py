from __future__ import annotations

from dataclasses import dataclass, field

from plan.agent import chat_turn
from plan.steward.contracts import ChatMessageDto, ChatSessionDto


@dataclass(slots=True)
class ChatSessionState:
    history: list[dict[str, str]] = field(default_factory=list)
    captured_user_index: int | None = None
    drafted_review_dates: set[str] = field(default_factory=set)


class ChatService:
    def __init__(self) -> None:
        self._sessions: dict[str, ChatSessionState] = {}

    def _session_state(self, session_id: str) -> ChatSessionState:
        return self._sessions.setdefault(session_id, ChatSessionState())

    def get_session(self, session_id: str) -> ChatSessionDto:
        history = self._session_state(session_id).history
        reply = ""
        for item in reversed(history):
            if item["role"] == "assistant":
                reply = item["content"]
                break
        return ChatSessionDto(
            session_id=session_id,
            reply=reply,
            history=[
                ChatMessageDto(role=item["role"], content=item["content"])
                for item in history
            ],
        )

    def send_message(self, session_id: str, message: str) -> ChatSessionDto:
        state = self._session_state(session_id)
        reply, updated_history = chat_turn(message, state.history)
        state.history = updated_history
        return ChatSessionDto(
            session_id=session_id,
            reply=reply,
            history=[
                ChatMessageDto(role=item["role"], content=item["content"])
                for item in updated_history
            ],
        )

    def append_assistant_message(self, session_id: str, content: str) -> ChatSessionDto:
        state = self._session_state(session_id)
        state.history.append({"role": "assistant", "content": content})
        return self.get_session(session_id)

    def latest_task_candidate(self, session_id: str) -> str | None:
        latest_message = self.latest_user_message(session_id)
        if latest_message is None:
            return None

        text = " ".join(latest_message.split()).strip().strip(".!, ")
        if len(text) < 5:
            return None

        lower = text.lower()
        if "?" in text or lower.startswith(
            (
                "what ",
                "why ",
                "how ",
                "when ",
                "where ",
                "who ",
                "should ",
                "can ",
                "could ",
                "would ",
                "do ",
                "does ",
                "did ",
                "is ",
                "are ",
                "am ",
                "will ",
            )
        ):
            return None

        for prefix in (
            "please ",
            "help me ",
            "can you ",
            "could you ",
            "i need to ",
            "need to ",
            "let's ",
            "lets ",
        ):
            if lower.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        if not text:
            return None
        text = text[0].upper() + text[1:]
        return text[:80].rstrip()

    def latest_user_message(self, session_id: str) -> str | None:
        state = self._session_state(session_id)
        for item in reversed(state.history):
            if item["role"] == "user":
                return item["content"]
        return None

    def latest_user_index(self, session_id: str) -> int | None:
        state = self._session_state(session_id)
        for index in range(len(state.history) - 1, -1, -1):
            if state.history[index]["role"] == "user":
                return index
        return None

    def latest_message_already_captured(self, session_id: str) -> bool:
        state = self._session_state(session_id)
        return (
            state.captured_user_index is not None
            and state.captured_user_index == self.latest_user_index(session_id)
        )

    def mark_latest_message_captured(self, session_id: str) -> None:
        state = self._session_state(session_id)
        state.captured_user_index = self.latest_user_index(session_id)

    def has_review_draft(self, session_id: str, report_date: str) -> bool:
        return report_date in self._session_state(session_id).drafted_review_dates

    def mark_review_drafted(self, session_id: str, report_date: str) -> None:
        self._session_state(session_id).drafted_review_dates.add(report_date)
