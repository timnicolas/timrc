"""Tests for todotxt.tui.render: the markup the task list is drawn from."""

from todotxt.tui.render import section_counter_markup, section_markup
from todotxt.view import Section


def _text(markup: list[tuple[str, str]]) -> str:
    """The markup flattened back to the string it puts on screen."""
    return "".join(text for _, text in markup)


def test_section_counter_shows_the_share_of_the_subtree_that_is_done():
    """Two open out of five means three are done, that is 60 %."""
    section = Section("+a", [], subtree_open=2, subtree_total=5)
    assert _text(section_counter_markup(section)) == "  60% - 2 open / 5"


def test_section_counter_is_dimmed():
    """The counter is an annotation, drawn in the same grey as the status line."""
    assert [attr for attr, _ in section_counter_markup(Section("+a", [], 0, 1, 1))] == ["dim"]


def test_section_counter_is_drawn_whether_the_section_is_folded_or_not():
    """Folding only swaps the marker: the counter stays put."""
    section = Section("+a", [], subtree_open=1, subtree_total=4)
    assert _text(section_markup(section, collapsed=True)) == " ▶ +a  75% - 1 open / 4"
    assert _text(section_markup(section, collapsed=False)) == " ▼ +a  75% - 1 open / 4"
