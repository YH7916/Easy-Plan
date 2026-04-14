from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from plan.steward.api import steward_error

from plan.steward.config import (
    detect_obsidian_vaults,
    settings_config,
    update_settings_config,
    use_detected_obsidian_vault,
)
from plan.steward.contracts import CapabilityDto, SettingsConfigDto, SettingsHealthDto

router = APIRouter(prefix="/settings")


def _current(request: Request):
    return request.app.state.container


_MODULES = [
    "overview", "sources", "planning", "insights",
    "notes", "chat", "automation", "settings",
]


@router.get("/health", response_model=SettingsHealthDto)
def settings_health(request: Request):
    from pathlib import Path

    settings = _current(request).settings

    adapter_states: dict[str, str] = {"lazy_zju": "available"}

    wr = settings.work_review_root
    adapter_states["work_review"] = (
        "available" if wr is not None and Path(wr).exists() else "degraded"
    )

    ov = settings.obsidian_vault_root
    if ov is None:
        adapter_states["obsidian"] = "not_configured"
    else:
        adapter_states["obsidian"] = "available" if Path(ov).exists() else "degraded"

    return SettingsHealthDto(
        status="ok",
        backend_url=settings.backend_url,
        modules=_MODULES,
        work_review_root=str(settings.work_review_root),
        obsidian_vault_root=str(ov) if ov is not None else None,
        adapter_states=adapter_states,
    )


@router.get("/capabilities", response_model=CapabilityDto)
def settings_capabilities(request: Request):
    settings = _current(request).settings
    ov = settings.obsidian_vault_root

    adapters = ["lazy_zju", "work_review"]
    if ov is not None:
        adapters.append("obsidian")

    features = ["sse_events", "automation"]
    if ov is not None:
        features.append("obsidian_deeplink")

    return CapabilityDto(
        version="1.0.0",
        api_version="v1",
        modules=_MODULES,
        adapters=adapters,
        features=features,
    )


@router.get("/config", response_model=SettingsConfigDto)
def settings_config_read(request: Request):
    return settings_config(_current(request).settings)


@router.post("/config", response_model=SettingsConfigDto)
def settings_config_update(payload: SettingsConfigDto, request: Request):
    from plan.steward.host import _build_container

    try:
        refreshed_settings = update_settings_config(payload)
    except ValueError as exc:
        raise steward_error(400, "bad_request", str(exc)) from exc

    previous = _current(request)
    request.app.state.container = _build_container(
        refreshed_settings,
        event_bus=previous.event_bus,
        chat=previous.chat,
    )
    _current(request).event_bus.publish(
        "settings.config_updated",
        {
            "obsidian_vault_root": (
                str(refreshed_settings.obsidian_vault_root)
                if refreshed_settings.obsidian_vault_root is not None
                else None
            ),
            "obsidian_generated_dir": refreshed_settings.obsidian_generated_dir.as_posix(),
        },
    )
    return settings_config(refreshed_settings)


@router.get("/obsidian/detected-vaults", response_model=list[str])
def settings_detected_obsidian_vaults():
    return detect_obsidian_vaults()


@router.post("/obsidian/use-detected-vault", response_model=SettingsConfigDto)
def settings_use_detected_obsidian_vault(payload: dict[str, Any], request: Request):
    from plan.steward.host import _build_container

    try:
        refreshed_settings = use_detected_obsidian_vault(payload["vault_root"])
    except KeyError as exc:
        raise steward_error(400, "bad_request", "vault_root is required.") from exc
    except ValueError as exc:
        raise steward_error(409, "conflict", str(exc)) from exc

    previous = _current(request)
    request.app.state.container = _build_container(
        refreshed_settings,
        event_bus=previous.event_bus,
        chat=previous.chat,
    )
    _current(request).event_bus.publish(
        "settings.config_updated",
        {
            "obsidian_vault_root": (
                str(refreshed_settings.obsidian_vault_root)
                if refreshed_settings.obsidian_vault_root is not None
                else None
            ),
            "obsidian_generated_dir": refreshed_settings.obsidian_generated_dir.as_posix(),
        },
    )
    return settings_config(refreshed_settings)
