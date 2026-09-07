"""Palette entries for the projects and contexts a todo file happens to hold.

Their names are only known once the file is read, so their colors cannot sit in the static
palette: they are registered on the screen as they show up, each one together with the bold copy
the headings use and the copy drawn on the selection background. State lives in the module
rather than being handed around, because the markup helpers that need a color are plain
functions called from the list, the detail pane and the edit fields alike.

With no screen bound — outside the TUI — every lookup falls back on the generic attribute, so
rendering keeps working with no palette to register into.
"""

from todotxt import colors, settings
from todotxt.config import SELECT_SUFFIX, register_focus, selection_entry

# Attribute of the color preview of a dialog, pointed at a new color as the choice cycles
PREVIEW = "color_preview"

# Suffix of the bold copy of a color, used by the section headings and the detail heading
BOLD_SUFFIX = "_bold"

# The block a color is previewed with, wide enough to read as a color rather than a glyph
SWATCH = "████"

_screen = None
_overrides: dict[str, str] = {}
_registered: set[str] = set()


def bind(screen) -> None:
    """Attach the screen to register into and read back the colors stored in the settings."""
    global _screen

    _screen = screen
    _registered.clear()
    _overrides.clear()
    _overrides.update(settings.load_colors())
    set_preview(colors.CYCLE[0])


def register(kind: str, names: list[str]) -> None:
    """Register the color of every given project or context, so markup can name it."""
    if _screen is None:
        return
    for entry in colors.entries(kind, names, _overrides):
        _register(entry)


def attr_for(kind: str, name: str) -> str:
    """The attribute drawing `name` in its own color, or the generic one for its kind."""
    return _ensure(kind, name) or kind


def bold_attr_for(kind: str, name: str, fallback: str) -> str:
    """The bold attribute drawing `name` in its own color, for a heading."""
    attr = _ensure(kind, name)
    return f"{attr}{BOLD_SUFFIX}" if attr else fallback


def color_of(kind: str, name: str) -> str:
    """The color `name` is currently drawn in, stored or picked from its checksum."""
    return colors.color(kind, name, _overrides)


def set_color(kind: str, name: str, value: str) -> None:
    """Give a project or context a color, and remember it for the next runs."""
    attr = colors.attr(kind, name)
    _overrides[attr] = value
    _registered.discard(attr)
    register(kind, [name])
    _repaint()
    settings.save_color(attr, value)


def rename(kind: str, old: str, new: str) -> None:
    """Carry the color of a renamed project or tag over to the name it now goes by.

    A name whose color was only ever derived from its own checksum would otherwise change color
    when renamed, which reads as a different thing entirely; the color it was showing is
    therefore pinned under the new name, whether it had been chosen or not.
    """
    if colors.attr(kind, old) != colors.attr(kind, new):
        set_color(kind, new, color_of(kind, old))


def set_preview(value: str) -> None:
    """Point the preview attribute at `value`, storing nothing: a dialog shows a choice with it."""
    if _screen is not None:
        _register_entry((PREVIEW, "", "", "", value, ""))
        _repaint()


def _repaint() -> None:
    """Force the next draw to repaint everything, so a repointed color shows on every row.

    urwid only redraws the rows whose content changed, and re-registering an entry changes no
    content at all: the rows keep naming the same attribute, which now stands for another color.
    """
    if _screen is not None:
        _screen.clear()


def _ensure(kind: str, name: str) -> str | None:
    """The attribute of `name`, registered on first sight. None while no screen is bound.

    Registering here is what colors a project typed straight into the add dialog, which by
    definition no reload has ever seen.
    """
    if _screen is None:
        return None
    attr = colors.attr(kind, name)
    if attr not in _registered:
        register(kind, [name])
    return attr


def _register(entry: tuple) -> None:
    """Register one color and the three copies of it the rest of the interface needs."""
    for item in (entry, selection_entry(entry), *_bold_entries(entry)):
        _register_entry(item)
    _registered.add(entry[0])


def _bold_entries(entry: tuple) -> tuple:
    """The bold copy of a color entry, and that copy over the selection background."""
    name, fg16, bg16, _mono, fg, bg = entry
    bold = (f"{name}{BOLD_SUFFIX}", f"{fg16},bold" if fg16 else "bold", bg16, "bold", f"{fg},bold", bg)
    return bold, selection_entry(bold)


def _register_entry(entry: tuple) -> None:
    """Hand one entry to the screen, and to the focus map when it is not a selection copy."""
    _screen.register_palette_entry(*entry)
    if not entry[0].endswith(SELECT_SUFFIX):
        register_focus(entry[0])
