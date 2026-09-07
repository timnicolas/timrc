"""Parsing and serialization of todo.txt lines.

Dates are deliberately not interpreted: leading date tokens are preserved verbatim so no
information is lost, but nothing here reads them.

Parsing accepts the priority either before or after the leading dates, since real files use
both, while `to_line` always writes the canonical todo.txt order `x (A) dates description`.
Rewriting a task therefore normalizes its line, which only affects tasks the user acts on:
untouched lines are copied verbatim by the store.
"""

import re
from dataclasses import dataclass, field, replace

PRIORITY_RE = re.compile(r"^\(([A-Z])\)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROJECT_RE = re.compile(r"^\+(\S+)$")
CONTEXT_RE = re.compile(r"^@(\S+)$")
TAG_RE = re.compile(r"^([^\s:]+):([^\s:]+)$")

NO_PROJECT = "(no project)"

# Separator turning "+phyling.firmware" into a sub-project of "+phyling"
PROJECT_SEPARATOR = "."

# Literal backslash-n stored in the file to break a task over several displayed lines.
# todo.txt is strictly one task per line, so the break is spelled out rather than real.
NEWLINE = "\\n"


def project_path(project: str) -> tuple[str, ...]:
    """Split a project into its nesting path, so '+a.b' sits under '+a'."""
    if project == NO_PROJECT:
        return (NO_PROJECT,)
    return tuple(project.lstrip("+").split(PROJECT_SEPARATOR))


def project_ancestors(project: str) -> list[str]:
    """Every parent project of `project`, outermost first: '+a.b.c' gives ['+a', '+a.b']."""
    path = project_path(project)
    if project == NO_PROJECT:
        return []
    return [f"+{PROJECT_SEPARATOR.join(path[:depth])}" for depth in range(1, len(path))]


def _ordered_words(words: list[str]) -> list[str]:
    """Sort a description's words into the canonical order: text, contexts, tags, projects.

    Keeping one order everywhere means a task reads the same on screen as in the file, whoever
    wrote the line. Relative order inside each group is preserved.
    """
    groups: dict[str, list[str]] = {"text": [], "context": [], "tag": [], "project": []}
    for word in words:
        if PROJECT_RE.match(word):
            groups["project"].append(word)
        elif CONTEXT_RE.match(word):
            groups["context"].append(word)
        elif TAG_RE.match(word):
            groups["tag"].append(word)
        else:
            groups["text"].append(word)
    return groups["text"] + groups["context"] + groups["tag"] + groups["project"]


def _normalize_description(description: str) -> str:
    """Put every line of a description in canonical word order, one line at a time.

    Splitting on the newline marker first matters: without it "+proj\\ndetails" would tokenize
    as a single word and be read as a project named "proj\\ndetails".
    """
    return NEWLINE.join(" ".join(_ordered_words(line.split())) for line in description.split(NEWLINE))


def description_words(description: str) -> list[str]:
    """Every word of a description, with the newline marker treated as a separator."""
    return [word for line in description.split(NEWLINE) for word in line.split()]


def _renamed_word(word: str, old: str, new: str) -> str:
    """Rewrite a '+project' word when it names `old` or one of its sub-projects."""
    match = PROJECT_RE.match(word)
    if match and (match.group(1) == old or match.group(1).startswith(f"{old}{PROJECT_SEPARATOR}")):
        return f"+{new}{match.group(1)[len(old):]}"
    return word


def _renamed_context(word: str, old: str, new: str) -> str:
    """Rewrite an '@context' word when it names `old`. Contexts have no sub-names."""
    match = CONTEXT_RE.match(word)
    return f"@{new}" if match and match.group(1) == old else word


@dataclass(frozen=True)
class Task:
    """A single todo.txt line, split into the parts this application acts on."""

    description: str
    completed: bool = False
    priority: str | None = None
    dates: tuple[str, ...] = ()
    index: int = -1
    raw: str = ""  # line this task was parsed from, kept so the store can find it again after edits
    projects: tuple[str, ...] = field(default_factory=tuple)
    contexts: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @classmethod
    def parse(cls, line: str, index: int = -1) -> "Task":
        """Build a Task from a raw todo.txt line."""
        words = line.strip().split()
        completed = False
        priority = None
        dates: list[str] = []

        if words and words[0] == "x":
            completed = True
            words.pop(0)

        # Priority and dates may come in either order depending on the tool that wrote the line
        while words:
            priority_match = PRIORITY_RE.match(words[0])
            if priority_match and priority is None:
                priority = priority_match.group(1)
                words.pop(0)
            elif DATE_RE.match(words[0]):
                dates.append(words.pop(0))
            else:
                break

        description = _normalize_description(" ".join(words))
        words = description_words(description)
        return cls(
            description=description,
            completed=completed,
            priority=priority,
            dates=tuple(dates),
            index=index,
            raw=line.strip(),
            projects=tuple(m.group(1) for m in map(PROJECT_RE.match, words) if m),
            contexts=tuple(m.group(1) for m in map(CONTEXT_RE.match, words) if m),
            tags=tuple((m.group(1), m.group(2)) for m in map(TAG_RE.match, words) if m),
        )

    def to_line(self) -> str:
        """Serialize back to a todo.txt line."""
        parts = []
        if self.completed:
            parts.append("x")
        if self.priority:
            parts.append(f"({self.priority})")
        parts.extend(self.dates)
        parts.append(self.description)
        return " ".join(part for part in parts if part)

    @property
    def lines(self) -> list[str]:
        """The description split on the newline marker: the first line, then the body."""
        return self.description.split(NEWLINE)

    @property
    def summary(self) -> str:
        """The first line of the description, the only one the task list shows collapsed."""
        return self.lines[0]

    @property
    def has_body(self) -> bool:
        """Whether the task carries more lines than the one shown collapsed."""
        return NEWLINE in self.description

    @property
    def project(self) -> str:
        """The project this task is grouped under, or NO_PROJECT when it has none."""
        return f"+{self.projects[0]}" if self.projects else NO_PROJECT

    @property
    def sort_key(self) -> tuple:
        """Order within a project section: open tasks first, then priority, then description."""
        return (
            self.completed,
            self.priority or "[",  # "[" sorts right after "Z", so unprioritized tasks come last
            self.description.lower(),
        )

    def toggled(self) -> "Task":
        """Return this task with its completion state flipped."""
        return replace(self, completed=not self.completed)

    def with_priority(self, priority: str | None) -> "Task":
        """Return this task with a different priority ('A'-'Z', or None to clear it)."""
        return replace(self, priority=priority)

    def with_project_renamed(self, old: str, new: str) -> "Task":
        """Return this task with project `old` renamed to `new`, its sub-projects carried along.

        Renaming "phyling" also renames "phyling.firmware", so a whole subtree moves at once.
        """
        old, new = old.lstrip("+"), new.lstrip("+")
        lines = [" ".join(_renamed_word(word, old, new) for word in line.split()) for line in self.lines]
        return self.with_description(NEWLINE.join(lines))

    def with_context_renamed(self, old: str, new: str) -> "Task":
        """Return this task with context `old` renamed to `new`."""
        old, new = old.lstrip("@"), new.lstrip("@")
        lines = [" ".join(_renamed_context(word, old, new) for word in line.split()) for line in self.lines]
        return self.with_description(NEWLINE.join(lines))

    def with_description(self, description: str) -> "Task":
        """Return this task with a new description, re-deriving projects, contexts and tags.

        A completion marker or priority typed into the text is honored rather than dropped,
        so editing a task the way todo.txt is normally written behaves as expected.
        """
        rebuilt = Task.parse(description, index=self.index)
        return replace(
            self,
            description=rebuilt.description,
            completed=self.completed or rebuilt.completed,
            priority=rebuilt.priority or self.priority,
            dates=self.dates or rebuilt.dates,
            projects=rebuilt.projects,
            contexts=rebuilt.contexts,
            tags=rebuilt.tags,
        )


def cycle_priority(priority: str | None, levels: str) -> str | None:
    """Return the priority after `priority` in `levels`, wrapping back to None at the end."""
    if priority is None:
        return levels[0] if levels else None
    position = levels.find(priority)
    if position == -1 or position == len(levels) - 1:
        return None
    return levels[position + 1]
