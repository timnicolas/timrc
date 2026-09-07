"""Modal boxes: the add/edit field with its completions, and the delete confirmation."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import urwid

from todotxt.model import NEWLINE

MAX_SUGGESTIONS = 8

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
        self.edit = urwid.Edit(edit_text=text.replace(NEWLINE, "\n"), multiline=True)
        self.edit.set_edit_pos(len(self.edit.edit_text))
        self.suggestions = urwid.Text("")
        body = urwid.Pile([urwid.AttrMap(self.edit, "dialog"), urwid.AttrMap(self.suggestions, "suggestion")])
        super().__init__(title, body)

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
    """One-line text box: enter accepts what it holds, esc cancels."""

    def __init__(
        self,
        title: str,
        label: str,
        text: str,
        on_accept: Callable[[str], None],
        on_cancel: Callable[[], None],
    ):
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self.edit = urwid.Edit(("dialog_title", f"{label} "), edit_text=text)
        self.edit.set_edit_pos(len(text))
        super().__init__(title, urwid.AttrMap(self.edit, "dialog"))

    def keypress(self, size, key: str) -> None:
        """Accept on enter, cancel on esc, type everything else into the field."""
        if key == "enter":
            self._on_accept(self.edit.edit_text.strip())
            return None
        if key == "esc":
            self._on_cancel()
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
