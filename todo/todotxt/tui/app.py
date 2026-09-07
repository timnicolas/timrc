"""Wiring of the todo.txt TUI: widgets, key dispatch and the poll for external changes."""

from pathlib import Path

import urwid

from todotxt import colors, settings
from todotxt.config import PALETTE, PRIORITY_LEVELS, SYNC_INTERVAL
from todotxt.model import NO_PROJECT, PROJECT_SEPARATOR, Task, cycle_priority
from todotxt.store import TaskNotFound, TodoStore
from todotxt.tui import palette
from todotxt.tui.detail import DetailPane, rebuilt_description
from todotxt.tui.dialogs import ColorPromptDialog, ConfirmDialog, PromptDialog, TaskDialog
from todotxt.tui.footer import Footer
from todotxt.tui.help import HelpOverlay
from todotxt.tui.keys import disable_extended_keys, enable_extended_keys, patch_input_sequences
from todotxt.tui.settings_menu import LABELS, PREFIX, SettingsOverlay
from todotxt.tui.tasklist import TaskList, section_key, task_key
from todotxt.tui.title import restore_title, set_title
from todotxt.view import Query, SortMode, ViewState, build_sections

DIALOG_WIDTH = ("relative", 70)
HELP_WIDTH = ("relative", 50)
# Given, not packed: the table is taller than a short terminal and scrolls inside the box
HELP_HEIGHT = ("relative", 80)
MENU_WIDTH = ("relative", 45)
MENU_HEIGHT = ("relative", 60)
MIN_MODAL_HEIGHT = 8
MIN_DIALOG_WIDTH = 30
MAX_PATH_WIDTH = 40
TRUECOLOR = 2**24
REORDER_HINT = "Reordering only works in file order — press s"
NO_PROJECT_QUESTION = "This task carries no project. Add it anyway?"
DETAIL_HIDDEN_HINT = "The detail pane is hidden — press D"
DETAIL_EDIT_HINT = "Editing the body — tab saves, enter breaks the line, esc cancels"

# Rows the search box and the status bar take out of the screen, around the body
SEARCH_ROWS = 3
FOOTER_ROWS = 1

# Rows the task list keeps whatever the detail pane grows to: its two borders and three tasks
MIN_LIST_ROWS = 5


def run(store: TodoStore, path: Path | None = None, search: str = "") -> None:
    """Start the TUI on `store`, filtered by `search` if one is given.

    `path` is only used to label the status bar and defaults to the store's own todo file.
    The terminal is asked for extended key reporting, and given it back whatever happens next.
    """
    patch_input_sequences()
    enable_extended_keys()
    set_title(search)
    try:
        TodoApp(store, path, search).run()
    finally:
        disable_extended_keys()
        restore_title()


class TodoApp:
    """The whole application: task list, footer, modals and the file-change poll."""

    def __init__(self, store: TodoStore, path: Path | None = None, search: str = ""):
        self.store = store
        self.path = Path(path) if path else store.todo_path
        self.state = ViewState()
        settings.load_into(self.state)
        self.state.search = search
        self.tasks: list[Task] = []
        self.list = TaskList()
        urwid.connect_signal(self.list.body, "modified", self._update_detail)
        self.footer = Footer()
        self.search = urwid.Edit(("completed", " / "), search)
        urwid.connect_signal(self.search, "change", self._on_search_change)
        # Drawn in the same muted grey as completed tasks: always available, never in the way
        # No bottom line: the box below supplies the single line the two of them share
        self.search_box = _dim_box(
            urwid.AttrMap(self.search, "completed"), "search", "completed", bline="", top=True
        )
        self.list_box = _dim_box(self.list, "tasks", "section")
        self.detail = DetailPane(
            on_edit_request=self._begin_detail_edit,
            on_accept=self._accept_detail_edit,
            on_next=self._leave_detail_for_search,
            on_cancel=self._end_detail_edit,
        )
        self.body = urwid.Pile([self.list_box])
        self.frame = urwid.Frame(self.body, header=self.search_box, footer=self.footer)
        self.loop = urwid.MainLoop(
            self.frame, PALETTE, unhandled_input=self._dispatch, handle_mouse=True, input_filter=self._filter_input
        )
        self._modal: urwid.Widget | None = None
        self._drag_row: int | None = None
        self._message = ""
        self._mtime = 0.0
        self._actions = {
            "q": self._quit,
            " ": self._toggle_fold,
            "right": lambda: self._set_fold(False),
            "left": lambda: self._set_fold(True),
            "enter": self._toggle_fold,
            "n": self._add_task,
            "e": self._edit_task,
            "x": self._toggle_done,
            "p": lambda: self._change_priority(forward=True),
            "P": lambda: self._change_priority(forward=False),
            "J": lambda: self._move_task(1),
            "K": lambda: self._move_task(-1),
            "d": self._delete_task,
            "a": self._archive_task,
            "A": self._archive_completed,
            "s": self._cycle_sort,
            "w": self._toggle_wrap,
            "c": self._toggle_completed,
            "C": self._toggle_confirm,
            "D": self._toggle_detail,
            "+": self._add_task_in_project,
            "=": lambda: self._resize_detail(1),
            "-": lambda: self._resize_detail(-1),
            "tab": self._focus_next_section,
            "/": self._start_search,
            ",": self._show_settings,
            "r": self._refresh,
            "?": self._show_help,
        }

    def run(self) -> None:
        """Load the file and enter the urwid main loop."""
        # The palette holds 24-bit colors: without this urwid rounds them to its 256-color set
        self.loop.screen.set_terminal_properties(colors=TRUECOLOR)
        palette.bind(self.loop.screen)
        self._reload()
        self.list.focus_first_task()
        self._apply_detail_layout()
        self._update_detail()
        self.loop.set_alarm_in(SYNC_INTERVAL, self._sync)
        self.loop.run()

    def _dispatch(self, key: str) -> None:
        """Route a key the list box did not use to the action it is bound to."""
        if self._modal is not None:
            return
        self._message = ""
        # A click in the list moves the focus out of the pane without leaving edit mode, and the
        # pane then receives nothing: recover here rather than swallow every key from now on
        if self.detail.editing and not self._detail_focused():
            self._commit_detail_edit()
        if self.detail.editing:
            return
        if self.frame.focus_position == "header":
            self._search_key(key)
            return

        action = self._actions.get(key)
        if action:
            action()
        self._update_status()

    def _quit(self) -> None:
        """Leave the application, saving an edit in progress on the way out."""
        self._commit_detail_edit()
        raise urwid.ExitMainLoop()

    def _toggle_fold(self) -> None:
        """Unfold what the cursor sits on: the body of a task, or the contents of a section."""
        task = self.list.focused_task
        if task is not None:
            self.state.toggle_expanded(task.to_line())
            self._refresh_view()
            return
        section = self.list.focused_header
        if section is None:
            return
        self.state.toggle_fold(section)
        self._render()
        self.list.restore_focus(section_key(section), section, self.list.position)

    def _set_fold(self, collapsed: bool) -> None:
        """Fold or unfold the section under the cursor, whichever way the arrow points.

        Inert on a task: the arrows only mean anything on a project heading.
        """
        section = self.list.focused_header
        if section is None or self.state.is_collapsed(section) == collapsed:
            return
        self.state.toggle_fold(section)
        self._render()
        self.list.restore_focus(section_key(section), section, self.list.position)

    def _toggle_done(self) -> None:
        """Flip the completion state of the focused task."""
        task = self.list.focused_task
        if task is None:
            return
        section = self.list.focused_section
        updated = task.toggled()
        self._follow_expanded(task, updated)
        if self._write(lambda: self.store.update(updated)):
            self._reload(focus_key=task_key(updated), fallback_section=section)

    def _change_priority(self, forward: bool) -> None:
        """Move the focused task to the next or previous priority, clearing it past the last one."""
        task = self.list.focused_task
        if task is None:
            return
        section = self.list.focused_section
        priority = cycle_priority(task.priority, PRIORITY_LEVELS) if forward else _previous_priority(task.priority)
        updated = task.with_priority(priority)
        self._follow_expanded(task, updated)
        if self._write(lambda: self.store.update(updated)):
            self._reload(focus_key=task_key(updated), fallback_section=section)

    def _add_task(self) -> None:
        """Open the add dialog, already filed under the project the view is filtered on."""
        self._open_new_dialog(self._filtered_project_prefix())

    def _add_task_in_project(self) -> None:
        """Open the add dialog on a project: the filtered one, or a '+' offering the whole list."""
        self._open_new_dialog(self._filtered_project_prefix() or "+")

    def _filtered_project_prefix(self) -> str:
        """'+project ' when the view is filtered on exactly one project, empty otherwise.

        Filtering on several projects says nothing about which one a new task belongs to.
        """
        projects = Query.parse(self.state.search).projects
        return f"+{projects[0]} " if len(projects) == 1 else ""

    def _open_new_dialog(self, text: str) -> None:
        """Open the add dialog on `text`, which a refused confirmation gives back to be fixed."""
        self._open_modal(
            TaskDialog(
                "New task",
                text,
                self.store.projects(),
                self.store.contexts(),
                on_accept=self._accept_new,
                on_cancel=self._close_modal,
            )
        )

    def _accept_new(self, text: str) -> None:
        """Append the task typed in the add dialog, asking first when it carries no project."""
        self._close_modal()
        if not text:
            return
        task = Task.parse(text)
        if task.projects or not self.state.confirm_without_project:
            self._store_new(task)
            return
        self._open_modal(
            ConfirmDialog(
                "No project",
                NO_PROJECT_QUESTION,
                on_confirm=lambda: self._store_new(task),
                on_cancel=lambda: self._open_new_dialog(text),
            )
        )

    def _store_new(self, task: Task) -> None:
        """Append a new task to the file and put the cursor on it."""
        self._close_modal()
        self.store.add(task)
        self._reload(focus_key=task_key(task), fallback_section=task.project)

    def _edit_task(self) -> None:
        """Edit the focused task, or rename the project when the cursor sits on a heading.

        Priority stays under p and P.
        """
        task = self.list.focused_task
        if task is None:
            self._rename_project()
            return
        section = self.list.focused_section
        self._open_modal(
            TaskDialog(
                "Edit task",
                task.description,
                self.store.projects(),
                self.store.contexts(),
                on_accept=lambda text: self._accept_edit(task, section, text),
                on_cancel=self._close_modal,
            )
        )

    def _accept_edit(self, task: Task, section: str, text: str) -> None:
        """Store the edited description, treating an empty or unchanged line as a cancel.

        The field holds `task.description` alone: dates and priority stay with the model, which
        also honors an 'x' or a '(A)' typed into the text.
        """
        self._close_modal()
        if not text or text == task.description:
            return
        updated = task.with_description(text)
        self._follow_expanded(task, updated)
        if self._write(lambda: self.store.update(updated)):
            self._reload(focus_key=task_key(updated), fallback_section=section)

    def _rename_from_settings(self, kind: str, name: str) -> None:
        """Ask for a new name for a project or a tag, then come back to the menu."""
        self._close_modal()
        self._open_modal(
            PromptDialog(
                f"Rename {LABELS[kind]}",
                "New name:",
                name,
                on_accept=lambda text: self._accept_settings_rename(kind, name, text),
                on_cancel=lambda: self._show_settings((kind, name)),
            )
        )

    def _accept_settings_rename(self, kind: str, old: str, text: str) -> None:
        """Rename a project or a tag across the file, its color following, then reopen the menu.

        An empty or unchanged name is a cancel; the menu comes back on the line that was edited,
        under whichever name it goes by now.
        """
        self._close_modal()
        new = _prefixed(kind, text)
        if not new or new == old:
            self._show_settings((kind, old))
            return
        if len(new.split()) > 1:
            self._notify(f"A {LABELS[kind]} name cannot contain spaces")
            self._show_settings((kind, old))
            return
        rename = self.store.rename_project if kind == colors.PROJECT else self.store.rename_context
        count = rename(old, new)
        if not count:
            self._notify(f"No task carries {old} any more")
            self._reload()
            self._show_settings((kind, old))
            return
        palette.rename(kind, old, new)
        self._follow_renamed(kind, old, new)
        self._notify(f"Renamed {old} to {new} in {count} task(s)")
        self._reload()
        self._show_settings((kind, new))

    def _rename_project(self) -> None:
        """Open the dialog renaming the focused project heading and choosing its color."""
        section = self.list.focused_header
        if section is None:
            return
        if section == NO_PROJECT:
            self._notify("Tasks with no project cannot be renamed")
            return
        self._open_modal(
            ColorPromptDialog(
                "Rename project",
                "New name:",
                section,
                f"Color of +{colors.root(colors.PROJECT, section)}:",
                palette.color_of(colors.PROJECT, section),
                on_accept=lambda text, color: self._accept_rename(section, text, color),
                on_cancel=self._close_modal,
            )
        )

    def _accept_rename(self, old: str, text: str, color: str) -> None:
        """Store the chosen color, and rename the project across the file when the name changed.

        An empty name is a cancel; an unchanged one still applies the color that was picked.
        """
        self._close_modal()
        new = _prefixed(colors.PROJECT, text)
        if not new:
            return
        if len(new.split()) > 1:
            self._notify("A project name cannot contain spaces")
            return
        if new == old:
            self._store_color(old, color)
            return
        count = self.store.rename_project(old, new)
        if not count:
            self._notify(f"No task carries {old} any more")
            self._reload()
            return
        palette.rename(colors.PROJECT, old, new)
        self._store_color(new, color)
        self._follow_renamed(colors.PROJECT, old, new)
        self._reload(focus_key=section_key(new), fallback_section=new)
        self._notify(f"Renamed {old} to {new} in {count} task(s)")

    def _store_color(self, project: str, color: str) -> None:
        """Remember the color picked for a project, unless it is the one it already had."""
        if color != palette.color_of(colors.PROJECT, project):
            palette.set_color(colors.PROJECT, project, color)

    def _show_settings(self, focus: tuple[str, str] | None = None) -> None:
        """Open the menu listing every project and tag, to rename or recolor them.

        It is built from a fresh read of the file, so a rename made from it is reflected when it
        comes back; `focus` is the line the cursor should land on.
        """
        self._open_modal(
            SettingsOverlay(
                self.store.projects(),
                self.store.contexts(),
                self._close_modal,
                self._rename_from_settings,
                focus=focus,
            ),
            width=MENU_WIDTH,
            height=MENU_HEIGHT,
        )

    def _follow_renamed(self, kind: str, old: str, new: str) -> None:
        """Carry folds and open bodies over to the new name, so nothing folds at random.

        Only a project has sections to fold; both kinds appear in the lines an expanded body is
        remembered by, which is why those are rewritten either way.
        """
        if kind == colors.PROJECT:
            self.state.collapsed = {_renamed_section(name, old, new) for name in self.state.collapsed}
        self.state.expanded = {_renamed_line(kind, line, old, new) for line in self.state.expanded}

    def _delete_task(self) -> None:
        """Ask for confirmation before removing the focused task."""
        task = self.list.focused_task
        if task is None:
            return
        section = self.list.focused_section
        self._open_modal(
            ConfirmDialog(
                "Delete task",
                task.summary,
                on_confirm=lambda: self._confirm_delete(task, section),
                on_cancel=self._close_modal,
            )
        )

    def _confirm_delete(self, task: Task, section: str) -> None:
        """Delete the task the confirmation was opened on."""
        self._close_modal()
        if self._write(lambda: self.store.delete(task)):
            self._notify("Task deleted")
            self._reload(fallback_section=section)

    def _archive_task(self) -> None:
        """Move the focused task to done.txt."""
        task = self.list.focused_task
        if task is None:
            return
        section = self.list.focused_section
        # Grabbed before the archive: the next task, or the one above when archiving the last
        neighbour = self.list.following_task() or self.list.preceding_task()
        if self._write(lambda: self.store.archive(task)):
            self._notify("Task archived")
            self._reload(focus_key=task_key(neighbour) if neighbour else None, fallback_section=section)

    def _archive_completed(self) -> None:
        """Move every completed task to done.txt."""
        section = self.list.focused_section
        count = self.store.archive_completed()
        self._notify(f"Archived {count} completed task(s)")
        self._reload(fallback_section=section)

    def _toggle_completed(self) -> None:
        """Show or hide the tasks that are already done."""
        self.state.show_completed = not self.state.show_completed
        self._save_settings()
        self._reload()

    def _toggle_confirm(self) -> None:
        """Switch the confirmation asked before adding a task that carries no project."""
        self.state.confirm_without_project = not self.state.confirm_without_project
        self._save_settings()
        self._notify(f"Confirm tasks with no project: {'on' if self.state.confirm_without_project else 'off'}")

    def _toggle_detail(self) -> None:
        """Show or hide the pane describing the focused row under the list."""
        self._commit_detail_edit()
        self.state.detail_visible = not self.state.detail_visible
        self._end_detail_edit()
        self._save_settings()
        self._apply_detail_layout()
        self._update_detail()

    def _apply_detail_layout(self) -> None:
        """Rebuild the body so the pane appears, disappears or takes its current height."""
        self.list_box.set_bottom_shared(self.state.detail_visible)
        contents = [(self.list_box, self.body.options())]
        if self.state.detail_visible:
            contents.append((self.detail, self.body.options("given", self._detail_rows())))
        self.body.contents = contents
        self.body.focus_position = 1 if self.detail.editing else 0

    def _resize_detail(self, delta: int) -> None:
        """Grow or shrink the detail pane, never past what leaves the list usable."""
        if not self.state.detail_visible:
            self._notify(DETAIL_HIDDEN_HINT)
            return
        height = min(max(settings.MIN_DETAIL_HEIGHT, self._detail_rows() + delta), self._max_detail_rows())
        if height == self.state.detail_height:
            return
        self.state.detail_height = height
        self._apply_detail_layout()
        self._save_settings()
        self._notify(f"Detail pane: {height} rows")

    def _detail_rows(self) -> int:
        """Height the pane is drawn at: the remembered one, cut down to what the screen allows."""
        return min(max(settings.MIN_DETAIL_HEIGHT, self.state.detail_height), self._max_detail_rows())

    def _max_detail_rows(self) -> int:
        """Tallest the pane may get before the list above it stops being usable."""
        rows = self.loop.screen.get_cols_rows()[1] - SEARCH_ROWS - FOOTER_ROWS - MIN_LIST_ROWS
        return max(settings.MIN_DETAIL_HEIGHT, rows)

    def _commit_detail_edit(self) -> None:
        """Save what the detail pane holds before leaving it. Only esc throws an edit away."""
        if self.detail.editing:
            self._accept_detail_edit(self.detail.task, self.detail.edit_text)

    def _detail_focused(self) -> bool:
        """Whether the detail pane really holds the focus, and not just the editing flag."""
        return self.state.detail_visible and len(self.body.contents) > 1 and self.body.focus_position == 1

    def _begin_detail_edit(self, at_end: bool = True) -> bool:
        """Put the pane into edit mode and hand it the focus. False when it shows no task."""
        if self._modal is not None or not self.state.detail_visible or not self.detail.begin_edit(at_end):
            return False
        self.body.focus_position = 1
        self._notify(DETAIL_EDIT_HINT)
        return True

    def _end_detail_edit(self) -> None:
        """Leave edit mode and give the focus back to the task list."""
        if not self.detail.editing:
            return
        self.detail.end_edit()
        self.body.focus_position = 0
        self._message = ""
        self._update_status()

    def _accept_detail_edit(self, task: Task, text: str) -> None:
        """Save the edited body with its metadata reattached, an unchanged one being a cancel."""
        section = self.list.focused_section
        self._end_detail_edit()
        description = rebuilt_description(task, text)
        if not description:
            return
        updated = task.with_description(description)
        if updated.to_line() == task.to_line():
            return
        self._follow_expanded(task, updated)
        if self._write(lambda: self.store.update(updated)):
            self._reload(focus_key=task_key(updated), fallback_section=section)
            self._notify("Task saved")

    def _update_detail(self) -> None:
        """Point the detail pane at the row under the cursor, whenever the pane is shown."""
        if self.state.detail_visible:
            self.detail.update(self.list.focused_row)

    def _filter_input(self, keys: list, _raw: list) -> list:
        """Take out the mouse events that drag the border of the detail pane, pass the rest on."""
        if "window resize" in keys:
            self._apply_detail_layout()
        if self._modal is not None or not self.state.detail_visible:
            self._drag_row = None
            return keys
        return [key for key in keys if not self._drag_step(key)]

    def _drag_step(self, key) -> bool:
        """Handle one event of a border drag, telling whether it belonged to the drag."""
        if not isinstance(key, tuple) or len(key) != 4:
            return False
        event, button, _col, row = key
        if event.endswith("mouse press") and button == 1 and row == self._border_row():
            self._drag_row = row
            return True
        if self._drag_row is None:
            return False
        if event.endswith("mouse drag"):
            self._resize_detail(self._drag_row - row)
            self._drag_row = self._border_row()
            return True
        if event.endswith("mouse release"):
            self._drag_row = None
            return True
        return False

    def _border_row(self) -> int:
        """Screen row the top border of the detail pane is drawn on."""
        return self.loop.screen.get_cols_rows()[1] - FOOTER_ROWS - self._detail_rows()

    def _refresh(self) -> None:
        """Drop the search and re-read the file from disk."""
        self.search.set_edit_text("")
        self._reload()
        self._notify("Refreshed")

    def _show_help(self) -> None:
        """Open the keybinding reference."""
        self._open_modal(HelpOverlay(self._close_modal), width=HELP_WIDTH, height=HELP_HEIGHT)

    def _focus_next_section(self) -> None:
        """Move the focus on to the next section: list, then detail pane, then search."""
        if self.state.detail_visible and self._begin_detail_edit():
            return
        self._start_search()

    def _leave_detail_for_search(self, task: Task, text: str) -> None:
        """Save what the pane holds, the way enter does, then carry the focus to the search."""
        self._accept_detail_edit(task, text)
        self._start_search()

    def _start_search(self) -> None:
        """Send the focus to the always-visible search field, which filters as the query is typed."""
        self.frame.focus_position = "header"
        self.search.set_edit_pos(len(self.search.edit_text))

    def _search_key(self, key: str) -> None:
        """Enter and tab keep the query, esc drops it; the list follows every keystroke."""
        if key not in ("enter", "esc", "tab"):
            return
        if key == "esc":
            self.search.set_edit_text("")
        self._end_search()

    def _on_search_change(self, _widget: urwid.Edit, text: str) -> None:
        """Filter the list on every keystroke of the search field."""
        self.state.search = text
        set_title(text)
        self._render()

    def _end_search(self) -> None:
        """Give the focus back to the list, keeping whatever query is in the field."""
        self.frame.focus_position = "body"
        self._reload()

    def _cycle_sort(self) -> None:
        """Move to the next ordering of tasks inside their project."""
        self.state.sort = self.state.sort.next()
        self._save_settings()
        self._refresh_view()
        self._notify(f"Sorted by {self.state.sort.label}")

    def _toggle_wrap(self) -> None:
        """Switch between wrapping a long task over several lines and truncating it."""
        self.state.wrap = not self.state.wrap
        self._save_settings()
        self._refresh_view()
        self._notify(f"Wrap {'on' if self.state.wrap else 'off'}")

    def _move_task(self, offset: int) -> None:
        """Swap the focused task with its neighbour in the same section, file order only."""
        task = self.list.focused_task
        if task is None:
            return
        if self.state.sort is not SortMode.FILE:
            self._notify(REORDER_HINT)
            return
        neighbour = self.list.neighbour_task(offset)
        if neighbour is None:
            return
        section = self.list.focused_section
        if self._write(lambda: self.store.swap(task, neighbour)):
            self._reload(focus_key=task_key(task), fallback_section=section)

    def _reload(self, focus_key: tuple[str, str] | None = None, fallback_section: str | None = None) -> None:
        """Re-read the file, rebuild the list and put the focus back where it belongs."""
        row = self.list.focused_row
        if focus_key is None and row is not None:
            focus_key = row.key
        if fallback_section is None and row is not None:
            fallback_section = row.section
        position = self.list.position
        self.tasks = self.store.load()
        self._register_colors()
        self.state.keep_expanded({task.to_line() for task in self.tasks})
        self._mtime = self.store.mtime()
        self._render()
        self.list.restore_focus(focus_key, fallback_section, position)

    def _register_colors(self) -> None:
        """Give every project and tag of the file a palette entry, before any row is built.

        Registering the whole file rather than waiting for a word to be drawn is what lets a
        focused row keep these colors: its focus map is read when the row is created.
        """
        palette.register(colors.PROJECT, [f"+{name}" for task in self.tasks for name in task.projects])
        palette.register(colors.CONTEXT, [f"@{name}" for task in self.tasks for name in task.contexts])

    def _refresh_view(self) -> None:
        """Redraw the list after a view-only change, leaving the cursor where it was."""
        row = self.list.focused_row
        position = self.list.position
        self._render()
        self.list.restore_focus(row.key if row else None, row.section if row else None, position)

    def _save_settings(self) -> None:
        """Persist the view preferences now: saving on every change survives a kill -9."""
        settings.save_from(self.state)

    def _follow_expanded(self, task: Task, updated: Task) -> None:
        """Carry an expanded body over to the version of a task that is about to replace it."""
        self.state.move_expanded(task.to_line(), updated.to_line())

    def _render(self) -> None:
        """Rebuild the rows from the current tasks and view state."""
        self.list.rebuild(build_sections(self.tasks, self.state), self.state, self._empty_message())
        self.list_box.set_title(f"tasks · sort: {self.state.sort.label}")
        self._update_status()

    def _empty_message(self) -> str:
        """What to show instead of the list when nothing is visible."""
        if self.state.search:
            return f"No task matches '{self.state.search}'."
        if self.tasks:
            return "Every task is done and hidden. Press c to show completed tasks."
        return "No task yet. Press n to add one."

    def _update_status(self) -> None:
        """Refresh the status line with the file, the counters and the last message."""
        open_count = sum(1 for task in self.tasks if not task.completed)
        parts = [_short_path(self.path), f"{open_count} open", f"{len(self.tasks) - open_count} done"]
        parts.append(f"sort: {self.state.sort.label}")
        if not self.state.show_completed:
            parts.append("completed hidden")
        if not self.state.wrap:
            parts.append("wrap off")
        if not self.state.confirm_without_project:
            parts.append("confirm off")
        markup = [("bold", f"  {self._message}")] if self._message else []
        markup.append(("dim", f"  {' · '.join(parts)}"))
        self.footer.set_status(markup)

    def _notify(self, message: str) -> None:
        """Show a one-off message in the status line until the next key is pressed."""
        self._message = message
        self._update_status()

    def _write(self, action) -> bool:
        """Run a store mutation, reporting a task that vanished from the file instead of crashing."""
        try:
            action()
        except TaskNotFound:
            self._notify("Task is no longer in the file — reloaded")
            self._reload()
            return False
        return True

    def _open_modal(self, widget: urwid.Widget, width=DIALOG_WIDTH, height="pack") -> None:
        """Show a dialog centered over the task list."""
        self._modal = widget
        self.loop.widget = urwid.Overlay(
            widget, self.frame, "center", width, "middle", height,
            min_width=MIN_DIALOG_WIDTH, min_height=MIN_MODAL_HEIGHT,
        )

    def _close_modal(self) -> None:
        """Close the open dialog and give the focus back to the list."""
        self._modal = None
        self.loop.widget = self.frame

    def _sync(self, _loop, _data=None) -> None:
        """Reload when the file changed outside the application, keeping focus and folds."""
        if self.store.mtime() != self._mtime:
            self._reload()
            self._notify("File changed on disk — reloaded")
        self.loop.set_alarm_in(SYNC_INTERVAL, self._sync)


def _prefixed(kind: str, text: str) -> str:
    """A name typed in a rename field, carrying the marker of its kind and nothing else."""
    bare = text.strip().lstrip(PREFIX[kind])
    return f"{PREFIX[kind]}{bare}" if bare else ""


def _renamed_line(kind: str, line: str, old: str, new: str) -> str:
    """A remembered task line once `old` has been renamed to `new`, project or tag alike."""
    task = Task.parse(line)
    renamed = (
        task.with_project_renamed(old, new) if kind == colors.PROJECT else task.with_context_renamed(old, new)
    )
    return renamed.to_line()


def _renamed_section(name: str, old: str, new: str) -> str:
    """A folded section's name once the project `old` has been renamed to `new`."""
    if name == old:
        return new
    if name.startswith(f"{old}{PROJECT_SEPARATOR}"):
        return f"{new}{name[len(old):]}"
    return name


def _dim_box(widget, title: str, title_attr: str, bline: str = "─", top: bool = False) -> urwid.Widget:
    """A framed box whose lines are dimmed and joined to the box above it."""
    return SharedBox(widget, title=title, title_attr=title_attr, bline=bline, top=top)


class SharedBox(urwid.WidgetWrap):
    """A LineBox drawn in the border color, sharing its top line with the box above.

    Only the frame is dimmed: the wrapped widget keeps a plain default attribute, so its own
    colors are untouched.
    """

    def __init__(self, widget, title: str, title_attr: str, bline: str = "─", top: bool = False):
        self._title = title
        self._title_attr = title_attr
        self._inner = urwid.AttrMap(widget, "text")
        self._bline = bline
        self._top = top
        self._bottom_shared = False
        super().__init__(self._build())

    def _build(self) -> urwid.Widget:
        """Rebuild the frame with the corners its neighbours currently call for."""
        corners = {} if self._top else {"tlcorner": "├", "trcorner": "┤"}
        # Dropping the bottom line lets the titled box below draw the single line they share
        bline = "" if self._bottom_shared else self._bline
        box = urwid.LineBox(
            self._inner, title=self._title, title_attr=self._title_attr, bline=bline, **corners
        )
        return urwid.AttrMap(box, "border")

    def set_title(self, title: str) -> None:
        """Change the title shown in the top line."""
        self._title = title
        self._w = self._build()

    def set_bottom_shared(self, shared: bool) -> None:
        """Turn the bottom corners into junctions when a box sits directly below."""
        if shared != self._bottom_shared:
            self._bottom_shared = shared
            self._w = self._build()


def _short_path(path: Path) -> str:
    """The file path, folded back to '~' and elided so it never crowds the counters off the bar."""
    try:
        shortened = f"~/{path.relative_to(Path.home())}"
    except ValueError:
        shortened = str(path)
    return shortened if len(shortened) <= MAX_PATH_WIDTH else f"…/{path.name}"


def _previous_priority(priority: str | None) -> str | None:
    """Return the priority whose forward cycle lands on `priority`."""
    current = None
    for _ in range(len(PRIORITY_LEVELS) + 1):
        if cycle_priority(current, PRIORITY_LEVELS) == priority:
            return current
        current = cycle_priority(current, PRIORITY_LEVELS)
    return None
