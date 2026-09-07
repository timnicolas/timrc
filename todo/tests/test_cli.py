"""Tests for todotxt.cli, exercised as a subprocess via `python -m todotxt`."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cli(args, tmp_path, todo_content=None, done_content=None):
    """Run `python -m todotxt <args>` with TODO_FILE/DONE_FILE pointed at tmp_path."""
    todo_file = tmp_path / "todo.txt"
    done_file = tmp_path / "done.txt"
    if todo_content is not None:
        todo_file.write_text(todo_content, encoding="utf-8")
    if done_content is not None:
        done_file.write_text(done_content, encoding="utf-8")

    env = {"PATH": "/usr/bin:/bin", "TODO_FILE": str(todo_file), "DONE_FILE": str(done_file)}
    result = subprocess.run(
        [sys.executable, "-m", "todotxt", *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result, todo_file, done_file


def test_add_appends_task_to_todo_file(tmp_path):
    """`todo add` appends a new task to todo.txt and reports its number and priority."""
    result, todo_file, _ = run_cli(["add", "buy", "milk", "+groceries", "-p", "a"], tmp_path)
    assert result.returncode == 0
    assert "Added task 0" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "(A) buy milk +groceries\n"


def test_list_shows_tasks_grouped_by_project(tmp_path):
    """`todo list` prints every open task, grouped under its project heading."""
    result, _, _ = run_cli(["list"], tmp_path, todo_content="buy milk +groceries\nx call mom +family\n")
    assert result.returncode == 0
    assert "+groceries" in result.stdout
    assert "buy milk" in result.stdout
    assert "call mom" not in result.stdout


def test_list_all_shows_completed_tasks_too(tmp_path):
    """`todo list --all` also shows completed tasks."""
    result, _, _ = run_cli(["list", "--all"], tmp_path, todo_content="buy milk +groceries\nx call mom +family\n")
    assert result.returncode == 0
    assert "buy milk" in result.stdout
    assert "call mom" in result.stdout


def test_list_filter_matches_keywords(tmp_path):
    """`todo list <word>` only shows tasks whose line contains that word."""
    result, _, _ = run_cli(["list", "milk"], tmp_path, todo_content="buy milk +groceries\nwalk dog +chores\n")
    assert result.returncode == 0
    assert "buy milk" in result.stdout
    assert "walk dog" not in result.stdout


def test_list_with_no_tasks_reports_none(tmp_path):
    """`todo list` on an empty todo file reports there are no tasks."""
    result, _, _ = run_cli(["list"], tmp_path, todo_content="")
    assert result.returncode == 0
    assert "No tasks." in result.stdout


def test_list_shows_summary_and_body_indicator_for_multiline_task(tmp_path):
    """`todo list` shows only the summary of a multi-line task, plus how many lines it hides."""
    result, _, _ = run_cli(["list"], tmp_path, todo_content="first line\\nsecond line\\nthird line +work\n")
    assert result.returncode == 0
    assert "first line" in result.stdout
    assert "second line" not in result.stdout
    assert "third line" not in result.stdout
    assert "(+2 lines)" in result.stdout


def test_list_shows_no_body_indicator_for_single_line_task(tmp_path):
    """`todo list` shows a single-line task exactly as before, with no body indicator."""
    result, _, _ = run_cli(["list"], tmp_path, todo_content="buy milk +groceries\n")
    assert result.returncode == 0
    assert "(+" not in result.stdout


def test_list_multiline_task_is_a_single_output_line(tmp_path):
    """A multi-line task still produces exactly one line of `todo list` output for the task itself."""
    result, _, _ = run_cli(["list"], tmp_path, todo_content="first line\\nsecond line +work\n")
    assert result.returncode == 0
    task_lines = [line for line in result.stdout.splitlines() if "first line" in line]
    assert len(task_lines) == 1


def test_show_prints_full_content_and_metadata(tmp_path):
    """`todo show <n>` prints every line of a multi-line task, with real line breaks, and its metadata."""
    result, _, _ = run_cli(["show", "0"], tmp_path, todo_content="(A) call mom +family\\ndetails @home\n")
    assert result.returncode == 0
    assert "Task 0" in result.stdout
    assert "Priority: A" in result.stdout
    assert "Projects: +family" in result.stdout
    assert "Contexts: @home" in result.stdout
    assert "call mom +family" in result.stdout
    assert "details @home" in result.stdout
    assert "\\n" not in result.stdout


def test_show_with_unknown_number_fails(tmp_path):
    """`todo show <n>` on a number that does not exist returns a non-zero exit code and errors on stderr."""
    result, _, _ = run_cli(["show", "5"], tmp_path, todo_content="buy milk\n")
    assert result.returncode != 0
    assert "no task numbered 5" in result.stderr


def test_add_with_literal_newline_marker_creates_one_physical_line(tmp_path):
    """`todo add` accepts a literal backslash-n typed by the user and stores it as one physical line."""
    result, todo_file, _ = run_cli(["add", "line one\\nline two +test"], tmp_path)
    assert result.returncode == 0
    content = todo_file.read_text(encoding="utf-8")
    assert content.count("\n") == 1
    assert content == "line one\\nline two +test\n"


def test_done_marks_task_completed(tmp_path):
    """`todo done <n>` flips the task at that number to completed."""
    result, todo_file, _ = run_cli(["done", "0"], tmp_path, todo_content="buy milk\n")
    assert result.returncode == 0
    assert "Marked task 0 as done" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "x buy milk\n"


def test_undone_marks_task_not_completed(tmp_path):
    """`todo undone <n>` flips the task at that number back to open."""
    result, todo_file, _ = run_cli(["undone", "0"], tmp_path, todo_content="x buy milk\n")
    assert result.returncode == 0
    assert "Marked task 0 as not done" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "buy milk\n"


def test_rm_deletes_task(tmp_path):
    """`todo rm <n>` removes the task at that number."""
    result, todo_file, _ = run_cli(["rm", "1"], tmp_path, todo_content="buy milk\ncall mom\n")
    assert result.returncode == 0
    assert "Removed task 1" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "buy milk\n"


def test_archive_moves_one_task_to_done_file(tmp_path):
    """`todo archive <n>` moves the given task out of todo.txt and into done.txt."""
    result, todo_file, done_file = run_cli(["archive", "0"], tmp_path, todo_content="x buy milk\ncall mom\n")
    assert result.returncode == 0
    assert "Archived task 0" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "call mom\n"
    assert done_file.read_text(encoding="utf-8") == "x buy milk\n"


def test_archive_without_number_archives_all_completed(tmp_path):
    """`todo archive` with no number archives every completed task."""
    result, todo_file, done_file = run_cli(
        ["archive"], tmp_path, todo_content="x buy milk\ncall mom\nx walk dog\n"
    )
    assert result.returncode == 0
    assert "Archived 2 completed task(s)" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "call mom\n"
    assert done_file.read_text(encoding="utf-8") == "x buy milk\nx walk dog\n"


def test_projects_lists_project_names(tmp_path):
    """`todo projects` lists every distinct project used in todo.txt."""
    result, _, _ = run_cli(["projects"], tmp_path, todo_content="buy milk +groceries\ncall mom +family\n")
    assert result.returncode == 0
    assert "+family" in result.stdout
    assert "+groceries" in result.stdout


def test_projects_with_none_reports_none(tmp_path):
    """`todo projects` on a todo file with no +project reports there are none."""
    result, _, _ = run_cli(["projects"], tmp_path, todo_content="buy milk\n")
    assert result.returncode == 0
    assert "No projects." in result.stdout


def test_done_with_unknown_number_fails(tmp_path):
    """`todo done <n>` on a number that does not exist returns a non-zero exit code and errors on stderr."""
    result, todo_file, _ = run_cli(["done", "5"], tmp_path, todo_content="buy milk\n")
    assert result.returncode != 0
    assert "no task numbered 5" in result.stderr
    assert todo_file.read_text(encoding="utf-8") == "buy milk\n"


def test_rm_with_unknown_number_fails(tmp_path):
    """`todo rm <n>` on a number that does not exist returns a non-zero exit code and errors on stderr."""
    result, todo_file, _ = run_cli(["rm", "42"], tmp_path, todo_content="buy milk\n")
    assert result.returncode != 0
    assert "no task numbered 42" in result.stderr
    assert todo_file.read_text(encoding="utf-8") == "buy milk\n"


def test_rename_renames_project_across_matching_tasks(tmp_path):
    """`todo rename <old> <new>` renames the project on every matching task and reports the count."""
    result, todo_file, _ = run_cli(
        ["rename", "groceries", "shopping"],
        tmp_path,
        todo_content="buy milk +groceries\ncall mom +family\nbuy eggs +groceries\n",
    )
    assert result.returncode == 0
    assert "Renamed 2 task(s)." in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "buy milk +shopping\ncall mom +family\nbuy eggs +shopping\n"


def test_rename_with_no_matching_project_reports_zero(tmp_path):
    """`todo rename <old> <new>` on a project that does not exist changes nothing and says so clearly."""
    result, todo_file, _ = run_cli(
        ["rename", "nonexistent", "whatever"], tmp_path, todo_content="buy milk +groceries\n"
    )
    assert result.returncode == 0
    assert "No tasks to rename." in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "buy milk +groceries\n"


def test_rename_dry_run_shows_changes_without_writing(tmp_path):
    """`todo rename --dry-run` prints the diff it would make but leaves the file untouched."""
    result, todo_file, _ = run_cli(
        ["rename", "groceries", "shopping", "--dry-run"],
        tmp_path,
        todo_content="buy milk +groceries\n",
    )
    assert result.returncode == 0
    assert "- buy milk +groceries" in result.stdout
    assert "+ buy milk +shopping" in result.stdout
    assert "1 task(s) would be renamed." in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "buy milk +groceries\n"


def test_rename_renames_a_context_when_the_old_name_carries_an_at_sign(tmp_path):
    """`todo rename @old @new` renames a context instead of a project, and only the exact one."""
    result, todo_file, _ = run_cli(
        ["rename", "@home", "@work"], tmp_path, todo_content="call mum @home\nread @homework\n"
    )
    assert result.returncode == 0
    assert "Renamed 1 task(s)." in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "call mum @work\nread @homework\n"


def test_rename_dry_run_on_a_context_leaves_the_file_untouched(tmp_path):
    """`todo rename -n @old @new` shows the context rename it would make without writing it."""
    result, todo_file, _ = run_cli(
        ["rename", "@home", "@work", "--dry-run"], tmp_path, todo_content="call mum @home\n"
    )
    assert "+ call mum @work" in result.stdout
    assert todo_file.read_text(encoding="utf-8") == "call mum @home\n"
