"""Tests for todotxt.model: parsing, serialization, sorting and priority helpers."""

import pytest

from todotxt.model import NO_PROJECT, Task, cycle_priority, description_words, project_ancestors, project_path


@pytest.mark.parametrize(
    "line",
    [
        "buy milk",
        "x buy milk",
        "(A) buy milk",
        "x (A) buy milk",
        "2016-05-20 buy milk",
        "x 2016-05-20 2016-05-01 buy milk",
        "(A) 2016-05-20 buy milk",
        "x (A) 2016-05-20 2016-05-01 buy milk",
        "buy milk @town due:2016-05-30 +groceries",
        "(B) call mom @phone @home due:2016-05-01 +family +errands",
        "just a plain description with no metadata",
    ],
)
def test_parse_to_line_roundtrip(line):
    """A line already in canonical order (priority before dates, then text/contexts/tags/projects)
    round-trips unchanged.
    """
    task = Task.parse(line, index=0)
    assert task.to_line() == line


def test_to_line_normalizes_priority_before_dates():
    """to_line() always writes the priority before the dates, normalizing a non-canonical
    (date before priority) input line to the canonical todo.txt order.
    """
    task = Task.parse("2016-05-20 (A) buy milk", index=0)
    assert task.to_line() == "(A) 2016-05-20 buy milk"


def test_to_line_normalization_loses_no_information():
    """Normalizing the token order still preserves the priority, the date and the description."""
    task = Task.parse("2016-05-20 (A) buy milk", index=0)
    assert task.priority == "A"
    assert task.dates == ("2016-05-20",)
    assert task.description == "buy milk"


def test_parse_empty_line():
    """An empty or whitespace-only line parses to an empty description."""
    task = Task.parse("   ", index=0)
    assert task.description == ""
    assert not task.completed
    assert task.priority is None
    assert task.dates == ()
    assert task.projects == ()


def test_parse_extracts_projects_contexts_tags():
    """Projects, contexts and tags are extracted from anywhere in the description."""
    task = Task.parse("call mom +family +errands @phone @home due:2016-05-01", index=0)
    assert task.projects == ("family", "errands")
    assert task.contexts == ("phone", "home")
    assert task.tags == (("due", "2016-05-01"),)


def test_project_returns_no_project_sentinel_when_absent():
    """A task with no +project uses the NO_PROJECT sentinel."""
    task = Task.parse("buy milk @town", index=0)
    assert task.project == NO_PROJECT


def test_project_returns_first_project():
    """A task with multiple +projects is grouped under the first one."""
    task = Task.parse("buy milk +groceries +home", index=0)
    assert task.project == "+groceries"


def test_sort_key_open_before_completed():
    """Open tasks sort before completed ones regardless of description."""
    open_task = Task.parse("zzz open task", index=0)
    done_task = Task.parse("x aaa done task", index=1)
    assert sorted([done_task, open_task], key=lambda t: t.sort_key) == [open_task, done_task]


def test_sort_key_priority_order():
    """Priorities sort A before B before C before unprioritized."""
    a = Task.parse("(A) task", index=0)
    b = Task.parse("(B) task", index=1)
    c = Task.parse("(C) task", index=2)
    none = Task.parse("task", index=3)
    assert sorted([none, c, a, b], key=lambda t: t.sort_key) == [a, b, c, none]


def test_toggled_flips_completion():
    """toggled() flips completed and preserves everything else."""
    task = Task.parse("(A) buy milk +groceries", index=0)
    toggled = task.toggled()
    assert toggled.completed is True
    assert toggled.priority == "A"
    assert toggled.projects == ("groceries",)
    assert toggled.toggled().completed is False


def test_with_priority_sets_and_clears():
    """with_priority() replaces the priority, including clearing it with None."""
    task = Task.parse("buy milk", index=0)
    prioritized = task.with_priority("A")
    assert prioritized.priority == "A"
    assert prioritized.with_priority(None).priority is None


def test_with_description_rederives_projects_and_contexts():
    """with_description() replaces the description and recomputes projects/contexts/tags."""
    task = Task.parse("(A) old description +oldproject @oldcontext", index=0)
    updated = task.with_description("new description +newproject @newcontext due:2016-05-01")
    assert updated.description == "new description @newcontext due:2016-05-01 +newproject"
    assert updated.projects == ("newproject",)
    assert updated.contexts == ("newcontext",)
    assert updated.tags == (("due", "2016-05-01"),)
    assert updated.priority == "A"


def test_with_description_preserves_index():
    """with_description() keeps the task's index unchanged."""
    task = Task.parse("old", index=3)
    assert task.with_description("new").index == 3


def test_with_description_honors_typed_priority():
    """Typing a leading priority into the new description overrides the old one."""
    task = Task.parse("(A) old description", index=0)
    updated = task.with_description("(B) new description")
    assert updated.priority == "B"


def test_with_description_honors_typed_completion_marker():
    """Typing a leading 'x ' into the new description marks the task completed."""
    task = Task.parse("old description", index=0)
    updated = task.with_description("x new description")
    assert updated.completed is True


def test_with_description_cannot_uncomplete_task():
    """Editing the description of a completed task without an 'x' marker keeps it completed."""
    task = Task.parse("x old description", index=0)
    updated = task.with_description("new description")
    assert updated.completed is True


def test_with_description_preserves_existing_dates():
    """Editing the description keeps the task's existing creation date, ignoring any typed in the new text."""
    task = Task.parse("2016-04-01 old description", index=0)
    updated = task.with_description("2020-01-01 new description")
    assert updated.dates == ("2016-04-01",)


def test_with_description_adopts_typed_dates_when_none_existed():
    """A task with no date yet adopts a date typed into the new description."""
    task = Task.parse("old description", index=0)
    updated = task.with_description("2020-01-01 new description")
    assert updated.dates == ("2020-01-01",)


def test_cycle_priority_from_none_starts_at_first_level():
    """Cycling from no priority starts at the first level."""
    assert cycle_priority(None, "ABC") == "A"


def test_cycle_priority_advances_through_levels():
    """Cycling advances one level at a time."""
    assert cycle_priority("A", "ABC") == "B"
    assert cycle_priority("B", "ABC") == "C"


def test_cycle_priority_wraps_to_none_at_end():
    """Cycling past the last level wraps back to None."""
    assert cycle_priority("C", "ABC") is None


def test_cycle_priority_unknown_priority_resets_to_none():
    """A priority outside the configured levels resets to None."""
    assert cycle_priority("Z", "ABC") is None


def test_cycle_priority_empty_levels():
    """With no configured levels, cycling always yields None."""
    assert cycle_priority(None, "") is None
    assert cycle_priority("A", "") is None


def test_parse_normalizes_word_order():
    """Task.parse() reorders a mixed description into text, contexts, tags, projects."""
    task = Task.parse("(A) +phyling due:2026-01-01 relire @bureau le rapport", index=0)
    assert task.to_line() == "(A) relire le rapport @bureau due:2026-01-01 +phyling"


def test_parse_normalization_preserves_relative_order_within_each_group():
    """Several projects, contexts and tags each keep their own relative order after normalization."""
    task = Task.parse("+zebra text here @yak @xray start:2026-01-01 due:2026-02-01 +alpha", index=0)
    assert task.description == "text here @yak @xray start:2026-01-01 due:2026-02-01 +zebra +alpha"
    assert task.projects == ("zebra", "alpha")
    assert task.contexts == ("yak", "xray")
    assert task.tags == (("start", "2026-01-01"), ("due", "2026-02-01"))


def test_parse_normalization_no_metadata_is_unaffected():
    """A description with no context, tag or project is left in its original word order."""
    task = Task.parse("relire le rapport avant demain", index=0)
    assert task.description == "relire le rapport avant demain"


def test_parse_normalization_is_idempotent():
    """Re-parsing an already-normalized line does not change it further."""
    line = Task.parse("(A) +phyling due:2026-01-01 relire @bureau le rapport", index=0).to_line()
    assert Task.parse(line, index=0).to_line() == line


def test_parse_normalization_loses_no_word():
    """Normalizing the word order keeps every word from the original description, just reordered."""
    line = "+phyling due:2026-01-01 relire @bureau le rapport"
    task = Task.parse(line, index=0)
    assert sorted(task.description.split()) == sorted(line.split())


def test_lines_single_line_task():
    """A task with no newline marker has exactly one line, itself."""
    task = Task.parse("buy milk", index=0)
    assert task.lines == ["buy milk"]


def test_lines_two_line_task():
    """A task with one newline marker splits into two lines."""
    task = Task.parse("first line\\nsecond line", index=0)
    assert task.lines == ["first line", "second line"]


def test_lines_three_line_task():
    """A task with two newline markers splits into three lines."""
    task = Task.parse("first\\nsecond\\nthird", index=0)
    assert task.lines == ["first", "second", "third"]


def test_summary_single_line_task_is_the_whole_description():
    """summary equals the description when there is no body."""
    task = Task.parse("buy milk", index=0)
    assert task.summary == "buy milk"


def test_summary_multi_line_task_is_only_the_first_line():
    """summary is only the first line of a multi-line description."""
    task = Task.parse("first line\\nsecond line", index=0)
    assert task.summary == "first line"


def test_has_body_false_for_single_line_task():
    """has_body is false when the description carries no newline marker."""
    task = Task.parse("buy milk", index=0)
    assert task.has_body is False


def test_has_body_true_for_multi_line_task():
    """has_body is true as soon as the description carries a newline marker."""
    task = Task.parse("first\\nsecond", index=0)
    assert task.has_body is True


def test_parse_extracts_project_glued_to_newline_marker():
    """A +project right before the newline marker is still recognized as a project, not
    swallowed into a single word spanning the marker."""
    task = Task.parse("call mom +family\\ndetails here", index=0)
    assert task.projects == ("family",)
    assert task.lines == ["call mom +family", "details here"]


def test_parse_extracts_context_glued_to_newline_marker():
    """A @context right after the newline marker is still recognized as a context, not
    swallowed into a single word spanning the marker."""
    task = Task.parse("call mom\\ndetails @home", index=0)
    assert task.contexts == ("home",)
    assert task.lines == ["call mom", "details @home"]


def test_parse_normalizes_each_line_independently():
    """Canonical word order is applied per line: a word never migrates from one line to another."""
    task = Task.parse("+work relire\\n@bureau le rapport", index=0)
    assert task.lines == ["relire +work", "le rapport @bureau"]


def test_parse_multiline_roundtrip_is_idempotent():
    """Re-parsing an already-normalized multi-line task's line does not change it further."""
    line = Task.parse("+work relire\\n@bureau le rapport", index=0).to_line()
    assert Task.parse(line, index=0).to_line() == line


def test_description_words_splits_across_newline_marker():
    """description_words() treats the newline marker as a word separator, not part of a word."""
    assert description_words("call mom +family\\ndetails @home") == ["call", "mom", "+family", "details", "@home"]


def test_project_path_root_project():
    """A root project's path is a single-element tuple."""
    assert project_path("+home") == ("home",)


def test_project_path_nested_project():
    """A nested project splits on the separator into a multi-segment path."""
    assert project_path("+a.b.c") == ("a", "b", "c")


def test_project_path_no_project_sentinel():
    """NO_PROJECT's path is itself, so it sorts as its own single-segment group."""
    assert project_path(NO_PROJECT) == (NO_PROJECT,)


def test_project_ancestors_root_project_has_none():
    """A root project (no separator) has no ancestors."""
    assert project_ancestors("+phyling") == []


def test_project_ancestors_one_level():
    """A one-level-deep sub-project has exactly its parent as ancestor."""
    assert project_ancestors("+a.b") == ["+a"]


def test_project_ancestors_multiple_levels():
    """A deeply nested project lists every ancestor, outermost first."""
    assert project_ancestors("+a.b.c") == ["+a", "+a.b"]


def test_project_ancestors_no_project_sentinel_has_none():
    """NO_PROJECT has no ancestors."""
    assert project_ancestors(NO_PROJECT) == []


def test_with_project_renamed_simple():
    """A plain project name is renamed in both the projects tuple and the description."""
    task = Task.parse("buy milk +groceries", index=0)
    renamed = task.with_project_renamed("groceries", "shopping")
    assert renamed.projects == ("shopping",)
    assert renamed.description == "buy milk +shopping"


def test_with_project_renamed_carries_subprojects_along():
    """Renaming a project also renames its sub-projects, at any nesting depth."""
    task = Task.parse("build firmware +phyling.firmware", index=0)
    renamed = task.with_project_renamed("phyling", "phy")
    assert renamed.projects == ("phy.firmware",)


def test_with_project_renamed_carries_multiple_levels_of_subprojects():
    """A sub-project several levels deep is still renamed when its top ancestor is."""
    task = Task.parse("deep task +a.b.c", index=0)
    renamed = task.with_project_renamed("a", "z")
    assert renamed.projects == ("z.b.c",)


def test_with_project_renamed_leaves_sibling_with_common_prefix_untouched():
    """A project that merely starts with the same letters, like +phylingX, is not touched."""
    task = Task.parse("other task +phylingX", index=0)
    renamed = task.with_project_renamed("phyling", "phy")
    assert renamed.projects == ("phylingX",)
    assert renamed.description == "other task +phylingX"


def test_with_project_renamed_preserves_multiline():
    """Renaming a project on a multi-line task keeps the newline marker and the line split."""
    task = Task.parse("first line +phyling\\nsecond line here", index=0)
    renamed = task.with_project_renamed("phyling", "phy")
    assert renamed.lines == ["first line +phy", "second line here"]
    assert renamed.has_body is True


def test_with_project_renamed_accepts_names_with_and_without_plus_prefix():
    """Both old and new names may be given with or without their leading '+'."""
    task = Task.parse("buy milk +groceries", index=0)
    assert task.with_project_renamed("+groceries", "+shopping").projects == ("shopping",)
    assert task.with_project_renamed("groceries", "shopping").projects == ("shopping",)
    assert task.with_project_renamed("+groceries", "shopping").projects == ("shopping",)


def test_with_project_renamed_merges_into_an_existing_project():
    """Renaming onto a project name already used by the task merges the two."""
    task = Task.parse("buy milk +groceries +shopping", index=0)
    renamed = task.with_project_renamed("groceries", "shopping")
    assert renamed.projects == ("shopping", "shopping")


def test_with_project_renamed_task_without_project_is_unchanged():
    """A task carrying no project at all is returned unchanged."""
    task = Task.parse("no project here", index=0)
    renamed = task.with_project_renamed("groceries", "shopping")
    assert renamed == task


def test_with_context_renamed_simple():
    """A plain context name is renamed in both the contexts tuple and the description."""
    task = Task.parse("call mom @home", index=0)
    renamed = task.with_context_renamed("home", "house")
    assert renamed.contexts == ("house",)
    assert renamed.description == "call mom @house"


def test_with_context_renamed_leaves_similarly_named_context_untouched():
    """Contexts have no hierarchy, so @homework is not touched when @home is renamed."""
    task = Task.parse("call mom @home @homework", index=0)
    renamed = task.with_context_renamed("home", "house")
    assert renamed.contexts == ("house", "homework")
    assert renamed.description == "call mom @house @homework"


def test_with_context_renamed_preserves_multiline():
    """Renaming a context on a multi-line task keeps the newline marker and the line split."""
    task = Task.parse("first line @home\\nsecond line here", index=0)
    renamed = task.with_context_renamed("home", "house")
    assert renamed.lines == ["first line @house", "second line here"]
    assert renamed.has_body is True


def test_with_context_renamed_accepts_names_with_and_without_at_prefix():
    """Both old and new names may be given with or without their leading '@'."""
    task = Task.parse("call mom @home", index=0)
    assert task.with_context_renamed("@home", "@house").contexts == ("house",)
    assert task.with_context_renamed("home", "house").contexts == ("house",)
    assert task.with_context_renamed("@home", "house").contexts == ("house",)


def test_with_context_renamed_does_not_touch_a_project_of_the_same_name():
    """Renaming a context never touches a project that happens to share its name."""
    task = Task.parse("call mom @work +work", index=0)
    renamed = task.with_context_renamed("work", "office")
    assert renamed.contexts == ("office",)
    assert renamed.projects == ("work",)


def test_with_context_renamed_merges_into_an_existing_context():
    """Renaming onto a context name already used by the task merges the two."""
    task = Task.parse("call mom @home @house", index=0)
    renamed = task.with_context_renamed("home", "house")
    assert renamed.contexts == ("house", "house")


def test_with_context_renamed_task_without_context_is_unchanged():
    """A task carrying no context at all is returned unchanged."""
    task = Task.parse("no context here", index=0)
    renamed = task.with_context_renamed("home", "house")
    assert renamed == task
