"""The keybinding reference shown on '?'."""

from collections.abc import Callable

import urwid

from todotxt.config import help_sections

KEY_COLUMN_WIDTH = 14


class HelpOverlay(urwid.WidgetWrap):
    """Read-only list of every keybinding, closed with '?', esc or 'q'."""

    def __init__(self, on_close: Callable[[], None]):
        self._on_close = on_close
        rows: list[urwid.Widget] = []
        for name, bindings in help_sections():
            if rows:
                rows.append(urwid.Divider())
            rows.append(urwid.Text(("section", name)))
            rows.extend(_binding_row(keys, label) for keys, label in bindings)
        box = urwid.LineBox(urwid.Padding(urwid.Pile(rows), left=1, right=1), title="Keybindings",
                            title_attr="dialog_title")
        super().__init__(urwid.AttrMap(box, "dialog"))

    def selectable(self) -> bool:
        """Always focusable, so the main loop routes keys here while the help is open."""
        return True

    def keypress(self, size, key: str) -> None:
        """Close on '?', esc or 'q', ignore everything else."""
        if key in ("?", "esc", "q"):
            self._on_close()
        return None


def _binding_row(keys: str, label: str) -> urwid.Widget:
    """One 'keys — label' line of the help screen."""
    return urwid.Columns(
        [(KEY_COLUMN_WIDTH, urwid.Text(("bold", keys))), urwid.Text(("dialog", label))],
        dividechars=1,
    )
