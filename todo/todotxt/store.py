"""Reading and writing the todo.txt and done.txt files."""

import os
import tempfile
from pathlib import Path

from todotxt.model import Task


class TaskNotFound(Exception):
    """Raised when a task can no longer be located in the file it came from."""


class TodoStore:
    """Persistence for a todo.txt file and its companion done.txt archive.

    Every mutation re-reads the file, applies the change and writes it back atomically, so
    edits made outside the application are never silently overwritten.
    """

    def __init__(self, todo_path: Path, done_path: Path):
        self.todo_path = Path(todo_path)
        self.done_path = Path(done_path)

    def load(self) -> list[Task]:
        """Read all tasks, skipping blank lines. Indices refer to non-blank lines only."""
        return [Task.parse(line, index=i) for i, line in enumerate(self._read_lines())]

    def mtime(self) -> float:
        """Last modification time of the todo file, or 0 when it does not exist yet."""
        try:
            return self.todo_path.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    def projects(self) -> list[str]:
        """All project names currently used, without their '+' prefix, sorted."""
        return sorted({project for task in self.load() for project in task.projects})

    def contexts(self) -> list[str]:
        """All context names currently used, without their '@' prefix, sorted."""
        return sorted({context for task in self.load() for context in task.contexts})

    def add(self, task: Task) -> None:
        """Append a new task to the todo file."""
        lines = self._read_lines()
        lines.append(task.to_line())
        self._write_lines(self.todo_path, lines)

    def update(self, task: Task) -> None:
        """Replace the stored line `task` came from with its current content."""
        lines = self._read_lines()
        lines[self._locate(task, lines)] = task.to_line()
        self._write_lines(self.todo_path, lines)

    def rename_project(self, old: str, new: str) -> int:
        """Rename a project across every task, its sub-projects included. Returns tasks changed."""
        return self._rename(lambda task: task.with_project_renamed(old, new))

    def rename_context(self, old: str, new: str) -> int:
        """Rename a context across every task. Returns how many tasks changed."""
        return self._rename(lambda task: task.with_context_renamed(old, new))

    def _rename(self, rewrite) -> int:
        """Apply a task rewrite to the whole file, counting only the lines it really changes."""
        lines = self._read_lines()
        changed = 0
        for position, line in enumerate(lines):
            task = Task.parse(line)
            renamed = rewrite(task)
            # Compared after parsing on both sides, so normalizing a line is never read as a rename
            if renamed.to_line() != task.to_line():
                lines[position] = renamed.to_line()
                changed += 1
        if changed:
            self._write_lines(self.todo_path, lines)
        return changed

    def swap(self, first: Task, second: Task) -> None:
        """Exchange the file lines of two tasks, so they can be reordered by hand."""
        lines = self._read_lines()
        first_position, second_position = self._locate(first, lines), self._locate(second, lines)
        lines[first_position], lines[second_position] = lines[second_position], lines[first_position]
        self._write_lines(self.todo_path, lines)

    def delete(self, task: Task) -> None:
        """Remove a task from the todo file."""
        lines = self._read_lines()
        del lines[self._locate(task, lines)]
        self._write_lines(self.todo_path, lines)

    def archive(self, task: Task) -> None:
        """Move one task out of the todo file and append it to done.txt."""
        lines = self._read_lines()
        position = self._locate(task, lines)
        archived = lines.pop(position)
        self._write_lines(self.todo_path, lines)
        self._write_lines(self.done_path, self._read_lines(self.done_path) + [archived])

    def archive_completed(self) -> int:
        """Move every completed task to done.txt. Returns how many were archived."""
        lines = self._read_lines()
        kept = [line for line in lines if not Task.parse(line).completed]
        archived = [line for line in lines if Task.parse(line).completed]
        if archived:
            self._write_lines(self.todo_path, kept)
            self._write_lines(self.done_path, self._read_lines(self.done_path) + archived)
        return len(archived)

    def _locate(self, task: Task, lines: list[str]) -> int:
        """Find the line a task belongs to, falling back to a content match if it moved.

        Matching uses the line the task was parsed from, not its current content, so a task
        that was edited in memory is still found at the line it came from.
        """
        line = task.raw or task.to_line()
        if 0 <= task.index < len(lines) and lines[task.index] == line:
            return task.index
        try:
            return lines.index(line)
        except ValueError:
            raise TaskNotFound(line) from None

    def _read_lines(self, path: Path | None = None) -> list[str]:
        """Read non-blank stripped lines from a file, treating a missing file as empty."""
        try:
            content = (path or self.todo_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        return [stripped for line in content.splitlines() if (stripped := line.strip())]

    @staticmethod
    def _write_lines(path: Path, lines: list[str]) -> None:
        """Write lines to a file atomically, so an interrupted write cannot truncate it."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write("".join(f"{line}\n" for line in lines))
            temp_path = handle.name
        os.replace(temp_path, path)
