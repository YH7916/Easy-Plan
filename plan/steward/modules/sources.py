from __future__ import annotations

from datetime import date

from plan.steward.adapters.lazy_zju import LazyZjuAdapter
from plan.steward.contracts import SourceDashboardItemDto, SourceItemDto, SourcesDashboardDto, TaskDto


class SourcesService:
    def __init__(self, lazy_adapter: LazyZjuAdapter) -> None:
        self.lazy_adapter = lazy_adapter

    def list_items(self) -> list[SourceItemDto]:
        return self.lazy_adapter.fetch_items()

    def dashboard(
        self,
        tasks: list[TaskDto],
        today: date | None = None,
    ) -> SourcesDashboardDto:
        current_date = today or date.today()
        items = [
            self._build_dashboard_item(item, tasks, current_date)
            for item in self.list_items()
        ]
        return SourcesDashboardDto(
            total_count=len(items),
            tracked_count=sum(1 for item in items if item.tracking_status == "tracked"),
            pending_intake_count=sum(
                1 for item in items if item.tracking_status == "pending_intake"
            ),
            due_soon_count=sum(1 for item in items if item.urgency == "due_soon"),
            overdue_count=sum(1 for item in items if item.urgency == "overdue"),
            items=items,
        )

    @staticmethod
    def _build_dashboard_item(
        item: SourceItemDto,
        tasks: list[TaskDto],
        today: date,
    ) -> SourceDashboardItemDto:
        tracked_task = SourcesService._find_task(item, tasks)
        tracking_status = "tracked" if tracked_task is not None else "pending_intake"
        urgency = SourcesService._urgency(item.due, today)
        recommendation = (
            "Already tracked in planning."
            if tracked_task is not None
            else "Accept into planning to turn this source item into steward-managed work."
        )
        return SourceDashboardItemDto(
            title=item.title,
            source=item.source,
            due=item.due,
            project=item.project,
            priority=item.priority,
            external_id=item.external_id,
            tracking_status=tracking_status,
            urgency=urgency,
            tracked_task_id=tracked_task.id if tracked_task is not None else None,
            tracked_task_status=tracked_task.status if tracked_task is not None else None,
            recommendation=recommendation,
        )

    @staticmethod
    def _find_task(item: SourceItemDto, tasks: list[TaskDto]) -> TaskDto | None:
        for task in tasks:
            if item.external_id and task.ticktick_id == item.external_id:
                return task
            if task.title == item.title and task.project == item.project and task.due == item.due:
                return task
        return None

    @staticmethod
    def _urgency(due: str | None, today: date) -> str:
        if due is None:
            return "unscheduled"
        due_date = date.fromisoformat(due)
        delta_days = (due_date - today).days
        if delta_days < 0:
            return "overdue"
        if delta_days <= 2:
            return "due_soon"
        return "upcoming"
