"""Tests for todotxt.store: loading, mutating and archiving todo.txt files."""

from todotxt.model import Task
from todotxt.store import TaskNotFound


def read_lines(path):
    """Read the lines of a store-managed file directly, for assertions outside the store's API."""
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def test_load_ignores_blank_lines(store):
    """Blank and whitespace-only lines are skipped, and indices refer to non-blank lines only."""
    store.todo_path.write_text("buy milk\n\n   \nx call mom\n\n", encoding="utf-8")
    tasks = store.load()
    assert [task.description for task in tasks] == ["buy milk", "call mom"]
    assert [task.index for task in tasks] == [0, 1]


def test_load_missing_todo_file_is_empty(store):
    """A todo.txt that does not exist yet is treated as an empty task list."""
    assert store.load() == []


def test_mtime_missing_file_returns_zero(store):
    """mtime() returns 0 for a todo.txt that does not exist yet."""
    assert store.mtime() == 0.0


def test_mtime_reflects_file(store):
    """mtime() reflects the todo file's actual modification time once it exists."""
    store.add(Task.parse("buy milk"))
    assert store.mtime() == store.todo_path.stat().st_mtime


def test_add_appends_task(store):
    """add() appends a new task line to todo.txt."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    assert [task.description for task in store.load()] == ["buy milk", "call mom"]


def test_update_replaces_task_line(store):
    """update() overwrites the stored line for the given task."""
    store.add(Task.parse("buy milk"))
    task = store.load()[0]
    store.update(task.with_priority("A"))
    assert store.load()[0].to_line() == "(A) buy milk"


def test_update_after_toggled_keeps_task_in_place(store):
    """update() with a toggled() task rewrites its line in place, not at the end of the file.

    Regression test: TodoStore._locate() used to look up the task's *new* (already mutated)
    content instead of the line it was parsed from, so update(task.toggled()) raised
    TaskNotFound instead of updating the line.
    """
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    store.add(Task.parse("walk dog"))
    task = store.load()[1]
    store.update(task.toggled())
    assert read_lines(store.todo_path) == ["buy milk", "x call mom", "walk dog"]


def test_update_after_with_priority_keeps_task_in_place(store):
    """update() with a with_priority() task rewrites its line in place."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    store.add(Task.parse("walk dog"))
    task = store.load()[1]
    store.update(task.with_priority("A"))
    assert read_lines(store.todo_path) == ["buy milk", "(A) call mom", "walk dog"]


def test_update_after_with_description_keeps_task_in_place(store):
    """update() with a with_description() task rewrites its line in place."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom +family"))
    store.add(Task.parse("walk dog"))
    task = store.load()[1]
    store.update(task.with_description("call dad +family"))
    assert read_lines(store.todo_path) == ["buy milk", "call dad +family", "walk dog"]


def test_delete_removes_task(store):
    """delete() removes the task's line and leaves the rest untouched."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    tasks = store.load()
    store.delete(tasks[0])
    assert [task.description for task in store.load()] == ["call mom"]


def test_archive_moves_task_to_done_file(store):
    """archive() removes the task from todo.txt and appends it to done.txt."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("x call mom"))
    task = store.load()[1]
    store.archive(task)
    assert [t.description for t in store.load()] == ["buy milk"]
    assert read_lines(store.done_path) == ["x call mom"]


def test_archive_appends_to_existing_done_file(store):
    """archive() appends to done.txt without discarding what was already archived."""
    store.done_path.write_text("x already archived\n", encoding="utf-8")
    store.add(Task.parse("x buy milk"))
    store.archive(store.load()[0])
    assert [line for line in store.done_path.read_text(encoding="utf-8").splitlines()] == [
        "x already archived",
        "x buy milk",
    ]


def test_archive_completed_moves_only_completed_tasks(store):
    """archive_completed() moves every completed task and leaves open ones in place."""
    store.add(Task.parse("x buy milk"))
    store.add(Task.parse("call mom"))
    store.add(Task.parse("x walk dog"))
    count = store.archive_completed()
    assert count == 2
    assert [t.description for t in store.load()] == ["call mom"]
    assert read_lines(store.done_path) == ["x buy milk", "x walk dog"]


def test_archive_completed_returns_zero_when_nothing_completed(store):
    """archive_completed() is a no-op returning 0 when there is nothing to archive."""
    store.add(Task.parse("buy milk"))
    assert store.archive_completed() == 0
    assert [t.description for t in store.load()] == ["buy milk"]


def test_missing_done_file_is_empty(store):
    """A done.txt that does not exist yet stays absent until something is archived."""
    store.add(Task.parse("buy milk"))
    assert not store.done_path.exists()


def test_update_raises_task_not_found_when_task_disappeared(store):
    """update() raises TaskNotFound when the task's line no longer exists anywhere in the file."""
    store.add(Task.parse("buy milk"))
    task = store.load()[0]
    store.todo_path.write_text("call mom\n", encoding="utf-8")
    try:
        store.update(task.with_priority("A"))
        assert False, "expected TaskNotFound"
    except TaskNotFound:
        pass


def test_delete_raises_task_not_found_when_task_disappeared(store):
    """delete() raises TaskNotFound when the task's line no longer exists anywhere in the file."""
    store.add(Task.parse("buy milk"))
    task = store.load()[0]
    store.todo_path.write_text("call mom\n", encoding="utf-8")
    try:
        store.delete(task)
        assert False, "expected TaskNotFound"
    except TaskNotFound:
        pass


def test_locate_falls_back_to_content_match_when_index_moved(store):
    """When the file was edited externally and the task's index no longer matches, update() and
    delete() locate the task by its line content instead."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    task = store.load()[0]

    store.todo_path.write_text("walk dog\nbuy milk\ncall mom\n", encoding="utf-8")

    store.update(task.with_priority("A"))
    lines = store.todo_path.read_text(encoding="utf-8").splitlines()
    assert lines == ["walk dog", "(A) buy milk", "call mom"]


def test_locate_falls_back_to_content_match_on_delete(store):
    """delete() also relocates a task by content when its index has shifted."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    task = store.load()[1]

    store.todo_path.write_text("walk dog\nbuy milk\ncall mom\n", encoding="utf-8")

    store.delete(task)
    lines = store.todo_path.read_text(encoding="utf-8").splitlines()
    assert lines == ["walk dog", "buy milk"]


def test_add_multiline_task_is_a_single_physical_line(store):
    """A multi-line task is stored as exactly one physical line in the file."""
    store.add(Task.parse("first line\\nsecond line"))
    assert read_lines(store.todo_path) == ["first line\\nsecond line"]


def test_update_multiline_task_stays_a_single_physical_line(store):
    """update() on a multi-line task rewrites it in place, still as one physical line."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("first line\\nsecond line"))
    task = store.load()[1]
    store.update(task.with_priority("A"))
    assert read_lines(store.todo_path) == ["buy milk", "(A) first line\\nsecond line"]


def test_multiline_task_roundtrips_through_store_without_loss(store):
    """A multi-line task survives a full load/store cycle with all its lines intact."""
    store.add(Task.parse("first line\\nsecond line\\nthird line"))
    task = store.load()[0]
    assert task.lines == ["first line", "second line", "third line"]


def test_projects_deduplicated_and_sorted(store):
    """projects() returns the unique project names across all tasks, sorted."""
    store.add(Task.parse("buy milk +groceries"))
    store.add(Task.parse("call mom +family"))
    store.add(Task.parse("buy eggs +groceries"))
    assert store.projects() == ["family", "groceries"]


def test_contexts_deduplicated_and_sorted(store):
    """contexts() returns the unique context names across all tasks, sorted."""
    store.add(Task.parse("buy milk @town"))
    store.add(Task.parse("call mom @phone"))
    store.add(Task.parse("buy eggs @town"))
    assert store.contexts() == ["phone", "town"]


def test_swap_exchanges_two_task_lines(store):
    """swap() exchanges the file lines of the two given tasks."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    tasks = store.load()
    store.swap(tasks[0], tasks[1])
    assert read_lines(store.todo_path) == ["call mom", "buy milk"]


def test_swap_leaves_other_lines_untouched(store):
    """swap() changes nothing but the two swapped lines: same line count, same other content."""
    store.add(Task.parse("walk dog"))
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    store.add(Task.parse("water plants"))
    tasks = store.load()
    store.swap(tasks[1], tasks[3])
    assert read_lines(store.todo_path) == ["walk dog", "water plants", "call mom", "buy milk"]


def test_swap_works_on_non_adjacent_tasks(store):
    """swap() reorders two tasks that are not next to each other in the file."""
    store.add(Task.parse("first"))
    store.add(Task.parse("second"))
    store.add(Task.parse("third"))
    store.add(Task.parse("fourth"))
    store.add(Task.parse("fifth"))
    tasks = store.load()
    store.swap(tasks[0], tasks[4])
    assert read_lines(store.todo_path) == ["fifth", "second", "third", "fourth", "first"]


def test_swap_task_with_itself_is_a_no_op(store):
    """Swapping a task with itself leaves the file unchanged."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    task = store.load()[0]
    store.swap(task, task)
    assert read_lines(store.todo_path) == ["buy milk", "call mom"]


def test_swap_raises_task_not_found_when_a_task_disappeared(store):
    """swap() raises TaskNotFound when either task's line no longer exists in the file."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    tasks = store.load()
    store.todo_path.write_text("call mom\n", encoding="utf-8")
    try:
        store.swap(tasks[0], tasks[1])
        assert False, "expected TaskNotFound"
    except TaskNotFound:
        pass


def test_written_file_ends_with_single_trailing_newline(store):
    """The file written to disk ends with exactly one newline and has no stray blank line."""
    store.add(Task.parse("buy milk"))
    store.add(Task.parse("call mom"))
    content = store.todo_path.read_text(encoding="utf-8")
    assert content == "buy milk\ncall mom\n"


def test_rename_project_renames_matching_tasks_and_returns_count(store):
    """rename_project() rewrites every task under the old project and reports how many changed."""
    store.add(Task.parse("buy milk +groceries"))
    store.add(Task.parse("call mom +family"))
    store.add(Task.parse("buy eggs +groceries"))
    count = store.rename_project("groceries", "shopping")
    assert count == 2
    assert [task.description for task in store.load()] == [
        "buy milk +shopping",
        "call mom +family",
        "buy eggs +shopping",
    ]


def test_rename_project_returns_zero_when_nothing_matches(store):
    """rename_project() returns 0 when no task uses the old project name."""
    store.add(Task.parse("buy milk +groceries"))
    assert store.rename_project("nonexistent", "whatever") == 0


def test_rename_project_does_not_rewrite_file_when_nothing_matches(store):
    """rename_project() leaves the file untouched, blank lines and all, when nothing matches."""
    store.todo_path.write_text("buy milk +groceries\n\ncall mom +family\n\n", encoding="utf-8")
    original = store.todo_path.read_text(encoding="utf-8")
    store.rename_project("nonexistent", "whatever")
    assert store.todo_path.read_text(encoding="utf-8") == original


def test_rename_project_preserves_line_order_and_count(store):
    """rename_project() keeps the same number of lines in the same order, renamed in place."""
    store.add(Task.parse("first +a"))
    store.add(Task.parse("second +b"))
    store.add(Task.parse("third +a"))
    store.rename_project("a", "z")
    assert read_lines(store.todo_path) == ["first +z", "second +b", "third +z"]


def test_rename_project_leaves_unrelated_tasks_byte_identical(store):
    """A task with no relation to the renamed project keeps its exact line, unchanged."""
    store.add(Task.parse("(A) buy milk +groceries @town due:2016-05-30"))
    store.add(Task.parse("call mom +family"))
    store.rename_project("groceries", "shopping")
    assert read_lines(store.todo_path)[1] == "call mom +family"


def test_rename_project_ignores_a_line_that_only_needs_normalizing(store):
    """A line in non-canonical order is not counted, nor rewritten, when no project matches.

    Regression test: comparing the renamed line against the raw one made normalizing look like
    a rename, inflating the count and rewriting untouched tasks.
    """
    store.todo_path.write_text("2016-05-20 (A) buy milk +groceries\ncall mom +family\n", encoding="utf-8")

    assert store.rename_project("unrelated", "whatever") == 0
    assert store.todo_path.read_text(encoding="utf-8") == "2016-05-20 (A) buy milk +groceries\ncall mom +family\n"


def test_rename_project_still_renames_a_line_in_non_canonical_order(store):
    """A task whose project matches is renamed even when its line was not canonical to start with."""
    store.todo_path.write_text("2016-05-20 (A) buy milk +groceries\n", encoding="utf-8")

    assert store.rename_project("groceries", "courses") == 1
    assert "+courses" in store.todo_path.read_text(encoding="utf-8")


def test_rename_context_renames_matching_tasks_and_returns_count(store):
    """rename_context() rewrites every task under the old context and reports how many changed."""
    store.add(Task.parse("buy milk @home"))
    store.add(Task.parse("call mom @office"))
    store.add(Task.parse("buy eggs @home"))
    count = store.rename_context("home", "house")
    assert count == 2
    assert [task.description for task in store.load()] == [
        "buy milk @house",
        "call mom @office",
        "buy eggs @house",
    ]


def test_rename_context_returns_zero_when_nothing_matches(store):
    """rename_context() returns 0 when no task uses the old context name."""
    store.add(Task.parse("buy milk @home"))
    assert store.rename_context("nonexistent", "whatever") == 0


def test_rename_context_does_not_rewrite_file_when_nothing_matches(store):
    """rename_context() leaves the file untouched, blank lines and all, when nothing matches."""
    store.todo_path.write_text("buy milk @home\n\ncall mom @office\n\n", encoding="utf-8")
    original = store.todo_path.read_text(encoding="utf-8")
    store.rename_context("nonexistent", "whatever")
    assert store.todo_path.read_text(encoding="utf-8") == original


def test_rename_context_preserves_line_order_and_count(store):
    """rename_context() keeps the same number of lines in the same order, renamed in place."""
    store.add(Task.parse("first @a"))
    store.add(Task.parse("second @b"))
    store.add(Task.parse("third @a"))
    store.rename_context("a", "z")
    assert read_lines(store.todo_path) == ["first @z", "second @b", "third @z"]


def test_rename_context_leaves_unrelated_tasks_byte_identical(store):
    """A task with no relation to the renamed context keeps its exact line, unchanged."""
    store.add(Task.parse("(A) buy milk @home +groceries due:2016-05-30"))
    store.add(Task.parse("call mom @office"))
    store.rename_context("home", "house")
    assert read_lines(store.todo_path)[1] == "call mom @office"


def test_rename_context_ignores_a_line_that_only_needs_normalizing(store):
    """A line in non-canonical order is not counted, nor rewritten, when no context matches.

    Regression test: comparing the renamed line against the raw one made normalizing look like
    a rename, inflating the count and rewriting untouched tasks.
    """
    store.todo_path.write_text("2016-05-20 (A) buy milk @home\ncall mom @office\n", encoding="utf-8")

    assert store.rename_context("unrelated", "whatever") == 0
    assert store.todo_path.read_text(encoding="utf-8") == "2016-05-20 (A) buy milk @home\ncall mom @office\n"


def test_rename_context_still_renames_a_line_in_non_canonical_order(store):
    """A task whose context matches is renamed even when its line was not canonical to start with."""
    store.todo_path.write_text("2016-05-20 (A) buy milk @home\n", encoding="utf-8")

    assert store.rename_context("home", "house") == 1
    assert "@house" in store.todo_path.read_text(encoding="utf-8")
