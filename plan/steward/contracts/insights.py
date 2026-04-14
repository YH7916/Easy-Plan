from __future__ import annotations

from pydantic import BaseModel


class InsightReportDto(BaseModel):
    date: str
    summary_markdown: str
    top_apps: list[str]
    open_task_count: int


class WeeklyReportDto(BaseModel):
    week_start: str
    week_end: str
    summary_markdown: str
    top_apps: list[str]
    daily_reports_count: int
    open_task_count: int
    focus_anomalies: list[str]
