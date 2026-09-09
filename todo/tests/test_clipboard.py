"""Tests for todotxt.clipboard: handing text to the system clipboard and the tmux buffer."""

import subprocess

from todotxt import clipboard


class _Recorder:
    """Stands in for subprocess.run, remembering the commands it was asked to run."""

    def __init__(self, returncode: int = 0):
        self.calls: list[tuple[list[str], str]] = []
        self._returncode = returncode

    def __call__(self, command, input="", **_kwargs):
        self.calls.append((command, input))
        return subprocess.CompletedProcess(command, self._returncode)


def test_copy_feeds_the_text_to_the_first_installed_command(monkeypatch):
    """pbcopy is tried first, and the text goes in on its standard input."""
    recorder = _Recorder()
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.setattr(clipboard.shutil, "which", lambda name: name == "pbcopy")
    monkeypatch.setattr(clipboard.subprocess, "run", recorder)
    assert clipboard.copy("hello") is True
    assert recorder.calls == [(["pbcopy"], "hello")]


def test_copy_also_fills_the_tmux_buffer_when_running_inside_tmux(monkeypatch):
    """Under tmux the text is pasteable with prefix + ] as well as from the system clipboard."""
    recorder = _Recorder()
    monkeypatch.setenv("TMUX", "/tmp/tmux-501/default,1,0")
    monkeypatch.setattr(clipboard.shutil, "which", lambda name: name == "pbcopy")
    monkeypatch.setattr(clipboard.subprocess, "run", recorder)
    clipboard.copy("hello")
    assert [command for command, _ in recorder.calls] == [["tmux", "load-buffer", "-"], ["pbcopy"]]


def test_copy_reports_failure_when_the_platform_has_no_clipboard_command(monkeypatch):
    """Saying so beats a key that looks like it worked and copied nothing."""
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.setattr(clipboard.shutil, "which", lambda _name: None)
    assert clipboard.copy("hello") is False
