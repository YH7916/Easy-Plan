from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from plan.config import get, set_key
from plan.steward.contracts import SettingsConfigDto


@dataclass(slots=True)
class StewardSettings:
    backend_url: str = "http://127.0.0.1:8765"
    host: str = "127.0.0.1"
    port: int = 8765
    work_review_root: Path = Path(os.environ.get("APPDATA", Path.home())) / "work-review"
    obsidian_vault_root: Path | None = None
    obsidian_generated_dir: Path = Path("Steward/Daily")
    automation_check_in_hours: int = 2


def load_settings() -> StewardSettings:
    backend_url = get("steward.backend_url", "http://127.0.0.1:8765")
    work_review_root = Path(
        get(
            "steward.adapters.work_review.root",
            str(Path(os.environ.get("APPDATA", Path.home())) / "work-review"),
        )
    )
    obsidian_root_value = get("steward.adapters.obsidian.vault_root")
    obsidian_root = Path(obsidian_root_value) if obsidian_root_value else None
    obsidian_generated_dir = Path(
        get("steward.adapters.obsidian.generated_dir", "Steward/Daily")
    )
    check_in_hours = int(get("steward.automation.check_in_hours", 2))
    return StewardSettings(
        backend_url=backend_url,
        host=get("steward.host", "127.0.0.1"),
        port=int(get("steward.port", 8765)),
        work_review_root=work_review_root,
        obsidian_vault_root=obsidian_root,
        obsidian_generated_dir=obsidian_generated_dir,
        automation_check_in_hours=check_in_hours,
    )


def settings_config(settings: StewardSettings | None = None) -> SettingsConfigDto:
    resolved = settings or load_settings()
    return SettingsConfigDto(
        work_review_root=str(resolved.work_review_root),
        obsidian_vault_root=(
            str(resolved.obsidian_vault_root)
            if resolved.obsidian_vault_root is not None
            else None
        ),
        obsidian_generated_dir=resolved.obsidian_generated_dir.as_posix(),
        automation_check_in_hours=resolved.automation_check_in_hours,
    )


def update_settings_config(payload: SettingsConfigDto) -> StewardSettings:
    work_review_root = payload.work_review_root.strip()
    if not work_review_root:
        raise ValueError("Work Review root cannot be empty.")

    obsidian_root = (payload.obsidian_vault_root or "").strip()
    generated_dir = Path(payload.obsidian_generated_dir.strip())
    if not str(generated_dir):
        raise ValueError("Obsidian generated folder cannot be empty.")
    if generated_dir.is_absolute():
        raise ValueError("Obsidian generated folder must stay relative to the vault root.")

    set_key("steward.adapters.work_review.root", str(Path(work_review_root)))
    set_key("steward.adapters.obsidian.vault_root", obsidian_root)
    set_key("steward.adapters.obsidian.generated_dir", generated_dir.as_posix())
    set_key("steward.automation.check_in_hours", payload.automation_check_in_hours)
    return load_settings()


def detect_obsidian_vaults() -> list[str]:
    appdata_root = Path(os.environ.get("APPDATA", Path.home()))
    config_path = appdata_root / "obsidian" / "obsidian.json"
    if not config_path.exists():
        return []

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    raw_vaults = payload.get("vaults")
    if not isinstance(raw_vaults, dict):
        return []

    ranked_paths: list[tuple[bool, int, str, str]] = []
    for vault in raw_vaults.values():
        if not isinstance(vault, dict):
            continue
        path = vault.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        ranked_paths.append(
            (
                not bool(vault.get("open")),
                -int(vault.get("ts", 0) or 0),
                path.lower(),
                str(Path(path)),
            )
        )

    unique_paths: list[str] = []
    seen: set[str] = set()
    for _, _, _, path in sorted(ranked_paths):
        if path in seen:
            continue
        seen.add(path)
        unique_paths.append(path)
    return unique_paths


def use_detected_obsidian_vault(vault_root: str) -> StewardSettings:
    detected = detect_obsidian_vaults()
    requested = str(Path(vault_root))
    detected_map = {path.lower(): path for path in detected}
    resolved = detected_map.get(requested.lower())
    if resolved is None:
        raise ValueError("Requested vault is not in Obsidian's detected vault list.")

    current = settings_config()
    updated = SettingsConfigDto(
        work_review_root=current.work_review_root,
        obsidian_vault_root=resolved,
        obsidian_generated_dir=current.obsidian_generated_dir,
        automation_check_in_hours=current.automation_check_in_hours,
    )
    return update_settings_config(updated)
