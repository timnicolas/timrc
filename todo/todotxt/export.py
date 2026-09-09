"""Plain-text renderings of what is on screen, for anything that leaves the application.

Markdown is what a task already looks like: bodies are written with headings and checkboxes, so
a copied section reads the same in a message or a note as it does in the list. Priorities and
projects come along, since a line pasted somewhere else has lost the column it was filed under.
"""

from todotxt.model import NO_PROJECT, Task
from todotxt.view import Section

CHECKED = "- [x] "
UNCHECKED = "- [ ] "

# Body lines sit under the bullet that opens their task
BODY_INDENT = " " * len(UNCHECKED)


def task_text(task: Task) -> str:
    """One task on its own: its description, with the line breaks the file stores as a marker."""
    return "\n".join(task.lines)


def task_item(task: Task) -> str:
    """One task as a markdown list item, its body indented under the bullet."""
    head, *body = task.lines
    bullet = CHECKED if task.completed else UNCHECKED
    priority = f"({task.priority}) " if task.priority else ""
    return "\n".join([f"{bullet}{priority}{head}", *(f"{BODY_INDENT}{line}" for line in body)])


def section_text(section: Section) -> str:
    """Every task of one project, under a heading naming it."""
    return "\n".join([_heading(section), *(task_item(task) for task in section.tasks)])


def sections_text(sections: list[Section]) -> str:
    """The whole visible list, project by project, empty projects left out."""
    return "\n\n".join(section_text(section) for section in sections if section.tasks)


def _heading(section: Section) -> str:
    """The markdown heading a project's tasks are listed under."""
    return f"## {'No project' if section.name == NO_PROJECT else section.name}"
