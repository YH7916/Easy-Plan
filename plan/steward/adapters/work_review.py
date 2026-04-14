from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class WorkReviewStatus:
    available: bool
    db_path: Path
    config_path: Path


@dataclass(slots=True)
class WorkReviewActivity:
    app_name: str
    window_title: str
    duration: int
    browser_url: str | None
    semantic_category: str | None


@dataclass(slots=True)
class WorkReviewHourlySummary:
    date: str
    hour: int
    summary: str
    main_apps: str
    total_duration: int
    representative_screenshots: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkReviewDailyReport:
    date: str
    locale: str
    content: str


@dataclass(slots=True)
class WorkReviewSnapshot:
    status: WorkReviewStatus
    recent_activities: list[WorkReviewActivity]
    hourly_summaries: list[WorkReviewHourlySummary]
    daily_report: WorkReviewDailyReport | None


class WorkReviewAdapter:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.db_path = self.root / "workreview.db"
        self.config_path = self.root / "config.json"

    def status(self) -> WorkReviewStatus:
        return WorkReviewStatus(
            available=self.db_path.exists(),
            db_path=self.db_path,
            config_path=self.config_path,
        )

    def availability(self) -> dict[str, str | None]:
        """Returns {"status": "available"|"degraded", "reason": str|None}"""
        if not self.db_path.exists():
            return {"status": "degraded", "reason": f"Database not found: {self.db_path}"}
        return {"status": "available", "reason": None}

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def snapshot(self, report_date: str, activity_limit: int = 20) -> WorkReviewSnapshot:
        status = self.status()
        if not status.available:
            return WorkReviewSnapshot(status=status, recent_activities=[], hourly_summaries=[], daily_report=None)

        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT app_name, window_title, duration, browser_url, semantic_category
                FROM activities
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (activity_limit,),
            )
            activities = [
                WorkReviewActivity(
                    app_name=row["app_name"],
                    window_title=row["window_title"],
                    duration=row["duration"],
                    browser_url=row["browser_url"],
                    semantic_category=row["semantic_category"],
                )
                for row in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT date, hour, summary, main_apps, total_duration, representative_screenshots
                FROM hourly_summaries
                WHERE date = ?
                ORDER BY hour DESC
                """,
                (report_date,),
            )
            hourly = [
                WorkReviewHourlySummary(
                    date=row["date"],
                    hour=row["hour"],
                    summary=row["summary"],
                    main_apps=row["main_apps"],
                    total_duration=row["total_duration"],
                    representative_screenshots=json.loads(row["representative_screenshots"] or "[]"),
                )
                for row in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT date, locale, content
                FROM daily_reports_localized
                WHERE date = ?
                ORDER BY locale = 'zh-CN' DESC, created_at DESC
                LIMIT 1
                """,
                (report_date,),
            )
            row = cursor.fetchone()
            report = None
            if row is not None:
                report = WorkReviewDailyReport(
                    date=row["date"],
                    locale=row["locale"],
                    content=row["content"],
                )
            return WorkReviewSnapshot(
                status=status,
                recent_activities=activities,
                hourly_summaries=hourly,
                daily_report=report,
            )
        finally:
            connection.close()

