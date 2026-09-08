"""Naming the pane after the view, so the window label says 'todo' and what it shows.

Only the pane title is set, never the window name: the app usually runs in one pane among
several, and renaming the window would both freeze it — tmux turns `automatic-rename` off on
the window it renames — and speak for the panes next door. Which pane the window is named
after is tmux's call, made from `automatic-rename-format`.
"""

import atexit
import os
import subprocess
import sys

from todotxt.view import Query

BASE = "todo"

_shown = ""
_previous: str | None = None


def pane_title(search: str) -> str:
    """'todo', followed by the projects the view is filtered on."""
    projects = Query.parse(search).projects
    return " ".join([BASE, *(f"+{project}" for project in projects)])


def set_title(search: str) -> None:
    """Name the pane after the current filter, doing nothing when the name has not changed."""
    global _shown, _previous

    title = pane_title(search)
    if title == _shown:
        return
    if not _shown:
        _previous = _read_pane_title()
        atexit.register(restore_title)
    _shown = title
    _write_title(title)


def restore_title() -> None:
    """Give the pane back the title it carried before the app took it over."""
    global _shown

    if not _shown:
        return
    _shown = ""
    if _previous is not None:
        _write_title(_previous)


def _write_title(title: str) -> None:
    """Set the title of the terminal we own, which tmux reads as the pane title."""
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()


def _read_pane_title() -> str | None:
    """The title our pane carried before we touched it, None outside tmux or on any hiccup.

    Nothing is ever written back through tmux, only read: a title set through the escape
    sequence lands on our own terminal, so a popup — where TMUX_PANE names the pane that
    opened it rather than one of our own — cannot rename someone else's pane.
    """
    pane = os.environ.get("TMUX_PANE")
    if not os.environ.get("TMUX") or not pane:
        return None
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "-t", pane, "#{pane_title}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    return result.stdout.rstrip("\n") if result.returncode == 0 else None
