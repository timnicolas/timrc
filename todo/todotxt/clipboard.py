"""Putting text on the clipboard, so what the list shows can leave without a mouse selection.

The TUI captures the mouse, which is what takes the terminal's own click-and-drag selection
away; copying is therefore done by the application rather than by the terminal. Under tmux the
text also goes into the paste buffer, so `prefix + ]` pastes it into the pane next door.
"""

import os
import shutil
import subprocess

# First one installed wins: macOS, then Wayland, then X11
COPY_COMMANDS = (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"])


def copy(text: str) -> bool:
    """Put `text` on the system clipboard, and in the tmux buffer when running inside tmux.

    False when the platform offers no clipboard command, which is what the caller reports
    rather than failing silently on a key that looks like it worked.
    """
    if os.environ.get("TMUX"):
        _run(["tmux", "load-buffer", "-"], text)
    command = next((command for command in COPY_COMMANDS if shutil.which(command[0])), None)
    return _run(command, text) if command else False


def _run(command: list[str], text: str) -> bool:
    """Feed `text` to `command` on its standard input, False when it is not usable."""
    try:
        return subprocess.run(command, input=text, text=True, capture_output=True).returncode == 0
    except OSError:
        return False
