"""The scrollable list of project sections and tasks, and its focus bookkeeping."""

import urwid

from todotxt.config import FOCUS_MAP
from todotxt.model import Task
from todotxt.tui.render import row_indent, section_markup, task_markup
from todotxt.view import Section, ViewState

FocusKey = tuple[str, str]


def task_key(task: Task) -> FocusKey:
    """Identity used to find a task's row again after the list is rebuilt."""
    return ("task", task.to_line())


def section_key(name: str) -> FocusKey:
    """Identity used to find a section's header row again after the list is rebuilt."""
    return ("section", name)


class Row(urwid.WidgetWrap):
    """A selectable line of the list. Keys are never consumed here: the application dispatches them."""

    def __init__(self, markup: list, key: FocusKey, section: str, indent: int = 0, wrap: str = "ellipsis"):
        self.key = key
        self.section = section
        text = urwid.Padding(urwid.Text(markup, wrap=wrap), left=indent)
        super().__init__(urwid.AttrMap(text, None, FOCUS_MAP))

    def selectable(self) -> bool:
        """Rows are always focusable, headers included."""
        return True

    def keypress(self, size, key: str) -> str:
        """Leave every key to the list box and, past it, to the application."""
        return key


class SectionRow(Row):
    """A project heading, focusable so it can be folded. Sub-projects are indented under their parent."""

    def __init__(self, section: Section, collapsed: bool):
        super().__init__(
            section_markup(section, collapsed),
            section_key(section.name),
            section.name,
            indent=row_indent(section.depth),
        )
        self.info = section


class TaskRow(Row):
    """A single task, filed under the section it is displayed in.

    An expanded task stays one row: its body is drawn as extra lines of the same widget, so the
    cursor keeps moving from task to task whatever is unfolded.
    """

    def __init__(self, task: Task, section: str, depth: int = 0, wrap: str = "ellipsis", expanded: bool = False):
        super().__init__(task_markup(task, expanded), task_key(task), section, indent=row_indent(depth), wrap=wrap)
        self.task = task


class TaskList(urwid.ListBox):
    """Renders the sections and handles vim-style motion; every other key bubbles up."""

    def __init__(self):
        super().__init__(urwid.SimpleFocusListWalker([]))
        self._pending_g = False

    def rebuild(self, sections: list[Section], state: ViewState, empty_message: str) -> None:
        """Replace the visible rows with `sections`, dropping those a folded parent hides."""
        wrap = "space" if state.wrap else "ellipsis"
        rows: list[urwid.Widget] = []
        for section in sections:
            if state.is_hidden(section.name):
                continue
            collapsed = state.is_collapsed(section.name)
            rows.append(SectionRow(section, collapsed))
            if not collapsed:
                rows.extend(
                    TaskRow(task, section.name, section.depth, wrap, state.is_expanded(task.to_line()))
                    for task in section.tasks
                )
        if not rows:
            rows.append(urwid.Text(("dim", f"  {empty_message}")))
        self.body[:] = rows

    @property
    def focused_row(self) -> Row | None:
        """The row under the cursor, or None when the list holds no selectable row."""
        if self.position >= len(self.body):
            return None
        row = self.body[self.position]
        return row if isinstance(row, Row) else None

    @property
    def focused_task(self) -> Task | None:
        """The task under the cursor, or None when a section header is focused."""
        row = self.focused_row
        return row.task if isinstance(row, TaskRow) else None

    @property
    def focused_header(self) -> str | None:
        """The section name when a header is focused, None when a task or nothing is."""
        row = self.focused_row
        return row.section if isinstance(row, SectionRow) else None

    @property
    def focused_section(self) -> str | None:
        """The section the cursor is in, whether a header or one of its tasks is focused."""
        row = self.focused_row
        return row.section if row else None

    @property
    def position(self) -> int:
        """Index of the focused row, or 0 when the list is empty or in the middle of a rebuild."""
        try:
            return self.focus_position
        except IndexError:
            return 0

    def neighbour_task(self, offset: int) -> Task | None:
        """The task `offset` rows away from the cursor, when it is filed under the same section."""
        row = self.focused_row
        position = self.position + offset
        if not isinstance(row, TaskRow) or not 0 <= position < len(self.body):
            return None
        neighbour = self.body[position]
        if isinstance(neighbour, TaskRow) and neighbour.section == row.section:
            return neighbour.task
        return None

    def following_task(self) -> Task | None:
        """The next task below the cursor, whatever section it belongs to."""
        for row in list(self.body)[self.position + 1:]:
            if isinstance(row, TaskRow):
                return row.task
        return None

    def preceding_task(self) -> Task | None:
        """The last task above the cursor, whatever section it belongs to."""
        for row in reversed(list(self.body)[: self.position]):
            if isinstance(row, TaskRow):
                return row.task
        return None

    def focus_first_task(self) -> None:
        """Focus the first task rather than its section header, so the first keypress acts on a task."""
        for position, row in enumerate(self.body):
            if isinstance(row, TaskRow):
                self.set_focus(position)
                return

    def restore_focus(self, key: FocusKey | None, fallback_section: str | None, fallback_position: int) -> None:
        """Focus `key` again, falling back to its section header then to the nearest row."""
        for candidate in (key, section_key(fallback_section) if fallback_section else None):
            position = self._find(candidate) if candidate else None
            if position is not None:
                self.set_focus(position)
                return
        self._focus_nearest(fallback_position)

    def keypress(self, size, key: str) -> str | None:
        """Handle j/k, gg and G here; anything else is left to the application."""
        if key == "g":
            self._pending_g = not self._pending_g
            if not self._pending_g:
                self._focus_nearest(0)
            return None
        self._pending_g = False
        if key == "G":
            self._focus_last()
            return None
        key = {"j": "down", "k": "up"}.get(key, key)
        return super().keypress(size, key)

    def _find(self, key: FocusKey) -> int | None:
        """Position of the row carrying `key`, or None when it is gone."""
        for position, row in enumerate(self.body):
            if getattr(row, "key", None) == key:
                return position
        return None

    def _focus_nearest(self, position: int) -> None:
        """Focus the closest selectable row at or before `position`, else the first one."""
        rows = self.body
        candidates = list(range(min(position, len(rows) - 1), -1, -1)) + list(range(len(rows)))
        for candidate in candidates:
            if rows[candidate].selectable():
                self.set_focus(candidate)
                return

    def _focus_last(self) -> None:
        """Focus the last selectable row."""
        for position in range(len(self.body) - 1, -1, -1):
            if self.body[position].selectable():
                self.set_focus(position, coming_from="above")
                return
