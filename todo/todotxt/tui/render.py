"""Urwid markup for the two kinds of rows the task list shows.

Dates never reach the screen: the model keeps them out of `Task.description`, so rendering the
description is enough to hide them while `to_line()` still writes them back untouched.

Nesting is not part of the markup: a row is indented by the padding the list box wraps it in, so
a task wrapped over several lines keeps its whole block aligned under its project.

A task carrying a body shows only its first line, with a counter of the lines it hides, until it
is expanded — expanding is what puts real line breaks in the markup of a single row.
"""

import re

from todotxt import markdown
from todotxt.config import PRIORITY_ATTR
from todotxt.model import CONTEXT_RE, NO_PROJECT, PROJECT_RE, TAG_RE, Task
from todotxt.view import Section

CHECKED = "[x]"
UNCHECKED = "[ ]"
FOLD_OPEN = "▼"
FOLD_CLOSED = "▶"

# Trails the first line of a collapsed multi-line task, followed by the number of hidden lines
BODY_MARKER = "⋯"

# Columns the lines of an expanded body sit at, so they line up past the checkbox
# Marks the runs markdown left alone, so they can still be colored word by word
PLAIN = "__plain__"
BODY_INDENT = " " * len(f" {UNCHECKED} ")

# Screen columns a section and its tasks shift right per nesting level
INDENT = 2


def task_markup(task: Task, expanded: bool = False) -> list[tuple[str, str]]:
    """Markup for one task: checkbox, priority and colored projects, contexts and tags.

    Only the first line is drawn; the rest of a multi-line task is replaced by a counter unless
    `expanded` asks for the whole body.
    """
    markup = _summary_markup(task)
    if not task.has_body:
        return markup
    if expanded:
        markup.extend(_body_markup(task))
    else:
        markup.append(("dim", f"{BODY_MARKER}{len(task.lines) - 1}"))
    return markup


def section_markup(section: Section, collapsed: bool) -> list[tuple[str, str]]:
    """Markup for a project heading, with a counter of the whole sub-tree while it is folded."""
    marker = FOLD_CLOSED if collapsed else FOLD_OPEN
    counter = f"  {section.subtree_open} open / {section.subtree_total}" if collapsed else ""
    return [("section", f" {marker} {section.label}{counter}")]


def detail_header_markup(task: Task) -> list[tuple[str, str]]:
    """Markup for the detail pane's first line: checkbox, priority, project, contexts and tags.

    It carries everything the body below it leaves out, which is why the pane never lets that
    line be edited in place: 'e' opens the task dialog for it.
    """
    box = CHECKED if task.completed else UNCHECKED
    markup: list[tuple[str, str]] = [("completed" if task.completed else "text", f" {box} ")]
    if task.priority:
        markup.append((PRIORITY_ATTR.get(task.priority, "bold"), _priority_prefix(task)))
    markup.append(("dim" if task.project == NO_PROJECT else "project", f"{task.project} "))
    markup.extend(("context", f"@{context} ") for context in task.contexts)
    markup.extend(("tag", f"{name}:{value} ") for name, value in task.tags)
    return markup


def body_line_markup(line: str, completed: bool) -> list[tuple[str, str]]:
    """Markup for one line of a task body: light markdown, or one flat color when it is done."""
    return [("completed", line)] if completed else _markdown_markup(line)


def row_indent(depth: int) -> int:
    """Screen columns a row at `depth` is padded by."""
    return depth * INDENT


def _summary_markup(task: Task) -> list[tuple[str, str]]:
    """Markup for the first line of a task, the only one a collapsed row shows."""
    if task.completed:
        return [("completed", f" {CHECKED} {_priority_prefix(task)}{task.summary} ")]

    markup = [("text", f" {UNCHECKED} ")]
    if task.priority:
        markup.append((PRIORITY_ATTR.get(task.priority, "bold"), _priority_prefix(task)))
    markup.extend(_words_markup(task.summary, None))
    return markup


def _body_markup(task: Task) -> list[tuple[str, str]]:
    """Markup for the lines an expanded task shows under its first one, each on its own row."""
    markup: list[tuple[str, str]] = []
    for line in task.lines[1:]:
        markup.append(("dim", f"\n{BODY_INDENT}"))
        markup.extend(body_line_markup(line, task.completed))
    return markup


def _markdown_markup(line: str) -> list[tuple[str, str]]:
    """Light markdown for a body line, the runs it leaves plain keeping their word colors."""
    markup: list[tuple[str, str]] = []
    for attr, text in markdown.line_markup(line, base=PLAIN):
        if attr == PLAIN:
            markup.extend(_plain_markup(text))
        else:
            markup.append((attr, text))
    return markup


def _plain_markup(text: str) -> list[tuple[str, str]]:
    """Word colors for a run markdown left alone, keeping its spacing so words stay apart."""
    pieces = re.split(r"(\s+)", text)
    return [(_word_attr(piece) if piece.strip() else "text", piece) for piece in pieces if piece]


def _words_markup(line: str, attr: str | None) -> list[tuple[str, str]]:
    """One markup entry per word, colored by what the word is unless `attr` forces one color."""
    return [(attr or _word_attr(word), f"{word} ") for word in line.split()]


def _priority_prefix(task: Task) -> str:
    """The '(A) ' prefix of a prioritized task, empty when it has no priority."""
    return f"({task.priority}) " if task.priority else ""


def _word_attr(word: str) -> str:
    """The palette attribute a description word is drawn with."""
    if PROJECT_RE.match(word):
        return "project"
    if CONTEXT_RE.match(word):
        return "context"
    if TAG_RE.match(word):
        return "tag"
    return "text"
