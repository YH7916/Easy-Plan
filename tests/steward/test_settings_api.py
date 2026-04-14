import json
import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

from tests.steward.conftest import _create_work_review_db


def test_settings_config_round_trip_hot_reloads_adapters(monkeypatch, steward_env, tmp_path):
    _, _, vault_root = steward_env

    import plan.config as cfg
    from plan.steward.config import StewardSettings
    from plan.steward.host import create_app

    work_review_root = tmp_path / "work-review-live"
    work_review_root.mkdir()
    _create_work_review_db(work_review_root / "workreview.db")
    (work_review_root / "config.json").write_text(
        json.dumps({"theme": "system"}, ensure_ascii=False),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[ai]",
                'provider = "claude"',
                'model = "claude-sonnet-4-6"',
                'api_key_env = "ANTHROPIC_API_KEY"',
                "",
                "[schedule]",
                'daily_time = "08:00"',
                "enabled = true",
                "run_on_missed = true",
                "",
                "[paths]",
                'profile = "data/profile.md"',
                'context = "data/context.md"',
                'tasks = "data/tasks.json"',
                "",
                "[steward]",
                'backend_url = "http://127.0.0.1:8765"',
                'host = "127.0.0.1"',
                "port = 8765",
                "",
                "[steward.adapters.work_review]",
                f"root = '{work_review_root}'",
                "",
                "[steward.adapters.obsidian]",
                'vault_root = ""',
                'generated_dir = "Steward/Daily"',
                "",
                "[steward.automation]",
                "check_in_hours = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(cfg, "_CONFIG_PATH", config_path)
    cfg._cache = None

    settings = StewardSettings(
        backend_url="http://127.0.0.1:8765",
        work_review_root=work_review_root,
        obsidian_vault_root=None,
        obsidian_generated_dir=Path("Steward/Daily"),
        automation_check_in_hours=2,
    )

    client = TestClient(create_app(settings))

    before = client.get("/overview/summary", params={"today": "2026-04-14"})
    updated = client.post(
        "/settings/config",
        json={
            "work_review_root": str(work_review_root),
            "obsidian_vault_root": str(vault_root),
            "obsidian_generated_dir": "Steward/Reviews",
            "automation_check_in_hours": 4,
        },
    )
    config = client.get("/settings/config")
    health = client.get("/settings/health")
    automation = client.get("/automation/status", params={"now": "2026-04-14T12:00:00"})
    after = client.get("/overview/summary", params={"today": "2026-04-14"})
    draft = client.post(
        "/overview/actions/execute",
        json={"action_id": "capture_daily_review", "today": "2026-04-14"},
    )

    assert before.status_code == 200
    assert any(
        action["id"] == "configure_notes_output"
        and action["target_page"] == "settings"
        and action["can_execute"] is False
        for action in before.json()["recommended_actions"]
    )
    assert updated.status_code == 200
    assert updated.json()["work_review_root"] == str(work_review_root)
    assert updated.json()["obsidian_vault_root"] == str(vault_root)
    assert updated.json()["obsidian_generated_dir"] == "Steward/Reviews"
    assert updated.json()["automation_check_in_hours"] == 4
    assert config.status_code == 200
    assert config.json()["obsidian_vault_root"] == str(vault_root)
    assert health.status_code == 200
    assert health.json()["obsidian_vault_root"] == str(vault_root)
    assert automation.status_code == 200
    assert automation.json()["check_in_hours"] == 4
    assert "4-hour cadence" in automation.json()["mode_summary"]
    assert after.status_code == 200
    assert any(
        action["id"] == "capture_daily_review" and action["can_execute"] is True
        for action in after.json()["recommended_actions"]
    )
    assert draft.status_code == 200
    assert "Steward\\Reviews" in draft.json()["note_draft"]["path"]
    assert Path(draft.json()["note_draft"]["path"]).exists()

    persisted = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert persisted["steward"]["adapters"]["work_review"]["root"] == str(work_review_root)
    assert persisted["steward"]["adapters"]["obsidian"]["vault_root"] == str(vault_root)
    assert persisted["steward"]["adapters"]["obsidian"]["generated_dir"] == "Steward/Reviews"
    assert persisted["steward"]["automation"]["check_in_hours"] == 4


def test_settings_detected_obsidian_vaults_route(monkeypatch, steward_env, tmp_path):
    settings, _, _ = steward_env

    from plan.steward.host import create_app

    appdata_root = tmp_path / "appdata"
    obsidian_root = appdata_root / "obsidian"
    obsidian_root.mkdir(parents=True)
    (obsidian_root / "obsidian.json").write_text(
        json.dumps(
            {
                "vaults": {
                    "vault-a": {
                        "path": "D:\\Vault\\Notes\\docs",
                        "ts": 1771593915299,
                        "open": True,
                    },
                    "vault-b": {
                        "path": "D:\\Vault\\Archive",
                        "ts": 1771593915200,
                        "open": False,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APPDATA", str(appdata_root))

    client = TestClient(create_app(settings))
    detected = client.get("/settings/obsidian/detected-vaults")

    assert detected.status_code == 200
    assert detected.json() == [
        "D:\\Vault\\Notes\\docs",
        "D:\\Vault\\Archive",
    ]


def test_settings_use_detected_obsidian_vault_persists_and_reloads(monkeypatch, steward_env, tmp_path):
    _, _, _ = steward_env

    import plan.config as cfg
    from plan.steward.config import StewardSettings
    from plan.steward.host import create_app

    work_review_root = tmp_path / "work-review-live"
    work_review_root.mkdir()
    _create_work_review_db(work_review_root / "workreview.db")
    (work_review_root / "config.json").write_text(
        json.dumps({"theme": "system"}, ensure_ascii=False),
        encoding="utf-8",
    )

    vault_root = tmp_path / "vault"
    (vault_root / "Inbox").mkdir(parents=True)
    (vault_root / "Inbox" / "Existing Note.md").write_text(
        "# Existing Note\n\nKeep editing in Obsidian.\n",
        encoding="utf-8",
    )

    appdata_root = tmp_path / "appdata"
    obsidian_root = appdata_root / "obsidian"
    obsidian_root.mkdir(parents=True)
    (obsidian_root / "obsidian.json").write_text(
        json.dumps(
            {
                "vaults": {
                    "vault-a": {
                        "path": str(vault_root),
                        "ts": 1771593915299,
                        "open": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APPDATA", str(appdata_root))

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[ai]",
                'provider = "claude"',
                'model = "claude-sonnet-4-6"',
                'api_key_env = "ANTHROPIC_API_KEY"',
                "",
                "[schedule]",
                'daily_time = "08:00"',
                "enabled = true",
                "run_on_missed = true",
                "",
                "[paths]",
                'profile = "data/profile.md"',
                'context = "data/context.md"',
                'tasks = "data/tasks.json"',
                "",
                "[steward]",
                'backend_url = "http://127.0.0.1:8765"',
                'host = "127.0.0.1"',
                "port = 8765",
                "",
                "[steward.adapters.work_review]",
                f"root = '{work_review_root}'",
                "",
                "[steward.adapters.obsidian]",
                'vault_root = ""',
                'generated_dir = "Steward/Daily"',
                "",
                "[steward.automation]",
                "check_in_hours = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cfg, "_CONFIG_PATH", config_path)
    cfg._cache = None

    settings = StewardSettings(
        backend_url="http://127.0.0.1:8765",
        work_review_root=work_review_root,
        obsidian_vault_root=None,
        obsidian_generated_dir=Path("Steward/Daily"),
        automation_check_in_hours=2,
    )

    client = TestClient(create_app(settings))

    applied = client.post(
        "/settings/obsidian/use-detected-vault",
        json={"vault_root": str(vault_root)},
    )
    config = client.get("/settings/config")
    health = client.get("/settings/health")
    notes_dashboard = client.get("/notes/dashboard")

    assert applied.status_code == 200
    assert applied.json()["obsidian_vault_root"] == str(vault_root)
    assert config.status_code == 200
    assert config.json()["obsidian_vault_root"] == str(vault_root)
    assert health.status_code == 200
    assert health.json()["obsidian_vault_root"] == str(vault_root)
    assert notes_dashboard.status_code == 200
    assert notes_dashboard.json()["vault_ready"] is True
    assert notes_dashboard.json()["indexed_count"] == 1

    persisted = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert persisted["steward"]["adapters"]["obsidian"]["vault_root"] == str(vault_root)
