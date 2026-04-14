from __future__ import annotations

from fastapi import APIRouter, Request
from plan.steward.contracts import WeeklyReportDto

router = APIRouter(prefix="/insights")


def _current(request: Request):
    return request.app.state.container


@router.get("/reports/daily")
def insights_daily_report(date: str, request: Request):
    report = _current(request).insights.daily_report(date)
    _current(request).event_bus.publish(
        "insights.report_generated",
        {"date": date, "top_apps": report.top_apps},
    )
    return report


@router.get("/reports/weekly", response_model=WeeklyReportDto)
def insights_weekly_report(week_start: str, request: Request):
    return _current(request).insights.weekly_report(week_start)
