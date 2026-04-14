from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from plan.steward.contracts import (
    AppOverviewDto,
    AutomationSignalDto,
    AutomationStatusDto,
    GuardrailsDto,
    InterventionRecordDto,
)


@dataclass(slots=True)
class _AutomationContext:
    new_source_items: int = 0
    backlog_pressure: bool = False
    focus_drift: bool = False
    last_check_in: datetime | None = None


class AutomationService:
    def __init__(
        self,
        check_in_hours: int = 2,
        history_path: Path | None = None,
    ) -> None:
        self.check_in_hours = check_in_hours
        self.guardrails = GuardrailsDto()
        self._history_path = history_path
        self._history: list[InterventionRecordDto] = []
        if history_path is not None:
            self._load_history()

    def _load_history(self) -> None:
        if self._history_path is None or not self._history_path.exists():
            return
        try:
            raw = json.loads(self._history_path.read_text(encoding="utf-8"))
            self._history = [InterventionRecordDto.model_validate(r) for r in raw]
        except Exception:
            self._history = []

    def _save_history(self) -> None:
        if self._history_path is None:
            return
        records = self._history[-50:]
        self._history_path.write_text(
            json.dumps([r.model_dump() for r in records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_intervention(
        self, signals: list[AutomationSignalDto], now: datetime
    ) -> None:
        record = InterventionRecordDto(
            timestamp=now.isoformat(),
            signals=signals,
            pending_count=len(signals),
        )
        self._history.append(record)
        self._save_history()

    def recent_history(self, limit: int = 10) -> list[InterventionRecordDto]:
        return self._history[-limit:]

    def evaluate_signals(
        self,
        now: datetime,
        new_source_items: int = 0,
        backlog_pressure: bool = False,
        focus_drift: bool = False,
        review_gap: bool = False,
        last_check_in: datetime | None = None,
    ) -> list[AutomationSignalDto]:
        signals: list[AutomationSignalDto] = []
        last = last_check_in
        if last is None or now - last >= timedelta(hours=self.check_in_hours):
            signals.append(
                AutomationSignalDto(
                    kind="scheduled_check_in",
                    summary=f"Fixed check-in due every {self.check_in_hours} hours.",
                    guardrails=self.guardrails,
                )
            )
        if new_source_items:
            signals.append(
                AutomationSignalDto(
                    kind="new_source_items",
                    summary=f"{new_source_items} new source items need triage.",
                    guardrails=self.guardrails,
                )
            )
        if backlog_pressure:
            signals.append(
                AutomationSignalDto(
                    kind="backlog_pressure",
                    summary="The task backlog needs a steward re-prioritization pass.",
                    guardrails=self.guardrails,
                )
            )
        if review_gap:
            signals.append(
                AutomationSignalDto(
                    kind="review_gap",
                    summary="Today's unified review is missing and should be refreshed.",
                    guardrails=self.guardrails,
                )
            )
        if focus_drift:
            signals.append(
                AutomationSignalDto(
                    kind="focus_drift",
                    summary="Recent activity suggests focus drift from the active plan.",
                    guardrails=self.guardrails,
                )
            )
        return signals

    def status(
        self,
        now: datetime,
        overview: AppOverviewDto | None = None,
    ) -> AutomationStatusDto:
        now = now.astimezone(timezone.utc)
        pending_source_items = overview.pending_intake_count if overview is not None else 0
        backlog_pressure = False
        review_gap = False
        if overview is not None:
            backlog_pressure = (
                overview.high_priority_open_count > 0
                or overview.overdue_source_count > 0
                or overview.open_task_count >= 12
            )
            review_gap = not overview.has_daily_report

        signals = self.evaluate_signals(
            now=now,
            new_source_items=pending_source_items,
            backlog_pressure=backlog_pressure,
            review_gap=review_gap,
        )
        if signals:
            self.record_intervention(signals, now)
        last_run_at = self._history[-1].timestamp if self._history else None
        return AutomationStatusDto(
            check_in_hours=self.check_in_hours,
            mode_summary=(
                "Active steward mode is monitoring intake pressure, backlog pressure, "
                f"and review gaps on a {self.check_in_hours}-hour cadence."
            ),
            pending_interventions_count=len(signals),
            guardrails=self.guardrails,
            signals=signals,
            last_run_at=last_run_at,
        )


class AutomationRunner:
    """Background asyncio task that periodically evaluates automation signals."""

    def __init__(
        self,
        automation: AutomationService,
        event_bus,  # EventBus
        interval_seconds: int = 300,
    ) -> None:
        self._automation = automation
        self._event_bus = event_bus
        self._interval = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:
                pass  # never crash the runner
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        status = self._automation.status(now, overview=None)
        if status.signals:
            self._event_bus.publish(
                "automation.runner_tick",
                {
                    "signal_count": len(status.signals),
                    "signals": [s.kind for s in status.signals],
                    "timestamp": now.isoformat(),
                },
            )
