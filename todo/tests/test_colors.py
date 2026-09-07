"""Tests for todotxt.colors: stable colors for projects and contexts."""

import subprocess
import sys
from pathlib import Path

from todotxt.colors import CONTEXT, CYCLE, PROJECT, attr, color, entries, next_color, root

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_root_of_a_project_is_its_top_level_ancestor():
    """A sub-project's root is the outermost project of its path."""
    assert root(PROJECT, "+phyling.firmware") == "phyling"


def test_root_of_a_context_keeps_its_dotted_name_whole():
    """Contexts have no hierarchy, so a dotted context name is its own root."""
    assert root(CONTEXT, "@phyling.firmware") == "phyling.firmware"


def test_root_absorbs_prefix_and_case():
    """The leading '+'/'@' and any casing are stripped before comparison."""
    assert root(PROJECT, "+Phyling") == "phyling"
    assert root(CONTEXT, "@Phyling") == "phyling"
    assert root(PROJECT, "Phyling") == "phyling"


def test_color_is_stable_across_calls():
    """Two calls for the same name return the same color."""
    assert color(PROJECT, "phyling", {}) == color(PROJECT, "phyling", {})


def test_color_is_stable_across_processes():
    """The default color comes from a checksum, not from a per-process hash seed."""
    here = color(PROJECT, "phyling", {})
    result = subprocess.run(
        [sys.executable, "-c", "from todotxt.colors import color; print(color('project', 'phyling', {}))"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == here


def test_color_of_subproject_matches_its_parent():
    """A sub-project's default color is its top-level project's color."""
    assert color(PROJECT, "phyling.firmware", {}) == color(PROJECT, "phyling", {})


def test_color_of_subproject_follows_an_overridden_parent():
    """An override on the parent project also applies to its sub-projects."""
    overrides = {attr(PROJECT, "phyling"): "#123456"}
    assert color(PROJECT, "phyling.firmware", overrides) == "#123456"


def test_color_override_takes_precedence_over_the_default():
    """A stored override wins over the checksum-derived default."""
    default = color(PROJECT, "phyling", {})
    override = next_color(default)
    overrides = {attr(PROJECT, "phyling"): override}
    assert color(PROJECT, "phyling", overrides) == override


def test_next_color_advances_one_step():
    """next_color() with the default step moves to the following color in the cycle."""
    assert next_color(CYCLE[0]) == CYCLE[1]


def test_next_color_can_step_backwards():
    """A negative step moves backwards through the cycle."""
    assert next_color(CYCLE[1], -1) == CYCLE[0]


def test_next_color_wraps_forward_past_the_end():
    """Stepping forward past the last color wraps around to the first."""
    assert next_color(CYCLE[-1], 1) == CYCLE[0]


def test_next_color_wraps_backward_past_the_start():
    """Stepping backward past the first color wraps around to the last."""
    assert next_color(CYCLE[0], -1) == CYCLE[-1]


def test_next_color_falls_back_to_the_start_of_the_cycle_for_an_unknown_color():
    """A color not in the cycle is treated as if it were the first one."""
    assert next_color("#ffffff", 1) == CYCLE[1]


def test_attr_names_a_project_color():
    """attr() names a project's palette entry as 'project:<root>'."""
    assert attr(PROJECT, "+phyling") == "project:phyling"


def test_attr_names_a_context_color():
    """attr() names a context's palette entry as 'context:<root>'."""
    assert attr(CONTEXT, "@phyling") == "context:phyling"


def test_attr_does_not_collide_across_kinds():
    """A project and a context sharing a name still get distinct palette attributes."""
    assert attr(PROJECT, "work") != attr(CONTEXT, "work")


def test_entries_has_one_entry_per_root_not_per_name():
    """A project and its sub-project collapse into a single palette entry."""
    result = entries(PROJECT, ["a", "a.b", "c"], {})
    assert {row[0] for row in result} == {"project:a", "project:c"}
    assert len(result) == 2


def test_entries_rows_are_six_field_tuples_naming_the_color():
    """Each entry is a 6-uplet of (attr, "", "", "", color, "")."""
    [row] = entries(PROJECT, ["phyling"], {})
    assert row == ("project:phyling", "", "", "", color(PROJECT, "phyling", {}), "")
