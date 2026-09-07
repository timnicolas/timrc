"""Command-line interface for the todo.txt manager.

Task numbers used by every command are `Task.index`: the position of the task's line in
todo.txt (skipping blank lines), as printed by `todo list`. Numbers are not reassigned when
other tasks are added or removed, only when the underlying line moves in the file.

`todo list` shows tasks in file order by default (see `--sort`), grouped by project with
sub-projects nested and indented under their parent. A multi-line task only shows its summary
(the first line) plus a discreet count of the lines it hides; `todo show <n>` reveals the rest.
"""

import argparse
import re
import sys

from todotxt.config import done_path, todo_path
from todotxt.model import Task
from todotxt.store import TaskNotFound, TodoStore
from todotxt.view import Section, SortMode, ViewState, build_sections

INDENT_UNIT = "  "

RESET = "\033[0m"
DIM = "\033[90m"
SECTION_COLOR = "\033[1;33m"
PROJECT_COLOR = "\033[33m"
CONTEXT_COLOR = "\033[35m"
PRIORITY_COLORS = {"A": "\033[1;31m", "B": "\033[33m", "C": "\033[1;32m"}
# Priorities beyond the colored ones are still valid todo.txt, so they fall back to plain bold
PRIORITY_FALLBACK_COLOR = "\033[1m"


def priority_type(value: str) -> str:
    """Validate a --priority argument and normalize it to a single uppercase letter."""
    if not re.fullmatch(r"[A-Za-z]", value):
        raise argparse.ArgumentTypeError("priority must be a single letter (A-Z)")
    return value.upper()


def sort_mode_type(value: str) -> SortMode:
    """Validate a --sort argument and convert it to a SortMode."""
    try:
        return SortMode(value)
    except ValueError:
        valid = ", ".join(mode.value for mode in SortMode)
        raise argparse.ArgumentTypeError(f"invalid choice: {value!r} (choose from {valid})") from None


def find_task(tasks: list[Task], number: int) -> Task:
    """Return the task whose index is `number`, raising TaskNotFound when there is none."""
    for task in tasks:
        if task.index == number:
            return task
    raise TaskNotFound(number)


def colorize_words(description: str) -> str:
    """Highlight +project and @context tokens in a description for terminal output."""
    words = []
    for word in description.split(" "):
        if word.startswith("+") and len(word) > 1:
            words.append(f"{PROJECT_COLOR}{word}{RESET}")
        elif word.startswith("@") and len(word) > 1:
            words.append(f"{CONTEXT_COLOR}{word}{RESET}")
        else:
            words.append(word)
    return " ".join(words)


def body_indicator(task: Task, colored: bool) -> str:
    """A discreet suffix noting how many more lines a multi-line task hides, or "" when there are none."""
    if not task.has_body:
        return ""
    extra = len(task.lines) - 1
    text = f" (+{extra} line{'s' if extra > 1 else ''})"
    return f"{DIM}{text}{RESET}" if colored else text


def format_task_line(task: Task, colored: bool, indent: str = "") -> str:
    """Render one task as a display line, numbered and without its dates.

    A multi-line task shows only its summary (the first line) plus `body_indicator`'s suffix.

    `indent` nests the line under its project section, matching the section's depth.
    """
    marker = "x" if task.completed else " "
    priority = f"({task.priority})" if task.priority else ""
    suffix = body_indicator(task, colored)
    if not colored:
        parts = [marker, priority, task.summary]
        return f"{indent}{task.index:>4}  " + " ".join(part for part in parts if part) + suffix

    if task.completed:
        parts = [marker, priority, task.summary]
        body = " ".join(part for part in parts if part)
        return f"{indent}{task.index:>4}  {DIM}{body}{RESET}{suffix}"

    priority_color = PRIORITY_COLORS.get(task.priority, PRIORITY_FALLBACK_COLOR)
    priority_display = f"{priority_color}{priority}{RESET}" if priority else ""
    parts = [marker, priority_display, colorize_words(task.summary)]
    return f"{indent}{task.index:>4}  " + " ".join(part for part in parts if part) + suffix


def section_header(section: Section, colored: bool) -> str:
    """Render a section's project heading, indented under its parent project when nested."""
    indent = INDENT_UNIT * section.depth
    label = section.label
    return f"{indent}{SECTION_COLOR}{label}{RESET}" if colored else f"{indent}{label}"


def cmd_add(args: argparse.Namespace, store: TodoStore) -> int:
    """Add a new task to the todo file."""
    task = Task.parse(" ".join(args.text))
    if args.priority:
        task = task.with_priority(args.priority)
    store.add(task)
    new_task = store.load()[-1]
    print(f"Added task {new_task.index}: {new_task.to_line()}")
    return 0


def cmd_list(args: argparse.Namespace, store: TodoStore) -> int:
    """List tasks grouped by project, sub-projects nested under their parent, sorted with --sort.

    The filter words share the query language of the interface: '+project' and '@context' terms
    are OR'd within their kind and AND'd across kinds, '(A)' selects a priority, and anything
    else has to appear in the line.
    """
    tasks = store.load()
    state = ViewState(show_completed=args.all, sort=args.sort, search=" ".join(args.filter))
    sections = [section for section in build_sections(tasks, state) if section.tasks]

    if not sections:
        print("No tasks.")
        return 0

    colored = sys.stdout.isatty()
    for i, section in enumerate(sections):
        if i:
            print()
        print(section_header(section, colored))
        indent = INDENT_UNIT * section.depth
        for task in section.tasks:
            print(format_task_line(task, colored, indent))
    return 0


def cmd_show(args: argparse.Namespace, store: TodoStore) -> int:
    """Show a task's full content, with real line breaks, and its metadata."""
    try:
        task = find_task(store.load(), args.number)
    except TaskNotFound:
        print(f"Error: no task numbered {args.number}", file=sys.stderr)
        return 1

    print(f"Task {task.index}")
    print(f"Status: {'done' if task.completed else 'open'}")
    if task.priority:
        print(f"Priority: {task.priority}")
    if task.projects:
        print(f"Projects: {' '.join(f'+{project}' for project in task.projects)}")
    if task.contexts:
        print(f"Contexts: {' '.join(f'@{context}' for context in task.contexts)}")
    if task.tags:
        print(f"Tags: {' '.join(f'{key}:{value}' for key, value in task.tags)}")
    print()
    for line in task.lines:
        print(line)
    return 0


def set_completed(store: TodoStore, task: Task, completed: bool) -> None:
    """Persist a task's completion state."""
    if task.completed == completed:
        return
    store.update(task.toggled())


def cmd_done(args: argparse.Namespace, store: TodoStore) -> int:
    """Mark a task as completed."""
    try:
        task = find_task(store.load(), args.number)
    except TaskNotFound:
        print(f"Error: no task numbered {args.number}", file=sys.stderr)
        return 1
    set_completed(store, task, True)
    print(f"Marked task {args.number} as done.")
    return 0


def cmd_undone(args: argparse.Namespace, store: TodoStore) -> int:
    """Mark a task as not completed."""
    try:
        task = find_task(store.load(), args.number)
    except TaskNotFound:
        print(f"Error: no task numbered {args.number}", file=sys.stderr)
        return 1
    set_completed(store, task, False)
    print(f"Marked task {args.number} as not done.")
    return 0


def cmd_rm(args: argparse.Namespace, store: TodoStore) -> int:
    """Delete a task."""
    try:
        task = find_task(store.load(), args.number)
    except TaskNotFound:
        print(f"Error: no task numbered {args.number}", file=sys.stderr)
        return 1
    store.delete(task)
    print(f"Removed task {args.number}.")
    return 0


def cmd_archive(args: argparse.Namespace, store: TodoStore) -> int:
    """Archive one completed task to done.txt, or all completed tasks when no number is given."""
    if args.number is None:
        count = store.archive_completed()
        print(f"Archived {count} completed task(s).")
        return 0
    try:
        task = find_task(store.load(), args.number)
    except TaskNotFound:
        print(f"Error: no task numbered {args.number}", file=sys.stderr)
        return 1
    store.archive(task)
    print(f"Archived task {args.number}.")
    return 0


def cmd_projects(args: argparse.Namespace, store: TodoStore) -> int:
    """List existing project names."""
    projects = store.projects()
    if not projects:
        print("No projects.")
        return 0
    for project in projects:
        print(f"+{project}")
    return 0


def cmd_normalize(args: argparse.Namespace, store: TodoStore) -> int:
    """Rewrite every task line in its canonical form (normalized word order).

    Untouched lines are already copied verbatim by the store, so only lines whose canonical
    form differs from what is on disk are rewritten, preserving every line's order and count.
    """
    changes = [(task, task.to_line()) for task in store.load() if task.to_line() != task.raw]
    if not changes:
        print("No lines to normalize.")
        return 0

    if args.dry_run:
        for task, normalized in changes:
            print(f"- {task.raw}")
            print(f"+ {normalized}")
        print(f"{len(changes)} line(s) would change.")
        return 0

    for task, _ in changes:
        store.update(task)
    print(f"Normalized {len(changes)} line(s).")
    return 0


def cmd_rename(args: argparse.Namespace, store: TodoStore) -> int:
    """Rename a project across every task, sub-projects included, or a context when given one."""
    context = args.old.startswith("@")
    rewrite = Task.with_context_renamed if context else Task.with_project_renamed
    if args.dry_run:
        # Compared against the task's own canonical line, so normalizing is never shown as a rename
        changes = [
            (task, renamed.to_line())
            for task in store.load()
            if (renamed := rewrite(task, args.old, args.new)).to_line() != task.to_line()
        ]
        if not changes:
            print("No tasks to rename.")
            return 0
        for task, renamed_line in changes:
            print(f"- {task.raw}")
            print(f"+ {renamed_line}")
        print(f"{len(changes)} task(s) would be renamed.")
        return 0

    count = store.rename_context(args.old, args.new) if context else store.rename_project(args.old, args.new)
    if not count:
        print("No tasks to rename.")
        return 0
    print(f"Renamed {count} task(s).")
    return 0


def run_tui(store: TodoStore, search: str = "") -> int:
    """Launch the interactive TUI, importing it lazily since it lives in a sibling module."""
    try:
        from todotxt.tui.app import run
    except ImportError as error:
        print(f"Error: the TUI is not available ({error})", file=sys.stderr)
        return 1
    run(store, search=search)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser and its subcommands."""
    parser = argparse.ArgumentParser(prog="todo", description="A terminal todo.txt manager.")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="add a new task")
    add_parser.add_argument("text", nargs="+", help="task text, may contain +project and @context words")
    add_parser.add_argument("-p", "--priority", type=priority_type, help="priority letter, e.g. A")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="list tasks grouped by project, sub-projects nested")
    list_parser.add_argument("filter", nargs="*", help="only show tasks matching all of these words (case-insensitive)")
    list_parser.add_argument("-a", "--all", action="store_true", help="also show completed tasks")
    list_parser.add_argument(
        "--sort",
        type=sort_mode_type,
        default=SortMode.FILE,
        help=f"how to order tasks inside each section: {', '.join(m.value for m in SortMode)} (default: file)",
    )
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show", help="show a task's full content and metadata")
    show_parser.add_argument("number", type=int, help="task number, as shown by `todo list`")
    show_parser.set_defaults(func=cmd_show)

    done_parser = subparsers.add_parser("done", help="mark a task as completed")
    done_parser.add_argument("number", type=int, help="task number, as shown by `todo list`")
    done_parser.set_defaults(func=cmd_done)

    undone_parser = subparsers.add_parser("undone", help="mark a task as not completed")
    undone_parser.add_argument("number", type=int, help="task number, as shown by `todo list`")
    undone_parser.set_defaults(func=cmd_undone)

    rm_parser = subparsers.add_parser("rm", help="delete a task")
    rm_parser.add_argument("number", type=int, help="task number, as shown by `todo list`")
    rm_parser.set_defaults(func=cmd_rm)

    archive_parser = subparsers.add_parser("archive", help="archive a task, or all completed tasks, to done.txt")
    archive_parser.add_argument(
        "number", type=int, nargs="?", default=None, help="task number to archive; omit to archive all completed tasks"
    )
    archive_parser.set_defaults(func=cmd_archive)

    projects_parser = subparsers.add_parser("projects", help="list existing projects")
    projects_parser.set_defaults(func=cmd_projects)

    normalize_parser = subparsers.add_parser(
        "normalize", help="rewrite the todo file in canonical form (normalized word order)"
    )
    normalize_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="show what would change without writing"
    )
    normalize_parser.set_defaults(func=cmd_normalize)

    rename_parser = subparsers.add_parser(
        "rename", help="rename a project across every task, sub-projects included, or a @context"
    )
    rename_parser.add_argument("old", help="project to rename, or '@context' to rename a context")
    rename_parser.add_argument("new", help="new name, with or without its leading + or @")
    rename_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="show what would change without writing"
    )
    rename_parser.set_defaults(func=cmd_rename)

    # Remembered so main can tell a subcommand from a filter meant for the TUI
    parser.subcommands = set(subparsers.choices)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments and dispatch to the matching command, or launch the TUI.

    Arguments that name no subcommand are a filter for the TUI, so `todo +phyling` opens the
    interface already narrowed to that project.
    """
    parser = build_parser()
    words = sys.argv[1:] if argv is None else argv
    store = TodoStore(todo_path(), done_path())

    if words and not words[0].startswith("-") and words[0] not in _subcommands(parser):
        return run_tui(store, " ".join(words))

    args = parser.parse_args(words)
    if not getattr(args, "command", None):
        return run_tui(store)

    return args.func(args, store)


def _subcommands(parser: argparse.ArgumentParser) -> set[str]:
    """Names argparse knows as subcommands, so anything else can be read as a filter."""
    return {
        name
        for action in parser._subparsers._group_actions  # noqa: SLF001 - argparse exposes no public API
        for name in action.choices
    } if parser._subparsers else set()


if __name__ == "__main__":
    sys.exit(main())
