import json
import pytest
from datetime import date
from plan.sources import SourceItem, BaseSource, register, load_sources


def test_source_item_to_task_dict():
    item = SourceItem(
        title="Do homework",
        source="school",
        due=date(2026, 4, 15),
        project="CS101",
        priority=2,
        external_id="hw-42",
    )
    d = item.to_task_dict()
    assert d["title"] == "Do homework"
    assert d["due"] == "2026-04-15"
    assert d["priority"] == 2
    assert d["external_id"] == "hw-42"


def test_source_item_no_due():
    item = SourceItem(title="Someday task", source="local")
    assert item.to_task_dict()["due"] is None


def test_base_source_push_raises():
    class DummySource(BaseSource):
        name = "dummy"
        def fetch(self):
            return []

    src = DummySource()
    with pytest.raises(NotImplementedError):
        src.push([])


def test_base_source_not_writable():
    class DummySource2(BaseSource):
        name = "dummy2"
        def fetch(self):
            return []

    assert DummySource2().is_writable is False


def test_register_decorator():
    @register
    class MySrc(BaseSource):
        name = "mysrc"
        def fetch(self):
            return []

    from plan.sources import _registry
    assert "mysrc" in _registry


def test_load_sources_skips_disabled():
    cfg = {"sources": {"school": {"enabled": False, "cli_command": "echo []"}}}
    sources = load_sources(cfg)
    assert sources == []


def test_load_sources_shell_source(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *a, **kw: b'[{"title":"hw1","due":null,"priority":0,"project":null,"external_id":"s1"}]')
    cfg = {"sources": {"school": {"enabled": True, "cli_command": "echo []", "writable": False}}}
    sources = load_sources(cfg)
    assert len(sources) == 1
    items = sources[0].fetch()
    assert items[0].title == "hw1"


def test_shell_source_fetch_parses_json(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    payload = json.dumps([
        {"title": "Lab report", "due": "2026-04-20", "priority": 2,
         "project": "CS101", "external_id": "lab-1"},
    ]).encode()
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: payload)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    items = src.fetch()
    assert len(items) == 1
    assert items[0].title == "Lab report"
    assert items[0].due == date(2026, 4, 20)
    assert items[0].priority == 2
    assert items[0].external_id == "lab-1"


def test_shell_source_fetch_handles_null_due(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    payload = json.dumps([{"title": "No due", "due": None}]).encode()
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: payload)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    items = src.fetch()
    assert items[0].due is None


def test_shell_source_raises_on_bad_json(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"not json")
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(ValueError, match="non-JSON"):
        src.fetch()


def test_shell_source_raises_on_non_array(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b'{"key": "val"}')
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(ValueError, match="JSON array"):
        src.fetch()


def test_shell_source_raises_on_command_failure(monkeypatch):
    import subprocess
    from plan.sources.shell import ShellSource
    def fail(*a, **kw):
        raise subprocess.CalledProcessError(1, "fake")
    monkeypatch.setattr(subprocess, "check_output", fail)
    src = ShellSource(name="school", config={"enabled": True, "cli_command": "fake", "writable": False})
    with pytest.raises(RuntimeError, match="command failed"):
        src.fetch()
