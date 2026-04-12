"""Config loader: reads config.toml + .env, supports get/set/save."""
from __future__ import annotations

import os
import tomllib
import tomli_w
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config.toml"


def _load_raw() -> dict:
    load_dotenv(_ROOT / ".env")
    with open(_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


_cache: dict | None = None


def get_config(reload: bool = False) -> dict:
    global _cache
    if _cache is None or reload:
        _cache = _load_raw()
    return _cache


def get(key: str, default: Any = None) -> Any:
    """Dot-separated key lookup, e.g. get('ai.model')."""
    cfg = get_config()
    parts = key.split(".")
    node: Any = cfg
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_key(key: str, value: Any) -> None:
    """Set a dot-separated key and persist to config.toml."""
    cfg = get_config()
    parts = key.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    _save(cfg)


def _save(cfg: dict) -> None:
    with open(_CONFIG_PATH, "wb") as f:
        tomli_w.dump(cfg, f)


def resolve_path(key: str) -> Path:
    """Resolve a paths.* config key relative to project root."""
    rel = get(f"paths.{key}")
    if rel is None:
        raise KeyError(f"paths.{key} not found in config")
    return _ROOT / rel


def api_key() -> str:
    """Return the Anthropic API key from env (supports ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN)."""
    env_var = get("ai.api_key_env", "ANTHROPIC_API_KEY")
    key = os.environ.get(env_var, "") or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not key:
        raise EnvironmentError(
            f"Neither {env_var} nor ANTHROPIC_AUTH_TOKEN is set. "
            "Add it to .env or export it in your shell."
        )
    return key
