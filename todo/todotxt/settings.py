"""Preferences remembered between runs, in a small INI file the user can edit by hand."""

import configparser
import os
from pathlib import Path

from todotxt.view import SortMode, ViewState

SECTION = "view"

# Below this the pane cannot show a heading line and any content at all
MIN_DETAIL_HEIGHT = 4


def config_path() -> Path:
    """Path of the preferences file, overridable with TODO_CONFIG."""
    return Path(os.environ.get("TODO_CONFIG", Path.home() / ".todo-config")).expanduser()


def load_into(state: ViewState, path: Path | None = None) -> None:
    """Apply the saved preferences to `state`, leaving it untouched when there is no file.

    A malformed or half-written file is ignored rather than fatal: preferences are a convenience,
    never a reason to refuse to start.
    """
    parser = configparser.ConfigParser()
    try:
        parser.read(path or config_path(), encoding="utf-8")
    except (configparser.Error, OSError):
        return
    if not parser.has_section(SECTION):
        return

    section = parser[SECTION]
    try:
        state.sort = SortMode(section.get("sort", state.sort.value))
    except ValueError:
        pass
    for name in ("show_completed", "wrap", "confirm_without_project", "detail_visible"):
        try:
            setattr(state, name, section.getboolean(name, getattr(state, name)))
        except ValueError:
            pass
    try:
        state.detail_height = max(MIN_DETAIL_HEIGHT, section.getint("detail_height", state.detail_height))
    except ValueError:
        pass


def save_from(state: ViewState, path: Path | None = None) -> None:
    """Write the preferences worth remembering. Failing to save is never worth a crash."""
    parser = configparser.ConfigParser()
    parser[SECTION] = {
        "sort": state.sort.value,
        "show_completed": str(state.show_completed).lower(),
        "wrap": str(state.wrap).lower(),
        "confirm_without_project": str(state.confirm_without_project).lower(),
        "detail_visible": str(state.detail_visible).lower(),
        "detail_height": str(state.detail_height),
    }
    target = path or config_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            parser.write(handle)
    except OSError:
        pass
