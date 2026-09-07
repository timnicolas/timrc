"""Terminal setup that lets the TUI tell Shift+Enter apart from a plain Enter.

Two separate things are needed, and urwid does neither on its own: the terminal has to be asked
for the modifyOtherKeys protocol, otherwise a multiplexer folds Shift+Enter back onto a bare
carriage return, and urwid's input table has to learn to decode what the terminal then sends.

The mode outlives the process, so a terminal left in it keeps injecting ';2;13~' into whatever
shell comes next. Every way out therefore has to undo it: the caller's own cleanup, a signal, or
the interpreter shutting down. Only SIGKILL escapes, since it cannot be caught.
"""

import atexit
import signal
import sys

from urwid.display import escape

# xterm modifyOtherKeys, reporting a modified key as CSI 27 ; modifier ; keycode ~.
# Level 1 escapes only the keys with no plain encoding, so ctrl-a and friends keep arriving
# as ordinary control codes; level 2 would escape those too and urwid would show garbage.
MODIFY_OTHER_KEYS_ON = "\x1b[>4;1m"
MODIFY_OTHER_KEYS_OFF = "\x1b[>4;0m"

# The keys the protocol escapes, and the name each one should decode to. A space stays a space
# whatever modifier came with it: in a text field there is nothing else it could mean.
ESCAPED_KEYCODES = {13: "enter", 9: "tab", 32: " ", 8: "backspace"}
MODIFIER_DIGITS = "2345678"

# Signals that end the process quietly enough to restore the terminal on the way out
RESTORED_SIGNALS = (signal.SIGTERM, signal.SIGHUP)

_enabled = False


def patch_input_sequences() -> None:
    """Teach urwid to decode the sequences the modifyOtherKeys protocol escapes.

    urwid compiles its sequence table into a trie when the module is imported, so appending to
    the table is not enough: the trie has to be rebuilt from it.
    """
    known = set(escape.input_sequences)
    for digit in MODIFIER_DIGITS:
        for keycode, name in ESCAPED_KEYCODES.items():
            key = name if name == " " else f"{escape.escape_modifier(digit)}{name}"
            entry = (f"[27;{digit};{keycode}~", key)
            if entry not in known:
                escape.input_sequences.append(entry)
    escape.input_trie = escape.KeyqueueTrie(escape.input_sequences)


def enable_extended_keys() -> None:
    """Ask the terminal to report Shift+Enter apart. Ignored by terminals that do not know it.

    Arms at the same time the two exits the caller cannot wrap in a `finally`: a signal and the
    interpreter shutting down.
    """
    global _enabled

    for number in RESTORED_SIGNALS:
        signal.signal(number, _restore_on_signal)
    atexit.register(disable_extended_keys)
    _enabled = True
    sys.stdout.write(MODIFY_OTHER_KEYS_ON)
    sys.stdout.flush()


def disable_extended_keys() -> None:
    """Put the terminal back to its usual key reporting, once, however often it is asked for.

    Called from a `finally`, from a signal handler and from `atexit`, so it has to survive both
    being run twice and a stdout already closed by the interpreter.
    """
    global _enabled

    if not _enabled:
        return
    _enabled = False
    try:
        sys.stdout.write(MODIFY_OTHER_KEYS_OFF)
        sys.stdout.flush()
    except ValueError:
        pass


def _restore_on_signal(number: int, _frame) -> None:
    """Restore the terminal, then die of `number` exactly as the process would have without us."""
    disable_extended_keys()
    signal.signal(number, signal.SIG_DFL)
    signal.raise_signal(number)
