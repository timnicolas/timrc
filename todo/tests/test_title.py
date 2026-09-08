"""Tests for todotxt.tui.title: the name the pane announces itself under."""

from todotxt.tui.title import pane_title


def test_pane_title_is_the_bare_name_without_a_filter():
    """With nothing filtered the pane is simply 'todo'."""
    assert pane_title("") == "todo"


def test_pane_title_lists_every_filtered_project():
    """Each project of the filter is appended, so the window label says what is on screen."""
    assert pane_title("+phyling +lte") == "todo +phyling +lte"


def test_pane_title_ignores_the_parts_of_the_filter_that_are_not_projects():
    """Contexts, priorities and plain words narrow the view but do not belong in the label."""
    assert pane_title("(A) +phyling @home due:today milk") == "todo +phyling"
