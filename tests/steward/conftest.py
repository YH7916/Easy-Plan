import json
import sqlite3
from pathlib import Path

import pytest


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


@pytest.fixture()
def steward_env(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    profile_file = data_dir / "profile.md"
    context_file = data_dir / "context.md"
    tasks_file = data_dir / "tasks.json"
    profile_file.write_text("# Profile\nBuilder.", encoding="utf-8")
    context_file.write_text("# Context\nNeed a steward.", encoding="utf-8")
    tasks_file.write_text(
        json.dumps(
            [
                {
                    "id": "task-1",
                    "title": "Finish backend host",
                    "project": "plan-steward",
                    "due": "2026-04-14",
                    "priority": 3,
                    "status": "open",
                    "source": "local",
                    "ticktick_id": None,
                    "time_block": None,
                }
            ]
        ),
        encoding="utf-8",
    )

    work_review_root = tmp_path / "work-review"
    work_review_root.mkdir()
    _create_work_review_db(work_review_root / "workreview.db")
    (work_review_root / "config.json").write_text(
        json.dumps({"theme": "system"}, ensure_ascii=False),
        encoding="utf-8",
    )

    vault_root = tmp_path / "detected-vault"
    (vault_root / "Inbox").mkdir(parents=True)
    (vault_root / "Inbox" / "Existing Note.md").write_text(
        "# Existing Note\n\nKeep editing in Obsidian.\n",
        encoding="utf-8",
    )

    import plan.config as cfg
    cfg._cache = None
    original_resolve = cfg.resolve_path

    def fake_resolve(key):
        mapping = {
            "profile": profile_file,
            "context": context_file,
            "tasks": tasks_file,
        }
        return mapping.get(key, original_resolve(key))

    monkeypatch.setattr(cfg, "resolve_path", fake_resolve)
    import plan.memory as mem_mod
    monkeypatch.setattr(mem_mod, "resolve_path", fake_resolve)

    from plan.steward.config import StewardSettings

    settings = StewardSettings(
        backend_url="http://127.0.0.1:8765",
        work_review_root=work_review_root,
        obsidian_vault_root=vault_root,
        obsidian_generated_dir=Path("Steward/Daily"),
        automation_check_in_hours=2,
    )
    return settings, tasks_file, vault_root
