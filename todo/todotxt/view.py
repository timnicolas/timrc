"""Grouping, sorting and filtering of tasks into the project sections the TUI and CLI display."""

from dataclasses import dataclass, field
from enum import Enum

from todotxt.model import NO_PROJECT, Task, project_ancestors, project_path


class SortMode(str, Enum):
    """How tasks are ordered inside a project section."""

    FILE = "file"
    PRIORITY = "priority"
    TAG = "tag"
    ALPHA = "alpha"

    @property
    def label(self) -> str:
        """Short name shown in the status bar."""
        return {
            SortMode.FILE: "file order",
            SortMode.PRIORITY: "priority",
            SortMode.TAG: "tag",
            SortMode.ALPHA: "alphabetical",
        }[self]

    def next(self) -> "SortMode":
        """The mode a sort key cycles to next."""
        modes = list(SortMode)
        return modes[(modes.index(self) + 1) % len(modes)]


@dataclass
class ViewState:
    """What the task list currently shows.

    The fold and expand sets are transient, but the sort, the toggles and the confirmation
    preference are saved between runs by `todotxt.settings`.
    """

    show_completed: bool = True
    search: str = ""
    sort: SortMode = SortMode.FILE
    wrap: bool = True
    confirm_without_project: bool = True
    detail_visible: bool = False
    detail_height: int = 8
    collapsed: set[str] = field(default_factory=set)
    expanded: set[str] = field(default_factory=set)

    def toggle_fold(self, section: str) -> None:
        """Fold a section if it is unfolded, unfold it otherwise."""
        self.collapsed ^= {section}

    def toggle_expanded(self, task_line: str) -> None:
        """Show a multi-line task's body if it is hidden, hide it otherwise."""
        self.expanded ^= {task_line}

    def is_expanded(self, task_line: str) -> bool:
        """Whether a task's body is shown under its first line."""
        return task_line in self.expanded

    def keep_expanded(self, task_lines: set[str]) -> None:
        """Forget the tasks that no longer exist, so the set cannot grow without bound."""
        self.expanded &= task_lines

    def move_expanded(self, old_line: str, new_line: str) -> None:
        """Carry an expanded body over to the rewritten version of the same task."""
        if old_line in self.expanded:
            self.expanded.discard(old_line)
            self.expanded.add(new_line)

    def is_collapsed(self, section: str) -> bool:
        """Whether a section is folded itself."""
        return section in self.collapsed

    def is_hidden(self, section: str) -> bool:
        """Whether a section is inside a folded parent, and so must not be drawn at all."""
        return any(parent in self.collapsed for parent in project_ancestors(section))


@dataclass
class Section:
    """A project heading and the tasks filed directly under it.

    Sub-projects are separate sections: '+phyling.firmware' follows '+phyling' with a greater
    depth, so the list can nest and fold them independently.
    """

    name: str
    tasks: list[Task]
    depth: int = 0
    subtree_open: int = 0
    subtree_total: int = 0

    @property
    def label(self) -> str:
        """What the heading shows: the whole project name, nesting being carried by the indent."""
        return self.name

    @property
    def open_count(self) -> int:
        """How many of the section's own tasks are not done yet."""
        return sum(1 for task in self.tasks if not task.completed)


def matches(task: Task, search: str) -> bool:
    """Whether a task matches a search query, case-insensitively."""
    return search.lower() in task.to_line().lower()


def sort_key(task: Task, mode: SortMode) -> tuple:
    """Ordering of a task inside its section for `mode`."""
    if mode is SortMode.FILE:
        return (task.index,)
    if mode is SortMode.ALPHA:
        return (task.completed, task.description.lower())
    if mode is SortMode.TAG:
        # "~" sorts after any tag name, so untagged tasks land at the end of the section
        first_tag = f"{task.tags[0][0]}:{task.tags[0][1]}" if task.tags else "~"
        return (task.completed, first_tag.lower(), task.description.lower())
    return task.sort_key


def build_sections(tasks: list[Task], state: ViewState) -> list[Section]:
    """Group tasks by project, parents before their sub-projects, unfiled ones last.

    Sections are ordered by their project path, so '+a' is immediately followed by '+a.b'. A
    parent that holds no task of its own is still created when one of its sub-projects exists.
    """
    visible = [
        task for task in tasks if (state.show_completed or not task.completed) and matches(task, state.search)
    ]

    grouped: dict[str, list[Task]] = {}
    for task in visible:
        grouped.setdefault(task.project, []).append(task)
        for ancestor in project_ancestors(task.project):
            grouped.setdefault(ancestor, [])

    ordered = sorted(grouped, key=lambda name: (name == NO_PROJECT, tuple(part.lower() for part in project_path(name))))
    sections = [
        Section(name, sorted(grouped[name], key=lambda task: sort_key(task, state.sort)), len(project_path(name)) - 1)
        for name in ordered
    ]
    _count_subtrees(sections, grouped)
    return sections


def _count_subtrees(sections: list[Section], grouped: dict[str, list[Task]]) -> None:
    """Fill in how many tasks each section holds once its sub-projects are counted in."""
    for section in sections:
        descendants = [
            tasks
            for name, tasks in grouped.items()
            if name == section.name or section.name in project_ancestors(name)
        ]
        section.subtree_total = sum(len(tasks) for tasks in descendants)
        section.subtree_open = sum(1 for tasks in descendants for task in tasks if not task.completed)
