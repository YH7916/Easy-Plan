import pytest


@pytest.fixture(autouse=True)
def patch_paths(monkeypatch, tmp_path):
    """Redirect profile/context paths to tmp_path."""
    import plan.config as cfg
    if hasattr(cfg, '_cache'):
        cfg._cache = None
    profile_file = tmp_path / "profile.md"
    context_file = tmp_path / "context.md"
    original_resolve = cfg.resolve_path

    def fake_resolve(key):
        if key == "profile":
            return profile_file
        if key == "context":
            return context_file
        return original_resolve(key)

    monkeypatch.setattr(cfg, "resolve_path", fake_resolve)
    yield


def test_read_profile_missing():
    from plan.memory import read_profile
    assert read_profile() == ""


def test_write_and_read_profile():
    from plan.memory import write_profile, read_profile
    write_profile("# My Profile\n\nI am a CS student.")
    assert "CS student" in read_profile()


def test_read_context_missing():
    from plan.memory import read_context
    assert read_context() == ""


def test_write_and_read_context():
    from plan.memory import write_context, read_context
    write_context("# Daily Context\n\nFeel focused today.")
    assert "focused" in read_context()


def test_append_context_creates_timestamped_entry():
    from plan.memory import append_context, read_context, write_context
    write_context("")
    append_context("Finished ML homework.")
    result = read_context()
    assert "Finished ML homework." in result
    import re
    assert re.search(r"## \d{4}-\d{2}-\d{2}", result)


def test_append_context_accumulates():
    from plan.memory import append_context, read_context, write_context
    write_context("")
    append_context("Entry one.")
    append_context("Entry two.")
    result = read_context()
    assert "Entry one." in result
    assert "Entry two." in result
