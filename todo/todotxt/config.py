"""Paths, colors and the keybinding table the help screen is built from."""

import os
from pathlib import Path

# Priorities offered when cycling with the priority key
PRIORITY_LEVELS = "ABC"

# How often the TUI checks the todo file for external changes, in seconds
SYNC_INTERVAL = 2.0


def todo_path() -> Path:
    """Path of the todo.txt file, overridable with TODO_FILE."""
    return Path(os.environ.get("TODO_FILE", Path.home() / "todo.txt")).expanduser()


def done_path() -> Path:
    """Path of the done.txt archive, overridable with DONE_FILE."""
    return Path(os.environ.get("DONE_FILE", Path.home() / "done.txt")).expanduser()


# Catppuccin-ish palette, to sit well next to the tmux status bar
# Colors taken from the user's shell palette (~/.tim/zsh/color.zsh), so both look alike.
# They are 24-bit values: the screen must be put in truecolor mode or urwid approximates them.
ORANGE = "#d77757"
SHIMMER = "#eb9f7f"
TEAL = "#b1b9f9"
BLUE = "#6383ff"
PURPLE = "#af87ff"
GREEN = "#4eba65"
RED = "#ff6b80"
YELLOW = "#e6b432"
CYAN = "#00c3c8"
BG_SELECT = "#264f78"
GREY = "#808080"

# One step lighter than GREY, so a quote reads apart from the dimmed marker in front of it
GREY_SOFT = "#a0a0a0"

# Frame lines are structure, not content: dark enough to stay out of the way
BORDER = "#3a3f4b"

# Entries are (name, fg16, bg16, mono, fg, bg): urwid needs a 16-color fallback next to the
# 24-bit value, and uses the latter only once the screen is switched to truecolor.
PALETTE = [
    ("text", "", "", "", "", ""),
    ("dim", "dark gray", "", "", GREY, ""),
    ("border", "dark gray", "", "", BORDER, ""),
    ("bold", "bold", "", "bold", "bold", ""),
    ("section", "light blue,bold", "", "bold", f"{BLUE},bold", ""),
    ("section_focus", "white,bold", "dark blue", "standout", f"{TEAL},bold", BG_SELECT),
    ("priority_a", "light red,bold", "", "bold", f"{RED},bold", ""),
    ("priority_b", "brown,bold", "", "bold", f"{ORANGE},bold", ""),
    ("priority_c", "light green,bold", "", "bold", f"{GREEN},bold", ""),
    ("project", "yellow", "", "", YELLOW, ""),
    ("context", "light magenta", "", "", PURPLE, ""),
    ("tag", "dark cyan", "", "", CYAN, ""),
    ("completed", "dark gray", "", "", GREY, ""),
    # Explicit light foreground: without one a light terminal theme draws dark on dark blue
    ("focus", "white", "dark blue", "standout", TEAL, BG_SELECT),
    ("dialog", "", "", "", "", ""),
    ("dialog_title", "yellow,bold", "", "bold", f"{YELLOW},bold", ""),
    ("suggestion", "light magenta", "", "", PURPLE, ""),
    ("md_heading", "light cyan,bold", "", "bold", f"{TEAL},bold", ""),
    ("md_code", "light green", "", "", GREEN, ""),
    ("md_bold", "white,bold", "", "bold", f"{SHIMMER},bold", ""),
    ("md_italic", "white,italics", "", "italics", f"{SHIMMER},italics", ""),
    ("md_quote", "light gray,italics", "", "italics", f"{GREY_SOFT},italics", ""),
    ("md_mark", "dark gray", "", "", GREY, ""),
]

PRIORITY_ATTR = {"A": "priority_a", "B": "priority_b", "C": "priority_c"}


# Suffix of the copy of an attribute drawn on the selection background
SELECT_SUFFIX = "_on_select"


def _selection_palette() -> list[tuple]:
    """A copy of every entry over the selection background, keeping its own foreground.

    Mapping the whole focused row to a single attribute would be simpler, but it flattens the
    project, context and markdown colors exactly on the line the user is reading.
    """
    return [
        (f"{name}{SELECT_SUFFIX}", fg16 or "white", "dark blue", mono or "standout", fg or TEAL, BG_SELECT)
        for name, fg16, _bg16, mono, fg, _bg in PALETTE
    ]


PALETTE += _selection_palette()

# Passed as the focus_map of every row, so a focused line gains the selection background
# without losing what its colors mean
FOCUS_MAP = {entry[0]: f"{entry[0]}{SELECT_SUFFIX}" for entry in PALETTE if not entry[0].endswith(SELECT_SUFFIX)}
FOCUS_MAP[None] = "focus"

# Single source of truth for keybindings, read by the help screen: (keys, action label, section)
KEYBINDINGS = [
    ("j / k", "Move down / up", "Navigation"),
    ("gg / G", "Go to top / bottom", "Navigation"),
    ("space / enter", "Unfold section or task", "Navigation"),
    ("n", "New task", "Tasks"),
    ("e", "Edit task / rename project", "Tasks"),
    ("shift+enter", "New line in the task editor", "Tasks"),
    ("x", "Toggle done", "Tasks"),
    ("p / P", "Priority up / down", "Tasks"),
    ("d", "Delete task", "Tasks"),
    ("J / K", "Move task down / up (file order)", "Tasks"),
    ("a", "Archive task to done.txt", "Archive"),
    ("A", "Archive all completed tasks", "Archive"),
    ("s", "Cycle sort inside projects", "View"),
    ("w", "Wrap long tasks on several lines", "View"),
    ("c", "Show / hide completed", "View"),
    ("C", "Confirm a task with no project", "View"),
    ("D", "Show / hide the detail pane", "View"),
    ("+ / -", "Grow / shrink the detail pane", "View"),
    ("click / drag", "Edit the body in the detail pane / move its border", "View"),
    ("/", "Search", "View"),
    ("r", "Refresh and clear search", "View"),
    ("?", "Help", "Help"),
    ("q", "Quit", "Help"),
]


def help_sections() -> list[tuple[str, list[tuple[str, str]]]]:
    """Keybindings grouped by section, in declaration order, for the help screen."""
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for keys, label, section in KEYBINDINGS:
        if not sections or sections[-1][0] != section:
            sections.append((section, []))
        sections[-1][1].append((keys, label))
    return sections
