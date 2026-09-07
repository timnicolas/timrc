"""Stable colors for projects and contexts, so a name always looks the same everywhere.

A name with no stored color still gets one: it is picked from the cycle by a checksum of the
name, which keeps it stable across runs without having to write anything down. Storing a color
is therefore only needed to override that choice.
"""

import zlib

from todotxt.model import PROJECT_SEPARATOR

PROJECT = "project"
CONTEXT = "context"

# Distinguishable on a dark background, the user's shell palette first
CYCLE = (
    "#e6b432",  # yellow
    "#00c3c8",  # cyan
    "#af87ff",  # purple
    "#4eba65",  # green
    "#ff6b80",  # red
    "#b1b9f9",  # teal
    "#d77757",  # orange
    "#6383ff",  # blue
    "#eb9f7f",  # shimmer
    "#5fd7af",  # spring
    "#ff87d7",  # pink
    "#bcbd22",  # olive
)


def root(kind: str, name: str) -> str:
    """The part of a name that decides its color: '+a.b' shares the color of '+a'."""
    bare = name.lstrip("+@").lower()
    return bare.split(PROJECT_SEPARATOR)[0] if kind == PROJECT else bare


def attr(kind: str, name: str) -> str:
    """Palette attribute holding the color of a project or context."""
    return f"{kind}:{root(kind, name)}"


def color(kind: str, name: str, overrides: dict[str, str]) -> str:
    """The stored color of a name, or the stable one its checksum lands on."""
    stored = overrides.get(attr(kind, name))
    if stored:
        return stored
    # crc32 rather than hash(): the latter is salted per process and would not be stable
    return CYCLE[zlib.crc32(root(kind, name).encode()) % len(CYCLE)]


def next_color(current: str, step: int = 1) -> str:
    """The next color of the cycle after `current`, wrapping around."""
    try:
        position = CYCLE.index(current)
    except ValueError:
        position = 0
    return CYCLE[(position + step) % len(CYCLE)]


def entries(kind: str, names: list[str], overrides: dict[str, str]) -> list[tuple]:
    """Palette entries naming the color of every given project or context."""
    seen: dict[str, str] = {}
    for name in names:
        seen.setdefault(attr(kind, name), color(kind, name, overrides))
    return [(name, "", "", "", value, "") for name, value in seen.items()]
