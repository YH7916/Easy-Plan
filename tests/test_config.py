import pytest
from pathlib import Path
import tomllib

CONFIG_PATH = Path("D:/Plan/config.toml")


def test_get_ai_model(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    assert cfg.get("ai.model") == "claude-sonnet-4-6"


def test_get_missing_key(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    assert cfg.get("nonexistent.key", "fallback") == "fallback"


def test_set_and_restore(monkeypatch):
    """set_key writes to config.toml and the value is readable back."""
    monkeypatch.chdir("D:/Plan")
    backup = CONFIG_PATH.read_bytes()
    import plan.config as cfg
    cfg._cache = None
    try:
        cfg.set_key("projects.areas", ["work", "study"])
        cfg._cache = None
        assert cfg.get("projects.areas") == ["work", "study"]
    finally:
        CONFIG_PATH.write_bytes(backup)
        cfg._cache = None


def test_resolve_path(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    p = cfg.resolve_path("tasks")
    assert p.name == "tasks.json"


def test_api_key_missing(monkeypatch):
    monkeypatch.chdir("D:/Plan")
    import plan.config as cfg
    cfg._cache = None
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        cfg.api_key()
