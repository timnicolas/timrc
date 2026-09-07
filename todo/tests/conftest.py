"""Shared fixtures for the todotxt test suite."""

import pytest

from todotxt.store import TodoStore


@pytest.fixture
def store(tmp_path):
    """A TodoStore pointed at fresh todo.txt/done.txt paths under tmp_path, neither created yet."""
    return TodoStore(tmp_path / "todo.txt", tmp_path / "done.txt")
