"""The bottom bar: a single status line. The keybindings live in the help screen, under '?'."""

import urwid


class Footer(urwid.WidgetWrap):
    """One row at the bottom of the screen: the file, the counters and the last message."""

    def __init__(self):
        self._status = urwid.Text("", wrap="clip")
        super().__init__(self._status)

    def set_status(self, markup) -> None:
        """Show status markup on the bar."""
        self._status.set_text(markup)
