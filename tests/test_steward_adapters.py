import json
import sqlite3
from pathlib import Path


def _create_work_review_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY,
            timestamp INTEGER,
            app_name TEXT,
            window_title TEXT,
            screenshot_path TEXT,
            ocr_text TEXT,
            category TEXT,
            duration INTEGER,
            browser_url TEXT,
            executable_path TEXT,
            semantic_category TEXT,
            semantic_confidence INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE hourly_summaries (
            id INTEGER PRIMARY KEY,
            date TEXT,
            hour INTEGER,
            summary TEXT,
            main_apps TEXT,
            activity_count INTEGER,
            total_duration INTEGER,
            representative_screenshots TEXT,
            created_at INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE daily_reports_localized (
            date TEXT,
            locale TEXT,
            content TEXT,
            ai_mode TEXT,
            model_name TEXT,
            created_at INTEGER
        )
        """
    )
    cur.execute(
        """
        INSERT INTO activities
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            1776000000,
            "VS Code",
            "Plan Steward",
            "screenshots\\2026-04-13\\090000.jpg",
            "editing plan",
            "developer",
            1800,
            None,
            r"C:\\Program Files\\Microsoft VS Code\\Code.exe",
            "编码开发",
            82,
        ),
    )
    cur.execute(
        """
        INSERT INTO hourly_summaries
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "2026-04-13",
            9,
            "Focused coding on the steward backend.",
            "VS Code, Codex",
            6,
            1800,
            json.dumps(["screenshots\\2026-04-13\\090000.jpg"]),
            1776003600,
        ),
    )
    cur.execute(
        """
        INSERT INTO daily_reports_localized
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-04-13",
            "zh-CN",
            "# 工作日报\n\n今天主要在实现后端。",
            "local",
            "qwen2.5",
            1776074423,
        ),
    )
    conn.commit()
    conn.close()


def test_work_review_adapter_reads_recent_activity_and_daily_report(tmp_path):
    root = tmp_path / "work-review"
    root.mkdir()
    _create_work_review_db(root / "workreview.db")
    (root / "config.json").write_text(
        json.dumps({"screenshot_interval": 30, "theme": "system"}, ensure_ascii=False),
        encoding="utf-8",
    )

    from plan.steward.adapters.work_review import WorkReviewAdapter

    adapter = WorkReviewAdapter(root)
    snapshot = adapter.snapshot("2026-04-13", activity_limit=5)

    assert snapshot.status.available is True
    assert snapshot.recent_activities[0].app_name == "VS Code"
    assert snapshot.hourly_summaries[0].hour == 9
    assert "今天主要在实现后端" in snapshot.daily_report.content


def test_obsidian_adapter_indexes_notes_and_writes_generated_summary(tmp_path):
    vault = tmp_path / "vault"
    note_dir = vault / "Projects"
    note_dir.mkdir(parents=True)
    (note_dir / "Plan Steward.md").write_text(
        "# Plan Steward\n\nA backend-first desktop steward.\n",
        encoding="utf-8",
    )

    from plan.steward.adapters.obsidian import ObsidianAdapter

    adapter = ObsidianAdapter(vault_root=vault, generated_dir=Path("Steward/Daily"))
    indexed = adapter.index_notes(limit=10)
    written = adapter.write_generated_note(
        note_type="daily",
        note_date="2026-04-13",
        title="Plan Steward Daily Summary",
        content="# Plan Steward Daily Summary\n\nShipped the first backend endpoints.\n",
    )
    dashboard = adapter.dashboard(limit_recent=10, limit_generated=10)

    assert indexed[0].title == "Plan Steward"
    assert indexed[0].obsidian_url.startswith("obsidian://open")
    assert written.path.exists()
    assert "Shipped the first backend endpoints." in written.path.read_text(encoding="utf-8")
    assert dashboard.vault_ready is True
    assert dashboard.indexed_count == 2
    assert dashboard.generated_count == 1
    assert dashboard.generated_notes[0].title == "Plan Steward Daily Summary"


def test_lazy_zju_adapter_normalizes_source_items(monkeypatch):
    from plan.sources import SourceItem
    from plan.steward.adapters.lazy_zju import LazyZjuAdapter

    class FakeSource:
        name = "lazy_zju"

        def fetch(self):
            return [
                SourceItem(
                    title="Lab 3",
                    source="lazy_zju",
                    project="courses",
                    priority=2,
                    external_id="assignment_42",
                )
            ]

    adapter = LazyZjuAdapter(lambda: [FakeSource()])
    items = adapter.fetch_items()

    assert len(items) == 1
    assert items[0].source == "lazy_zju"
    assert items[0].external_id == "assignment_42"
    assert items[0].title == "Lab 3"
