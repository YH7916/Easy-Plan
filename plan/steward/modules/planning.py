from __future__ import annotations

from datetime import date

from plan.steward.contracts import SourceItemDto, TaskDto, TaskSuggestionDto, TimeBlockDto, TodayQueueDto
from plan.tasks import add_task, list_tasks, load_tasks, mark_done, save_tasks, update_task

# Allowed status transitions (state machine)
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "open":        {"in_progress", "blocked", "done"},
    "in_progress": {"open", "blocked", "done"},
    "blocked":     {"open", "in_progress"},
    "done":        set(),  # terminal state
}

VALID_STATUSES = {"open", "in_progress", "blocked", "done"}


class PlanningService:
    def list_tasks(self) -> list[TaskDto]:
        return [TaskDto.model_validate(task) for task in list_tasks(status=None)]

    def create_task(
        self,
        title: str,
        project: str | None = None,
        due: str | None = None,
        priority: int = 0,
        source: str = "local",
        external_id: str | None = None,
    ) -> TaskDto:
        task = add_task(
            title,
            project=project,
            due=due,
            priority=priority,
            source=source,
            ticktick_id=external_id,
        )
        return TaskDto.model_validate(task)

    def transition_task(self, task_id: str, new_status: str) -> TaskDto:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status!r}. Must be one of {sorted(VALID_STATUSES)}")

        tasks = load_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task is None:
            raise KeyError(task_id)

        allowed = _VALID_TRANSITIONS.get(task.get("status", "open"), set())
        if new_status not in allowed:
            raise PermissionError(
                f"Cannot transition task from {task.get('status')!r} to {new_status!r}. "
                f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}"
            )

        task["status"] = new_status
        save_tasks(tasks)
        return TaskDto.model_validate(task)

    def complete_task(self, task_id: str) -> TaskDto:
        return self.transition_task(task_id, "done")

    def open_task_count(self) -> int:
        return len(list_tasks(status="open"))

    def today_queue(self, today: date | None = None) -> TodayQueueDto:
        resolved = today or date.today()
        open_tasks = [t for t in self.list_tasks() if t.status == "open"]
        prioritized = sorted(open_tasks, key=lambda t: t.priority, reverse=True)[:5]

        time_blocks = []
        start_hour, start_min = 9, 0
        for task in prioritized:
            end_hour = start_hour + 1
            end_min = start_min + 30
            if end_min >= 60:
                end_hour += 1
                end_min -= 60
            time_blocks.append(TimeBlockDto(
                start_time=f"{start_hour:02d}:{start_min:02d}",
                end_time=f"{end_hour:02d}:{end_min:02d}",
                task_id=task.id,
                task_title=task.title,
                estimated_minutes=90,
            ))
            start_hour = end_hour
            start_min = end_min

        return TodayQueueDto(
            date=resolved.isoformat(),
            tasks=prioritized,
            time_blocks=time_blocks,
            total_estimated_minutes=len(prioritized) * 90,
        )

    def list_suggestions(self, source_items: list[SourceItemDto]) -> list[TaskSuggestionDto]:
        tracked_tasks = self.list_tasks()
        suggestions: list[TaskSuggestionDto] = []
        for item in source_items:
            if self._is_tracked(item, tracked_tasks):
                continue
            suggestions.append(
                TaskSuggestionDto(
                    title=item.title,
                    source=item.source,
                    due=item.due,
                    project=item.project,
                    priority=item.priority,
                    external_id=item.external_id,
                    reason=(
                        f"Source item from {item.source} is not yet tracked in the unified task pool."
                    ),
                )
            )
        return suggestions

    def accept_suggestion(self, suggestion: TaskSuggestionDto) -> TaskDto:
        tracked_tasks = self.list_tasks()
        for task in tracked_tasks:
            if self._matches_task(
                task,
                suggestion.title,
                suggestion.project,
                suggestion.due,
                suggestion.external_id,
            ):
                return task
        return self.create_task(
            title=suggestion.title,
            project=suggestion.project,
            due=suggestion.due,
            priority=suggestion.priority,
            source=suggestion.source,
            external_id=suggestion.external_id,
        )

    @staticmethod
    def _is_tracked(item: SourceItemDto, tracked_tasks: list[TaskDto]) -> bool:
        return any(
            PlanningService._matches_task(
                task,
                item.title,
                item.project,
                item.due,
                item.external_id,
            )
            for task in tracked_tasks
        )

    @staticmethod
    def _matches_task(
        task: TaskDto,
        title: str,
        project: str | None,
        due: str | None,
        external_id: str | None,
    ) -> bool:
        if external_id and task.ticktick_id == external_id:
            return True
        return task.title == title and task.project == project and task.due == due
