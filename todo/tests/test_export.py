"""Tests for todotxt.export: the plain-text form of what the list shows."""

from todotxt.export import section_text, sections_text, task_item, task_text
from todotxt.model import NO_PROJECT, Task
from todotxt.view import Section, ViewState, build_sections


def test_task_text_turns_the_stored_marker_into_real_line_breaks():
    """A body is written with a literal '\\n' in the file, which no one wants to paste."""
    task = Task.parse(r"call mum +family\n- [ ] birthday\n- [ ] address", index=0)
    assert task_text(task) == "call mum +family\n- [ ] birthday\n- [ ] address"


def test_task_item_opens_with_an_unchecked_box_and_keeps_the_priority():
    """A pasted task carries the priority it was filed under, the column being gone."""
    assert task_item(Task.parse("(A) call mum +family", index=0)) == "- [ ] (A) call mum +family"


def test_task_item_checks_the_box_of_a_completed_task():
    """A done task pastes as a ticked checkbox rather than a bare line."""
    assert task_item(Task.parse("x call mum +family", index=0)) == "- [x] call mum +family"


def test_task_item_indents_the_body_under_its_bullet():
    """The lines under the first one line up with the text, not with the dash."""
    task = Task.parse(r"call mum +family\nbring a cake", index=0)
    assert task_item(task) == "- [ ] call mum +family\n      bring a cake"


def test_section_text_lists_the_tasks_under_a_heading_naming_the_project():
    """A copied project pastes as a markdown section."""
    tasks = [Task.parse("alpha +work", index=0), Task.parse("x beta +work", index=1)]
    section = Section("+work", tasks)
    assert section_text(section) == "## +work\n- [ ] alpha +work\n- [x] beta +work"


def test_section_text_names_the_unfiled_section_in_words():
    """'(no project)' is an internal marker, so the heading spells it out instead."""
    assert section_text(Section(NO_PROJECT, [Task.parse("alpha", index=0)])) == "## No project\n- [ ] alpha"


def test_sections_text_separates_projects_and_drops_the_empty_ones():
    """A parent that only exists to hold a sub-project has no tasks of its own to paste."""
    tasks = [Task.parse("alpha +a.b", index=0), Task.parse("beta +c", index=1)]
    sections = build_sections(tasks, ViewState())
    assert sections_text(sections) == "## +a.b\n- [ ] alpha +a.b\n\n## +c\n- [ ] beta +c"


def test_sections_text_follows_the_filter_the_list_is_showing():
    """Copying the list copies what is on screen, not the whole file."""
    tasks = [Task.parse("alpha +a", index=0), Task.parse("beta +b", index=1)]
    sections = build_sections(tasks, ViewState(search="+a"))
    assert sections_text(sections) == "## +a\n- [ ] alpha +a"
