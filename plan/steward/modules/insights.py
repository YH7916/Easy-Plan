from __future__ import annotations

from plan.steward.adapters.work_review import WorkReviewAdapter
from plan.steward.contracts import InsightReportDto, WeeklyReportDto
from plan.steward.modules.planning import PlanningService


class InsightsService:
    def __init__(
        self,
        work_review_adapter: WorkReviewAdapter,
        planning_service: PlanningService,
    ) -> None:
        self.work_review_adapter = work_review_adapter
        self.planning_service = planning_service

    def daily_report(self, report_date: str) -> InsightReportDto:
        snapshot = self.work_review_adapter.snapshot(report_date)
        tasks = self.planning_service.list_tasks()
        open_tasks = [task for task in tasks if task.status == "open"]
        top_apps: list[str] = []
        for activity in snapshot.recent_activities:
            if activity.app_name not in top_apps:
                top_apps.append(activity.app_name)
        sections = []
        if snapshot.daily_report is not None:
            sections.append(snapshot.daily_report.content.strip())
        if open_tasks:
            lines = "\n".join(f"- {task.title}" for task in open_tasks[:5])
            sections.append(f"## Unified Task Snapshot\n\nOpen tasks: {len(open_tasks)}\n{lines}")
        return InsightReportDto(
            date=report_date,
            summary_markdown="\n\n".join(section for section in sections if section),
            top_apps=top_apps,
            open_task_count=len(open_tasks),
        )

    def weekly_report(self, week_start: str) -> WeeklyReportDto:
        from datetime import date, timedelta
        from collections import Counter

        start = date.fromisoformat(week_start)
        start = start - timedelta(days=start.weekday())
        end = start + timedelta(days=6)

        daily_reports = []
        for i in range(7):
            day = (start + timedelta(days=i)).isoformat()
            try:
                report = self.daily_report(day)
                daily_reports.append(report)
            except Exception:
                pass

        all_apps: list[str] = []
        for r in daily_reports:
            all_apps.extend(r.top_apps)
        top_apps = [app for app, _ in Counter(all_apps).most_common(5)]

        lines = [f"# Weekly Report {start} – {end}\n"]
        for r in daily_reports:
            lines.append(f"## {r.date}\n{r.summary_markdown}\n")

        social_keywords = {"twitter", "weibo", "bilibili", "youtube", "tiktok", "instagram"}
        anomalies = []
        for r in daily_reports:
            if any(k in app.lower() for app in r.top_apps for k in social_keywords):
                anomalies.append(f"{r.date}: high social media usage detected")

        open_count = daily_reports[-1].open_task_count if daily_reports else 0

        return WeeklyReportDto(
            week_start=start.isoformat(),
            week_end=end.isoformat(),
            summary_markdown="\n".join(lines),
            top_apps=top_apps,
            daily_reports_count=len(daily_reports),
            open_task_count=open_count,
            focus_anomalies=anomalies,
        )

    def has_daily_report(self, report_date: str) -> bool:
        return self.work_review_adapter.snapshot(report_date).daily_report is not None

    def work_review_available(self) -> bool:
        return self.work_review_adapter.status().available
