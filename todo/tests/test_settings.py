"""Tests for todotxt.settings: loading and saving preferences to the INI config file."""

from pathlib import Path

from todotxt.settings import config_path, load_into, save_from
from todotxt.view import SortMode, ViewState


def test_save_from_then_load_into_roundtrips_all_keys(tmp_path):
    """Every saved preference comes back unchanged after a save/load roundtrip."""
    path = tmp_path / "config.ini"
    saved = ViewState(sort=SortMode.ALPHA, show_completed=False, wrap=False, confirm_without_project=False)
    save_from(saved, path)

    loaded = ViewState()
    load_into(loaded, path)
    assert loaded.sort == SortMode.ALPHA
    assert loaded.show_completed is False
    assert loaded.wrap is False
    assert loaded.confirm_without_project is False


def test_load_into_missing_file_keeps_defaults(tmp_path):
    """Loading from a file that does not exist leaves the state at its defaults."""
    state = ViewState()
    load_into(state, tmp_path / "missing.ini")
    assert state == ViewState()


def test_load_into_corrupted_file_keeps_defaults_without_raising(tmp_path):
    """A file that is not valid INI is ignored, not fatal."""
    path = tmp_path / "corrupted.ini"
    path.write_text("this is not [valid ini at all = \n[[[", encoding="utf-8")
    state = ViewState()
    load_into(state, path)
    assert state == ViewState()


def test_load_into_ignores_invalid_value_without_affecting_other_keys(tmp_path):
    """An invalid value for one key is skipped, while the other keys still load normally."""
    path = tmp_path / "config.ini"
    path.write_text(
        "[view]\nsort = not-a-mode\nwrap = not-a-boolean\nshow_completed = true\nconfirm_without_project = false\n",
        encoding="utf-8",
    )
    state = ViewState()
    load_into(state, path)
    assert state.sort == SortMode.FILE
    assert state.wrap is True
    assert state.show_completed is True
    assert state.confirm_without_project is False


def test_config_path_respects_todo_config_env_var(tmp_path, monkeypatch):
    """config_path() returns the path from TODO_CONFIG when it is set."""
    custom = tmp_path / "custom-config"
    monkeypatch.setenv("TODO_CONFIG", str(custom))
    assert config_path() == custom


def test_config_path_defaults_to_home_when_unset(monkeypatch):
    """config_path() falls back to ~/.todo-config when TODO_CONFIG is not set."""
    monkeypatch.delenv("TODO_CONFIG", raising=False)
    assert config_path() == Path.home() / ".todo-config"


def test_save_from_to_unwritable_directory_does_not_raise(tmp_path):
    """save_from() never raises, even when the target directory cannot be created."""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    target = blocked / "sub" / ".todo-config"
    save_from(ViewState(), target)
    assert not target.exists()
