"""Modal boxes: the add/edit field with its completions, and the delete confirmation."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import urwid

from todotxt import colors
from todotxt.model import NEWLINE
from todotxt.tui import palette
from todotxt.tui.render import body_line_markup

MAX_SUGGESTIONS = 8

# Shown next to the color preview: the keys the text field itself does not use
COLOR_HINT = "↑ / ↓ to change"

# A completion stub runs back to the previous whitespace, line breaks included
WORD_BOUNDARY_RE = re.compile(r"\s")


@dataclass
class _Completion:
    """A tab-completion cycle in progress on one word of the edit field."""

    start: int
    stub: str
    candidates: list[str]
    length: int
    index: int = 0


class HighlightedEdit(urwid.Edit):
    """Edit field that keeps the syntax colors of what it holds while it is being edited.

    urwid draws an Edit with a single attribute, but `get_text` may return one attribute run per
    piece: that is enough to colour the field, and it leaves editing and the caret untouched.
    A field carrying a caption is left alone, since the caption owns the runs in front.
    """

    def get_text(self):
        """The text on screen, plus one attribute run per coloured piece of it."""
        if self._caption:
            return super().get_text()
        markup: list[tuple[str, str]] = []
        for index, line in enumerate(self.edit_text.split("\n")):
            if index:
                markup.append(("text", "\n"))
            markup.extend(body_line_markup(line, completed=False))
        text, attrs = urwid.util.decompose_tagmarkup(markup)
        return (text, attrs) if text else (self.edit_text, [])


def move_to_line_edge(edit: urwid.Edit, to_end: bool) -> None:
    """Put the cursor at the start or the end of the line it currently sits on."""
    text, position = edit.edit_text, edit.edit_pos
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    edit.set_edit_pos(end if to_end and end != -1 else len(text) if to_end else start)


class Dialog(urwid.WidgetWrap):
    """A bordered, titled box that takes every key it is given."""

    def __init__(self, title: str, body: urwid.Widget):
        box = urwid.LineBox(urwid.Padding(body, left=1, right=1), title=title, title_attr="dialog_title")
        super().__init__(urwid.AttrMap(box, "dialog"))

    def selectable(self) -> bool:
        """Always focusable, so the main loop routes keys to the dialog while it is open."""
        return True


class TaskDialog(Dialog):
    """Editor for a task, completing '+project' and '@context' words with tab.

    The field is multi-line and shows real line breaks, which is far more readable than the
    literal marker the file stores; the two are converted into each other on the way in and out.
    """

    def __init__(
        self,
        title: str,
        text: str,
        projects: list[str],
        contexts: list[str],
        on_accept: Callable[[str], None],
        on_cancel: Callable[[], None],
    ):
        self._projects = [f"+{project}" for project in projects]
        self._contexts = [f"@{context}" for context in contexts]
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self._completion: _Completion | None = None
        self.edit = HighlightedEdit(edit_text=text.replace(NEWLINE, "\n"), multiline=True)
        self.edit.set_edit_pos(len(self.edit.edit_text))
        self.suggestions = urwid.Text("")
        body = urwid.Pile([urwid.AttrMap(self.edit, "dialog"), urwid.AttrMap(self.suggestions, "suggestion")])
        super().__init__(title, body)
        # Opening on a '+' should already list the projects, without waiting for a keystroke
        self._show_suggestions(self._stub())

    def keypress(self, size, key: str) -> None:
        """Accept on enter, break the line on shift+enter, cancel on esc, complete on tab."""
        if key == "enter":
            self._on_accept(to_marker(self.edit.edit_text))
            return None
        if key == "shift enter":
            self.edit.insert_text("\n")
            return None
        if key == "esc":
            self._on_cancel()
            return None
        if key == "tab":
            self._complete()
            return None
        if key in ("ctrl a", "ctrl e"):
            move_to_line_edge(self.edit, key == "ctrl e")
            return None
        self._completion = None
        super().keypress(size, key)
        self._show_suggestions(self._stub())
        return None

    def _stub(self) -> str:
        """The word being typed, from the last whitespace up to the cursor."""
        return WORD_BOUNDARY_RE.split(self.edit.edit_text[: self.edit.edit_pos])[-1]

    def _candidates(self, stub: str) -> list[str]:
        """Known projects or contexts starting with `stub`, empty for any other word."""
        if stub.startswith("+"):
            pool = self._projects
        elif stub.startswith("@"):
            pool = self._contexts
        else:
            return []
        return [name for name in pool if name.lower().startswith(stub.lower())]

    def _complete(self) -> None:
        """Insert the next candidate for the word under the cursor, cycling on repeated tabs."""
        if self._completion is None:
            stub = self._stub()
            candidates = self._candidates(stub)
            if not candidates:
                self._show_suggestions(stub)
                return
            self._completion = _Completion(self.edit.edit_pos - len(stub), stub, candidates, len(stub))

        state = self._completion
        choice = state.candidates[state.index]
        text = self.edit.edit_text
        self.edit.set_edit_text(f"{text[: state.start]}{choice}{text[state.start + state.length :]}")
        self.edit.set_edit_pos(state.start + len(choice))
        state.length = len(choice)
        state.index = (state.index + 1) % len(state.candidates)
        self._show_suggestions(state.stub)

    def _show_suggestions(self, stub: str) -> None:
        """List the completions available for `stub` under the edit field."""
        candidates = self._candidates(stub)
        self.suggestions.set_text("  ".join(candidates[:MAX_SUGGESTIONS]))


def to_marker(text: str) -> str:
    """Turn the line breaks typed in the field into the literal marker a todo.txt line carries."""
    lines = [line.strip() for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return NEWLINE.join(lines)


class PromptDialog(Dialog):
    """One-line text box: enter accepts what it holds, esc cancels.

    `rows` are drawn under the field, for a subclass with something to show next to the text.
    """

    def __init__(
        self,
        title: str,
        label: str,
        text: str,
        on_accept: Callable[[str], None],
        on_cancel: Callable[[], None],
        rows: list[urwid.Widget] | None = None,
    ):
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self.edit = urwid.Edit(("dialog_title", f"{label} "), edit_text=text)
        self.edit.set_edit_pos(len(text))
        field = urwid.AttrMap(self.edit, "dialog")
        super().__init__(title, urwid.Pile([field, *rows]) if rows else field)

    def keypress(self, size, key: str) -> None:
        """Accept on enter, cancel on esc, type everything else into the field."""
        if key == "enter":
            self._on_accept(self.edit.edit_text.strip())
            return None
        if key == "esc":
            self._on_cancel()
            return None
        if key in ("ctrl a", "ctrl e"):
            move_to_line_edge(self.edit, key == "ctrl e")
            return None
        super().keypress(size, key)
        return None


class ConfirmDialog(Dialog):
    """Yes/no box: 'y' or enter confirms, 'n', esc or 'q' cancels, anything else is ignored."""

    def __init__(self, title: str, question: str, on_confirm: Callable[[], None], on_cancel: Callable[[], None]):
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        body = urwid.Pile(
            [
                urwid.Text(("dialog", question), wrap="ellipsis"),
                urwid.Text(
                    [
                        ("dialog_title", "y"),
                        ("dialog", " confirm    "),
                        ("dialog_title", "n"),
                        ("dialog", " cancel"),
                    ]
                ),
            ]
        )
        super().__init__(title, body)

    def keypress(self, size, key: str) -> None:
        """Route the answer to the right callback and swallow every other key."""
        if key in ("y", "Y", "enter"):
            self._on_confirm()
        elif key in ("n", "N", "esc", "q"):
            self._on_cancel()
        return None


class ColorPromptDialog(PromptDialog):
    """Rename box that also picks the color the name is drawn in, cycled with up and down.

    Only the preview changes while the color is being chosen: 'enter' hands the name and the
    color over to the caller, which is what stores them and repaints the rest of the interface.
    """

    def __init__(
        self,
        title: str,
        label: str,
        text: str,
        subject: str,
        color: str,
        on_accept: Callable[[str, str], None],
        on_cancel: Callable[[], None],
    ):
        self._color = color
        self._subject = subject
        self._preview = urwid.Text("")
        super().__init__(
            title, label, text, lambda name: on_accept(name, self._color), on_cancel, rows=[self._preview]
        )
        self._show_preview()

    def keypress(self, size, key: str) -> None:
        """Cycle the color on up and down, leaving every other key to the text field."""
        step = {"down": 1, "up": -1}.get(key)
        if step is None:
            return super().keypress(size, key)
        self._color = colors.next_color(self._color, step)
        self._show_preview()
        return None

    def _show_preview(self) -> None:
        """Redraw the swatch and its code under the field, on the color currently chosen."""
        palette.set_preview(self._color)
        self._preview.set_text(
            [("dim", f"{self._subject} "), (palette.PREVIEW, palette.SWATCH),
             ("dim", f"  {self._color}   {COLOR_HINT}")]
        )
