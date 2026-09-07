"""Light markdown rendering for the body of a multi-line task.

Marks are never hidden: a task body is a todo.txt line the user also reads and edits in a plain
editor, so what is on screen matches what is in the file, character for character. Marks are only
dimmed, and the text they carry is styled.
"""

import re

HEADING_RE = re.compile(r"^(#{1,6})(\s+)(.*)$")
BULLET_RE = re.compile(r"^(\s*)([-*+]|\d+\.)(\s+)(.*)$")
QUOTE_RE = re.compile(r"^(>\s?)(.*)$")

# Inline marks, longest first so "**bold**" is not read as two italics
INLINE_RE = re.compile(r"(`[^`\n]+`|\*\*[^*\n]+\*\*|__[^_\n]+__|\*[^*\n]+\*|_[^_\n]+_)")

INLINE_ATTRS = (
    ("`", "md_code"),
    ("**", "md_bold"),
    ("__", "md_bold"),
    ("*", "md_italic"),
    ("_", "md_italic"),
)

MARK = "md_mark"


def line_markup(line: str, base: str = "text") -> list[tuple[str, str]]:
    """Urwid markup for one line of a task body, `base` styling everything unmarked."""
    heading = HEADING_RE.match(line)
    if heading:
        hashes, space, text = heading.groups()
        return [(MARK, f"{hashes}{space}"), ("md_heading", text)]

    quote = QUOTE_RE.match(line)
    if quote:
        marker, text = quote.groups()
        return [(MARK, marker), ("md_quote", text)]

    bullet = BULLET_RE.match(line)
    if bullet:
        indent, marker, space, rest = bullet.groups()
        return [(MARK, f"{indent}{marker}{space}"), *_inline_markup(rest, base)]

    return _inline_markup(line, base)


def _inline_markup(text: str, base: str) -> list[tuple[str, str]]:
    """Split a line on its inline marks, keeping the marks visible but dimmed."""
    markup: list[tuple[str, str]] = []
    for piece in INLINE_RE.split(text):
        if not piece:
            continue
        markup.extend(_piece_markup(piece, base))
    return markup or [(base, "")]


def _piece_markup(piece: str, base: str) -> list[tuple[str, str]]:
    """A marked run as dimmed opening mark, styled text and dimmed closing mark."""
    for mark, attr in INLINE_ATTRS:
        if len(piece) > 2 * len(mark) and piece.startswith(mark) and piece.endswith(mark):
            return [(MARK, mark), (attr, piece[len(mark):-len(mark)]), (MARK, mark)]
    return [(base, piece)]
