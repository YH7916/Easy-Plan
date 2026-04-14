from __future__ import annotations

from datetime import date

from plan.steward.contracts import (
    AppOverviewDto,
    NoteDraftDto,
    OverviewActionDto,
    OverviewActionExecutionDto,
)
from plan.steward.modules.insights import InsightsService
from plan.steward.modules.notes import NotesService
from plan.steward.modules.planning import PlanningService
from plan.steward.modules.sources import SourcesService


class OverviewService:
    def __init__(
        self,
        planning_service: PlanningService,
        sources_service: SourcesService,
        insights_service: InsightsService,
        notes_service: NotesService,
    ) -> None:
        self.planning_service = planning_service
        self.sources_service = sources_service
        self.insights_service = insights_service
        self.notes_service = notes_service

    def summary(self, today: date | None = None) -> AppOverviewDto:
        current_day = today or date.today()
        current_date = current_day.isoformat()
        notes = self.notes_service.index(limit=20)
        tasks = self.planning_service.list_tasks()
        source_dashboard = self.sources_service.dashboard(tasks, today=current_day)
        source_suggestions = self.planning_service.list_suggestions(self.sources_service.list_items())
        has_report = self.insights_service.has_daily_report(current_date)
        report = self.insights_service.daily_report(current_date)
        high_priority_open_count = sum(
            1 for task in tasks if task.status == "open" and task.priority >= 3
        )
        alerts = []
        if self.insights_service.work_review_available():
            alerts.append("Work review data available")
        if high_priority_open_count:
            alerts.append("High-priority tasks need review")
        if source_dashboard.pending_intake_count:
            alerts.append(f"{source_dashboard.pending_intake_count} source items are waiting for intake")
        if source_dashboard.overdue_count:
            alerts.append(f"{source_dashboard.overdue_count} source items are overdue")

        recommended_next_actions, recommended_actions = self._recommended_actions(
            current_day,
            pending_intake_count=source_dashboard.pending_intake_count,
            due_soon_count=source_dashboard.due_soon_count,
            overdue_count=source_dashboard.overdue_count,
            high_priority_open_count=high_priority_open_count,
            has_report=has_report,
            source_suggestions=source_suggestions,
        )

        daily_brief = (
            f"{sum(1 for task in tasks if task.status == 'open')} open tasks, "
            f"{source_dashboard.pending_intake_count} pending intake items, "
            f"{source_dashboard.due_soon_count} due soon source items."
        )
        return AppOverviewDto(
            open_task_count=sum(1 for task in tasks if task.status == "open"),
            high_priority_open_count=high_priority_open_count,
            source_item_count=source_dashboard.total_count,
            pending_intake_count=source_dashboard.pending_intake_count,
            due_soon_source_count=source_dashboard.due_soon_count,
            overdue_source_count=source_dashboard.overdue_count,
            notes_indexed_count=len(notes),
            has_daily_report=has_report,
            active_alerts=alerts,
            daily_brief=daily_brief,
            focus_apps=report.top_apps[:5],
            recommended_next_actions=recommended_next_actions,
            recommended_actions=recommended_actions,
        )

    @staticmethod
    def daily_review_title(report_date: str) -> str:
        return f"Plan Steward Daily Review {report_date}"

    def get_daily_review_draft(self, report_date: str) -> NoteDraftDto | None:
        return self.notes_service.find_daily_draft(
            report_date,
            self.daily_review_title(report_date),
        )

    def execute_action(
        self,
        action_id: str,
        today: date | None = None,
    ) -> OverviewActionExecutionDto:
        current_day = today or date.today()
        actions = {
            action.id: action
            for action in self.summary(today=current_day).recommended_actions
        }
        action = actions.get(action_id)
        if action is None:
            raise KeyError(action_id)
        if not action.can_execute:
            raise PermissionError(action_id)

        if action_id == "review_intake_queue":
            suggestion = self._top_suggestion(self.planning_service.list_suggestions(self.sources_service.list_items()))
            if suggestion is None:
                raise KeyError(action_id)
            task = self.planning_service.accept_suggestion(suggestion)
            return OverviewActionExecutionDto(
                summary=f'Accepted "{task.title}" into Planning.',
                target_page="planning",
                created_task=task,
            )

        if action_id == "capture_daily_review":
            note = self.write_daily_review_draft(current_day.isoformat())
            return OverviewActionExecutionDto(
                summary=f"Daily review draft written for {current_day.isoformat()}.",
                target_page="insights",
                note_draft=note,
            )

        raise KeyError(action_id)

    def _recommended_actions(
        self,
        current_day: date,
        *,
        pending_intake_count: int,
        due_soon_count: int,
        overdue_count: int,
        high_priority_open_count: int,
        has_report: bool,
        source_suggestions: list,
    ) -> tuple[list[str], list[OverviewActionDto]]:
        recommended_next_actions: list[str] = []
        recommended_actions: list[OverviewActionDto] = []
        top_suggestion = self._top_suggestion(source_suggestions)
        existing_daily_review = self.get_daily_review_draft(current_day.isoformat())

        if pending_intake_count:
            recommended_next_actions.append(
                f"Review {pending_intake_count} pending source items and accept the ones that should enter planning."
            )
            recommended_actions.append(
                OverviewActionDto(
                    id="review_intake_queue",
                    label="Review Intake Queue",
                    description=(
                        "Open Planning to decide which incoming source items should enter the steward task pool."
                    ),
                    target_page="planning",
                    can_execute=top_suggestion is not None,
                    execute_label="Accept Top Item" if top_suggestion is not None else None,
                )
            )
        if overdue_count:
            recommended_next_actions.append(
                f"Resolve {overdue_count} overdue source items before they slip further."
            )
            recommended_actions.append(
                OverviewActionDto(
                    id="resolve_overdue_sources",
                    label="Resolve Overdue Sources",
                    description=(
                        "Open Planning to triage overdue source work before it slips further."
                    ),
                    target_page="planning",
                )
            )
        elif due_soon_count:
            recommended_next_actions.append(
                f"Schedule the {due_soon_count} source items due soon before they become urgent."
            )
            recommended_actions.append(
                OverviewActionDto(
                    id="plan_due_soon_work",
                    label="Plan Due-Soon Work",
                    description=(
                        "Open Chat with a steward prompt to sequence the source work that is approaching its deadline."
                    ),
                    target_page="chat",
                    chat_prompt=(
                        f"Help me schedule the {due_soon_count} source items due soon before they become urgent."
                    ),
                )
            )
        if high_priority_open_count:
            recommended_next_actions.append(
                f"Advance {high_priority_open_count} high-priority tasks already in the unified task pool."
            )
            recommended_actions.append(
                OverviewActionDto(
                    id="sequence_high_priority_tasks",
                    label="Sequence High-Priority Work",
                    description=(
                        "Open Chat with a steward prompt to choose the next high-priority task to execute."
                    ),
                    target_page="chat",
                    chat_prompt=(
                        f"Help me sequence my {high_priority_open_count} high-priority tasks and choose the next one to execute."
                    ),
                )
            )
        if not has_report:
            if self.notes_service.adapter is None:
                recommended_next_actions.append(
                    "Configure Obsidian output so the steward can write daily reviews and notes drafts."
                )
                recommended_actions.append(
                    OverviewActionDto(
                        id="configure_notes_output",
                        label="Configure Obsidian Output",
                        description=(
                            "Open Settings to connect an Obsidian vault before generating steward drafts."
                        ),
                        target_page="settings",
                    )
                )
            elif existing_daily_review is not None:
                recommended_next_actions.append(
                    "Today's daily review draft already exists. Open Notes to review it or jump back into Obsidian."
                )
                recommended_actions.append(
                    OverviewActionDto(
                        id="open_daily_review_draft",
                        label="Open Today's Draft",
                        description=(
                            "Open Notes to review the existing daily review draft instead of generating a duplicate."
                        ),
                        target_page="notes",
                    )
                )
            else:
                recommended_next_actions.append(
                    "Generate or review today's insight summary so the steward has fresh context."
                )
                recommended_actions.append(
                    OverviewActionDto(
                        id="capture_daily_review",
                        label="Capture Daily Review",
                        description=(
                            "Generate today's unified review draft now, then continue in Insights if you want to inspect the full report."
                        ),
                        target_page="insights",
                        can_execute=True,
                        execute_label="Write Draft",
                    )
                )
        if not recommended_next_actions:
            recommended_next_actions.append(
                "No immediate friction detected. Continue the current plan and keep the steward updated."
            )
            recommended_actions.append(
                OverviewActionDto(
                    id="check_in_with_steward",
                    label="Check In With Steward",
                    description=(
                        "Open Chat to reflect on progress and keep the steward context fresh."
                    ),
                    target_page="chat",
                    chat_prompt="Help me review my current progress and decide what to focus on next.",
                )
            )

        return recommended_next_actions, recommended_actions

    @staticmethod
    def _top_suggestion(source_suggestions):
        if not source_suggestions:
            return None

        def sort_key(suggestion):
            due = suggestion.due or "9999-12-31"
            return (due, -suggestion.priority, suggestion.title.lower())

        return sorted(source_suggestions, key=sort_key)[0]

    def write_daily_review_draft(self, report_date: str) -> NoteDraftDto:
        report = self.insights_service.daily_report(report_date)
        title = self.daily_review_title(report_date)
        top_apps = ", ".join(report.top_apps[:5]) if report.top_apps else "No dominant apps captured"
        sections = [
            f"# {title}",
            "",
            "_Generated by Plan Steward. Review and refine in Obsidian._",
            "",
            "## At a Glance",
            "",
            f"- Date: {report.date}",
            f"- Open tasks in steward pool: {report.open_task_count}",
            f"- Focus apps: {top_apps}",
            "",
            "## Unified Review",
            "",
            report.summary_markdown.strip() or "No unified report was available for this date.",
        ]
        return self.notes_service.write_daily_draft(
            date=report_date,
            title=title,
            content="\n".join(sections).strip() + "\n",
        )
