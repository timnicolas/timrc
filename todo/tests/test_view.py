"""Tests for todotxt.view: grouping, filtering and folding of the task list."""

from todotxt.model import NO_PROJECT, Task
from todotxt.view import Section, SortMode, ViewState, build_sections, sort_key


def test_build_sections_groups_by_project():
    """Tasks are grouped into one section per project."""
    tasks = [
        Task.parse("buy milk +groceries", index=0),
        Task.parse("call mom +family", index=1),
        Task.parse("buy eggs +groceries", index=2),
    ]
    sections = build_sections(tasks, ViewState())
    assert {section.name for section in sections} == {"+groceries", "+family"}
    groceries = next(s for s in sections if s.name == "+groceries")
    assert [t.description for t in groceries.tasks] == ["buy milk +groceries", "buy eggs +groceries"]


def test_build_sections_alphabetical_with_no_project_last():
    """Sections are sorted alphabetically by project name, with the unfiled section last."""
    tasks = [
        Task.parse("zeta task +zeta", index=0),
        Task.parse("no project task", index=1),
        Task.parse("alpha task +alpha", index=2),
    ]
    sections = build_sections(tasks, ViewState())
    assert [section.name for section in sections] == ["+alpha", "+zeta", NO_PROJECT]


def test_build_sections_default_sort_is_file_order():
    """With no sort mode specified, tasks keep the order they have in the file, not priority."""
    tasks = [
        Task.parse("(C) low priority", index=0),
        Task.parse("(A) high priority", index=1),
        Task.parse("no priority", index=2),
        Task.parse("(B) medium priority", index=3),
    ]
    sections = build_sections(tasks, ViewState())
    assert [t.description for t in sections[0].tasks] == [
        "low priority",
        "high priority",
        "no priority",
        "medium priority",
    ]


def test_build_sections_sorts_by_priority_within_section():
    """With sort=PRIORITY, tasks are ordered by priority before description."""
    tasks = [
        Task.parse("(C) low priority", index=0),
        Task.parse("(A) high priority", index=1),
        Task.parse("no priority", index=2),
        Task.parse("(B) medium priority", index=3),
    ]
    sections = build_sections(tasks, ViewState(sort=SortMode.PRIORITY))
    assert [t.description for t in sections[0].tasks] == [
        "high priority",
        "medium priority",
        "low priority",
        "no priority",
    ]


def test_build_sections_hides_completed_when_show_completed_false():
    """show_completed=False filters out completed tasks."""
    tasks = [
        Task.parse("open task +work", index=0),
        Task.parse("x done task +work", index=1),
    ]
    sections = build_sections(tasks, ViewState(show_completed=False))
    assert len(sections) == 1
    assert [t.description for t in sections[0].tasks] == ["open task +work"]


def test_build_sections_drops_section_left_empty_by_filter():
    """A section whose only task gets filtered out disappears entirely."""
    tasks = [
        Task.parse("open task +work", index=0),
        Task.parse("x done task +chores", index=1),
    ]
    sections = build_sections(tasks, ViewState(show_completed=False))
    assert [section.name for section in sections] == ["+work"]


def test_build_sections_search_filters_case_insensitively():
    """search filters tasks by a case-insensitive substring match."""
    tasks = [
        Task.parse("Buy Milk +groceries", index=0),
        Task.parse("call mom +family", index=1),
    ]
    sections = build_sections(tasks, ViewState(search="MILK"))
    assert len(sections) == 1
    assert [t.description for t in sections[0].tasks] == ["Buy Milk +groceries"]


def test_build_sections_search_matches_whole_line():
    """search matches against the whole rendered line, not just the description."""
    tasks = [
        Task.parse("(A) buy milk +groceries @town", index=0),
        Task.parse("call mom +family", index=1),
    ]
    sections = build_sections(tasks, ViewState(search="@town"))
    assert len(sections) == 1
    assert [t.description for t in sections[0].tasks] == ["buy milk @town +groceries"]


def test_view_state_toggle_fold_and_is_collapsed():
    """toggle_fold() flips a section's collapsed state, tracked by is_collapsed()."""
    state = ViewState()
    assert not state.is_collapsed("+work")
    state.toggle_fold("+work")
    assert state.is_collapsed("+work")
    state.toggle_fold("+work")
    assert not state.is_collapsed("+work")


def test_section_open_count():
    """open_count counts only the tasks that are not completed."""
    section = Section(
        name="+work",
        tasks=[
            Task.parse("open one", index=0),
            Task.parse("x done one", index=1),
            Task.parse("open two", index=2),
        ],
    )
    assert section.open_count == 2


def test_section_open_count_all_completed():
    """open_count is 0 when every task in the section is completed."""
    section = Section(name="+work", tasks=[Task.parse("x done one", index=0)])
    assert section.open_count == 0


def test_sort_mode_next_cycles_through_all_modes_and_wraps():
    """next() steps through FILE, PRIORITY, TAG, ALPHA in order and wraps back to FILE."""
    assert SortMode.FILE.next() == SortMode.PRIORITY
    assert SortMode.PRIORITY.next() == SortMode.TAG
    assert SortMode.TAG.next() == SortMode.ALPHA
    assert SortMode.ALPHA.next() == SortMode.FILE


def test_sort_key_file_mode_respects_file_index():
    """sort_key() with FILE orders tasks by their index, regardless of description."""
    second = Task.parse("second task", index=5)
    first = Task.parse("first task", index=2)
    assert sorted([second, first], key=lambda t: sort_key(t, SortMode.FILE)) == [first, second]


def test_sort_key_priority_mode_orders_by_priority_then_description():
    """sort_key() with PRIORITY matches Task.sort_key: priority order, unprioritized last."""
    a = Task.parse("(A) task", index=0)
    b = Task.parse("(B) task", index=1)
    none = Task.parse("task", index=2)
    assert sorted([none, b, a], key=lambda t: sort_key(t, SortMode.PRIORITY)) == [a, b, none]


def test_sort_key_alpha_mode_orders_open_before_completed_then_alphabetically():
    """sort_key() with ALPHA keeps open tasks before completed ones, alphabetical within each group."""
    zeta_open = Task.parse("zeta task", index=0)
    alpha_open = Task.parse("alpha task", index=1)
    alpha_done = Task.parse("x alpha done", index=2)
    ordered = sorted([alpha_done, zeta_open, alpha_open], key=lambda t: sort_key(t, SortMode.ALPHA))
    assert ordered == [alpha_open, zeta_open, alpha_done]


def test_sort_key_tag_mode_sends_untagged_tasks_last():
    """sort_key() with TAG orders by first tag, and tasks with no tag land at the end."""
    untagged = Task.parse("write report", index=0)
    later_due = Task.parse("call mom due:2026-01-01", index=1)
    earlier_due = Task.parse("email boss due:2025-01-01", index=2)
    ordered = sorted([untagged, later_due, earlier_due], key=lambda t: sort_key(t, SortMode.TAG))
    assert ordered == [earlier_due, later_due, untagged]


def test_build_sections_creates_subproject_section_after_parent():
    """A sub-project section follows its parent, both present as separate sections."""
    tasks = [
        Task.parse("root task +a", index=0),
        Task.parse("child task +a.b", index=1),
    ]
    sections = build_sections(tasks, ViewState())
    assert [section.name for section in sections] == ["+a", "+a.b"]
    assert sections[0].depth == 0
    assert sections[1].depth == 1


def test_build_sections_synthesizes_parent_without_its_own_task():
    """A parent section is created even when only its sub-project has tasks."""
    tasks = [Task.parse("child only +a.b", index=0)]
    sections = build_sections(tasks, ViewState())
    assert [section.name for section in sections] == ["+a", "+a.b"]
    parent = sections[0]
    assert parent.tasks == []
    assert parent.depth == 0


def test_section_label_is_the_full_project_name_at_every_depth():
    """label always spells the whole project out, nesting being carried by the indent instead."""
    tasks = [Task.parse("child task +a.b.c", index=0)]
    root, middle, leaf = build_sections(tasks, ViewState())
    assert root.label == "+a"
    assert middle.label == "+a.b"
    assert leaf.label == "+a.b.c"


def test_build_sections_subtree_counts_include_descendants():
    """subtree_total/subtree_open count a section's own tasks plus every descendant's."""
    tasks = [
        Task.parse("root open +a", index=0),
        Task.parse("x root done +a", index=1),
        Task.parse("child open +a.b", index=2),
        Task.parse("grandchild open +a.b.c", index=3),
    ]
    sections = build_sections(tasks, ViewState())
    root = next(s for s in sections if s.name == "+a")
    child = next(s for s in sections if s.name == "+a.b")
    grandchild = next(s for s in sections if s.name == "+a.b.c")
    assert root.subtree_total == 4
    assert root.subtree_open == 3
    assert child.subtree_total == 2
    assert child.subtree_open == 2
    assert grandchild.subtree_total == 1
    assert grandchild.subtree_open == 1


def test_is_hidden_differs_from_is_collapsed_on_folded_parent():
    """is_hidden() is true for a section under a folded ancestor, unlike is_collapsed()."""
    state = ViewState()
    state.toggle_fold("+a")
    assert state.is_collapsed("+a")
    assert not state.is_collapsed("+a.b")
    assert not state.is_hidden("+a")
    assert state.is_hidden("+a.b")


def test_is_hidden_propagates_through_multiple_nesting_levels():
    """Folding a grandparent hides every deeper descendant, not just its direct child."""
    state = ViewState()
    state.toggle_fold("+a")
    assert state.is_hidden("+a.b.c")


def test_is_hidden_only_reacts_to_ancestors_not_the_section_itself():
    """Folding a section only hides its descendants, and does not mark it hidden itself."""
    state = ViewState()
    state.toggle_fold("+a.b")
    assert not state.is_hidden("+a.b")
    assert state.is_hidden("+a.b.c")
    assert not state.is_hidden("+a")


def test_build_sections_multiline_task_grouped_by_first_line_project():
    """A multi-line task is filed under the project named in its first line."""
    tasks = [Task.parse("call mom +family\\ndetails here", index=0)]
    sections = build_sections(tasks, ViewState())
    assert [section.name for section in sections] == ["+family"]


def test_build_sections_search_matches_word_in_task_body():
    """search finds a word that only appears in a multi-line task's body, not its summary."""
    tasks = [
        Task.parse("call mom\\ndetails about the reunion", index=0),
        Task.parse("buy milk", index=1),
    ]
    sections = build_sections(tasks, ViewState(search="reunion"))
    assert len(sections) == 1
    assert sections[0].tasks[0].summary == "call mom"


def test_build_sections_no_project_last_with_subprojects_present():
    """NO_PROJECT still sorts after every project section, including synthesized sub-projects."""
    tasks = [
        Task.parse("unfiled task", index=0),
        Task.parse("child task +a.b", index=1),
    ]
    sections = build_sections(tasks, ViewState())
    assert [section.name for section in sections] == ["+a", "+a.b", NO_PROJECT]
