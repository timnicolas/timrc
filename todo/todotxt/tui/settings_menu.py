"""The settings menu, on ',': every project and tag of the file, renameable and recolorable.

One place to review the whole scheme side by side, and the only place a tag can be renamed or
recolored, since a tag has no heading to press 'e' on. A color change lands immediately, in the
list behind as much as in the settings file: the palette entry itself is repointed, so nothing
has to be rebuilt for it to show everywhere. A rename hands over to the application, which asks
for the new name and comes back here.

Sub-projects are folded into their parent, since they share its color by design: renaming the
line renames the whole family, and a single sub-project is still renamed from its own heading.
"""

from collections.abc import Callable

import urwid

from todotxt import colors
from todotxt.config import FOCUS_MAP
from todotxt.tui import palette

TITLE = "Settings"
HINT = " ← / → color · e rename · esc close"
EMPTY = " No project or tag in this file yet."

# What each kind is called in the menu, in its dialogs and in its messages
LABELS = {colors.PROJECT: "project", colors.CONTEXT: "tag"}

# The character a name of each kind is written with
PREFIX = {colors.PROJECT: "+", colors.CONTEXT: "@"}

HEADINGS = {colors.PROJECT: "Projects", colors.CONTEXT: "Tags"}


class MenuRow(urwid.WidgetWrap):
    """One project or tag, drawn in its own color, which left and right cycle."""

    def __init__(self, kind: str, name: str, on_rename: Callable[[str, str], None]):
        self.key = (kind, name)
        self._kind = kind
        self._name = name
        self._on_rename = on_rename
        self._text = urwid.Text("")
        super().__init__(urwid.AttrMap(urwid.Padding(self._text, left=1), None, FOCUS_MAP))
        self._show()

    def selectable(self) -> bool:
        """Focusable, so the list box can move the cursor from one line to the next."""
        return True

    def keypress(self, size, key: str) -> str | None:
        """Cycle the color on left and right, rename on 'e' or enter, leave the rest alone."""
        if key in ("e", "enter"):
            self._on_rename(self._kind, self._name)
            return None
        step = {"right": 1, "l": 1, "left": -1, "h": -1}.get(key)
        if step is None:
            return key
        palette.set_color(self._kind, self._name, colors.next_color(self._color(), step))
        self._show()
        return None

    def _color(self) -> str:
        """The color the row currently stands for."""
        return palette.color_of(self._kind, self._name)

    def _show(self) -> None:
        """Redraw the swatch, the name and the color code, all in the color itself."""
        attr = palette.attr_for(self._kind, self._name)
        self._text.set_text([(attr, f"{palette.SWATCH}  {self._name}"), ("dim", f"   {self._color()}")])


class SettingsOverlay(urwid.WidgetWrap):
    """Scrollable list of every project and tag, closed with esc, 'q' or ','."""

    def __init__(
        self,
        projects: list[str],
        contexts: list[str],
        on_close: Callable[[], None],
        on_rename: Callable[[str, str], None],
        focus: tuple[str, str] | None = None,
    ):
        self._on_close = on_close
        rows = _group(colors.PROJECT, projects, on_rename) + _group(colors.CONTEXT, contexts, on_rename)
        listing = urwid.ListBox(urwid.SimpleFocusListWalker(rows or [urwid.Text(("dim", EMPTY))]))
        body = urwid.Frame(listing, footer=urwid.Text(("dim", HINT)))
        box = urwid.LineBox(urwid.Padding(body, left=1, right=1), title=TITLE, title_attr="dialog_title")
        super().__init__(urwid.AttrMap(box, "dialog"))
        _focus(listing, focus)

    def selectable(self) -> bool:
        """Always focusable, so the main loop routes keys here while the menu is open."""
        return True

    def keypress(self, size, key: str) -> str | None:
        """Close on esc, 'q' or ','; 'j' and 'k' move as they do in the task list."""
        if key in ("esc", "q", ","):
            self._on_close()
            return None
        return super().keypress(size, {"j": "down", "k": "up"}.get(key, key))


def _group(kind: str, names: list[str], on_rename: Callable[[str, str], None]) -> list[urwid.Widget]:
    """A heading and one row per color of `names`, empty when the file uses none of that kind."""
    roots: list[str] = []
    for name in names:
        root = colors.root(kind, name)
        if root not in roots:
            roots.append(root)
    if not roots:
        return []
    return [urwid.Text(("section", f" {HEADINGS[kind]}"))] + [
        MenuRow(kind, f"{PREFIX[kind]}{root}", on_rename) for root in roots
    ]


def _focus(listing: urwid.ListBox, wanted: tuple[str, str] | None) -> None:
    """Put the cursor on `wanted`, on the first line when it is gone or none was asked for."""
    for candidate in (wanted, None):
        for position, row in enumerate(listing.body):
            if isinstance(row, MenuRow) and candidate in (None, row.key):
                listing.set_focus(position)
                return
