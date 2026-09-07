"""The detail pane shown under the task list, on 'D'.

It describes whatever the cursor sits on: a metadata line — checkbox, priority, project,
contexts and tags — then the body of the task alone, stripped of the words that line already
shows and rendered as light markdown.

Clicking in that body turns it into an edit field, which is the only moment the pane is
focusable: outside an edit, 'j' and 'k' can never leave the list. The metadata line is not
edited here; 'e' still opens the task dialog for it.
"""

import urwid

from todotxt.model import CONTEXT_RE, NEWLINE, NO_PROJECT, PROJECT_RE, TAG_RE, Task, description_words
from todotxt.tui.dialogs import to_marker
from todotxt.tui.render import body_line_markup, detail_header_markup
from todotxt.tui.tasklist import Row, SectionRow, TaskRow
from todotxt.view import Section

TITLE = "detail"
EDIT_TITLE = "detail · enter saves · shift+enter breaks the line · esc cancels"

# Row the metadata line is drawn on: right under the top border of the box
HEADER_ROW = 1


def content_lines(task: Task) -> list[str]:
    """The body of `task` without the words its metadata line already shows, one entry per line."""
    return [" ".join(word for word in line.split() if not _is_metadata(word)) for line in task.lines]


def rebuilt_description(task: Task, text: str) -> str:
    """Put an edited body back together with the metadata the pane keeps out of it.

    The metadata words are simply appended to the first line: `Task.parse` is what puts a
    description in canonical order, so nothing here decides where a project or a tag ends up.
    A word the user typed back in by hand is not added a second time.
    """
    body = to_marker(text)
    if not body:
        return ""
    lines = body.split(NEWLINE)
    written = set(description_words(body))
    missing = [word for word in _metadata_words(task) if word not in written]
    lines[0] = " ".join([lines[0], *missing]).strip()
    return NEWLINE.join(lines)


class DetailPane(urwid.WidgetWrap):
    """Box under the list showing the metadata and the body of a task, editable in place."""

    def __init__(self, on_edit_request, on_accept, on_cancel):
        self._on_edit_request = on_edit_request
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self._row: Row | None = None
        self._editing = False
        self._header = urwid.Text("", wrap="space")
        self._body = urwid.Text("", wrap="space")
        self._edit = urwid.Edit(multiline=True, wrap="space")
        # Padded so the field sits exactly where the read-only body was drawn, and does not jump
        self._field = urwid.Padding(self._edit, left=1)
        self._walker = urwid.SimpleListWalker([self._header, self._body])
        self._listing = urwid.ListBox(self._walker)
        # Top corners are junctions: this line doubles as the bottom of the list box above
        self._box = urwid.LineBox(
            urwid.AttrMap(self._listing, "text"),
            title=TITLE,
            title_attr="section",
            tlcorner="├",
            trcorner="┤",
        )
        super().__init__(urwid.AttrMap(self._box, "border"))
        self.update(None)

    @property
    def editing(self) -> bool:
        """Whether the body is currently an edit field holding the focus."""
        return self._editing

    @property
    def task(self) -> Task | None:
        """The task the pane describes, None under a project heading or on an empty list."""
        return self._row.task if isinstance(self._row, TaskRow) else None

    def selectable(self) -> bool:
        """Focusable only while editing, so every navigation key otherwise reaches the task list."""
        return self._editing

    def update(self, row: Row | None) -> None:
        """Show `row`: a task, a project heading, or an empty pane. Ignored while editing."""
        if self._editing:
            return
        self._row = row
        if isinstance(row, TaskRow):
            self._header.set_text(detail_header_markup(row.task))
            self._body.set_text(_content_markup(row.task) or "")
        elif isinstance(row, SectionRow):
            self._header.set_text(_section_meta(row.info))
            self._body.set_text(("dim", _section_hint(row.info.name)))
        else:
            self._header.set_text(("dim", " Nothing selected."))
            self._body.set_text("")

    def begin_edit(self) -> bool:
        """Turn the body into an edit field. False when the pane shows no task to edit."""
        task = self.task
        if self._editing or task is None:
            return False
        self._edit.set_edit_text("\n".join(content_lines(task)))
        self._edit.set_edit_pos(len(self._edit.edit_text))
        self._walker[1] = self._field
        self._listing.set_focus(1)
        self._editing = True
        self._box.set_title(EDIT_TITLE)
        return True

    def end_edit(self) -> None:
        """Put the body back to its read-only markup, whether the edit was saved or dropped."""
        if not self._editing:
            return
        self._editing = False
        self._walker[1] = self._body
        self._listing.set_focus(0)
        self._box.set_title(TITLE)
        self.update(self._row)

    def keypress(self, size, key: str) -> str | None:
        """Enter saves, shift+enter breaks the line, esc drops the edit; the rest is typed in."""
        if not self._editing:
            return key
        if key == "enter":
            self._on_accept(self.task, self._edit.edit_text)
            return None
        if key == "shift enter":
            self._edit.insert_text("\n")
            return None
        if key == "esc":
            self._on_cancel()
            return None
        return super().keypress(size, key)

    def mouse_event(self, size, event: str, button: int, col: int, row: int, focus: bool) -> bool | None:
        """A click in the body starts an edit; the borders and the metadata line are left alone."""
        if not self._editing and event.endswith("mouse press") and button == 1:
            if row < self._body_row(size) or not self._on_edit_request():
                return False
            focus = True
        return super().mouse_event(size, event, button, col, row, focus)

    def _body_row(self, size) -> int:
        """First row the body is drawn on, under the top border and the whole metadata line."""
        return HEADER_ROW + self._header.rows((max(1, size[0] - 2),))


def _content_markup(task: Task) -> list[tuple[str, str]]:
    """Markup for the body of a task, one screen line per stored line, indented past the border."""
    markup: list[tuple[str, str]] = []
    for position, line in enumerate(content_lines(task)):
        markup.append(("dim", "\n " if position else " "))
        markup.extend(body_line_markup(line, task.completed))
    return markup


def _metadata_words(task: Task) -> list[str]:
    """The project, context and tag words the pane hides from the body."""
    return (
        [f"@{context}" for context in task.contexts]
        + [f"{name}:{value}" for name, value in task.tags]
        + [f"+{project}" for project in task.projects]
    )


def _is_metadata(word: str) -> bool:
    """Whether a word is a project, a context or a key:value tag rather than content."""
    return bool(PROJECT_RE.match(word) or CONTEXT_RE.match(word) or TAG_RE.match(word))


def _section_meta(section: Section) -> list:
    """The heading line of the pane when a project heading is focused."""
    return [("section", f" {section.label}"), ("dim", f"  {section.subtree_open} open / {section.subtree_total}")]


def _section_hint(name: str) -> str:
    """What the pane offers under a project heading."""
    if name == NO_PROJECT:
        return " Tasks filed under no project."
    return " Press e to rename this project and its sub-projects."
