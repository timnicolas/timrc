"""Naming the window after the view, so a pane running the app says 'todo' and what it shows.

Setting the title through an escape sequence is not enough under tmux, which ignores it unless
`allow-rename` is on, so the window is renamed through tmux itself. Renaming turns that window's
automatic naming off, hence the restore on the way out.
"""

import atexit
import os
import subprocess
import sys

from todotxt.view import Query

BASE = "todo"

_shown = ""


def window_title(search: str) -> str:
    """'todo', followed by the projects the view is filtered on."""
    projects = Query.parse(search).projects
    return " ".join([BASE, *(f"+{project}" for project in projects)])


def set_title(search: str) -> None:
    """Name the window after the current filter, doing nothing when the name has not changed."""
    global _shown

    title = window_title(search)
    if title == _shown:
        return
    _shown = title
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()
    _tmux("rename-window", title)
    atexit.register(restore_title)


def restore_title() -> None:
    """Hand the window name back to whatever was naming it before."""
    global _shown

    if not _shown:
        return
    _shown = ""
    _tmux("set-window-option", "automatic-rename", "on")


def _tmux(command: str, *args: str) -> None:
    """Run one tmux command against the pane we live in, and nothing at all outside tmux."""
    pane = os.environ.get("TMUX_PANE")
    if not os.environ.get("TMUX") or not pane:
        return
    try:
        subprocess.run(["tmux", command, "-t", pane, *args], check=False, capture_output=True)
    except OSError:
        pass
