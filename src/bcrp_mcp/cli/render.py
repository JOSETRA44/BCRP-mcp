"""Low-level terminal rendering primitives for the `bcrp` CLI.

Design rule: table cells are always *plain* text — colour is applied only to
borders, headers and labels — so column-width arithmetic never has to reason
about invisible ANSI escape sequences.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from typing import Any, Callable

# --- global style state (set once by app.main via configure) ---------------

_COLOR = False
_UNICODE = True

_BOX_UNICODE = {
    "h": "─", "v": "│",
    "tl": "┌", "tm": "┬", "tr": "┐",
    "ml": "├", "mm": "┼", "mr": "┤",
    "bl": "└", "bm": "┴", "br": "┘",
}
_BOX_ASCII = {
    "h": "-", "v": "|",
    "tl": "+", "tm": "+", "tr": "+",
    "ml": "+", "mm": "+", "mr": "+",
    "bl": "+", "bm": "+", "br": "+",
}

MIN_COL_WIDTH = 4
INDENT = "  "


def _stdout_supports_unicode() -> bool:
    enc = getattr(sys.stdout, "encoding", None) or ""
    try:
        "─│┌┐└┘…—·".encode(enc)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def configure(*, color: bool | None = None, ascii_mode: bool = False) -> None:
    """Resolve colour/unicode support once, before any rendering happens."""
    global _COLOR, _UNICODE
    if color is None:
        color = (
            sys.stdout.isatty()
            and os.environ.get("NO_COLOR") is None
            and os.environ.get("TERM") != "dumb"
        )
    _COLOR = bool(color)
    _UNICODE = (not ascii_mode) and _stdout_supports_unicode()


def terminal_width() -> int:
    return shutil.get_terminal_size(fallback=(100, 24)).columns


# --- colour helpers --------------------------------------------------------


def _sgr(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _COLOR else text


def bold(text: str) -> str:
    return _sgr("1", text)


def dim(text: str) -> str:
    return _sgr("2", text)


def cyan(text: str) -> str:
    return _sgr("36", text)


def yellow(text: str) -> str:
    return _sgr("33", text)


def red(text: str) -> str:
    return _sgr("31", text)


# --- value formatting ------------------------------------------------------


def placeholder() -> str:
    return "—" if _UNICODE else "-"


def ellipsis() -> str:
    return "…" if _UNICODE else "..."


def bullet_char() -> str:
    return "·" if _UNICODE else "-"


def fmt_number(value: Any, decimals: int | None = None) -> str:
    """Format a number with thousands separators and a fixed precision.

    `decimals` comes from the BCRP series metadata, so each series prints at
    the precision the central bank actually publishes it at.
    """
    if value is None:
        return placeholder()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if not isinstance(value, (int, float)):
        return str(value)
    if decimals is None:
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text or "0"
    return f"{value:,.{decimals}f}"


def fmt_value(value: Any) -> str:
    if value is None:
        return placeholder()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return fmt_number(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(fmt_value(v) for v in value) if value else placeholder()
    return str(value)


def truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    ell = ellipsis()
    if width <= len(ell):
        return text[:width]
    return text[: width - len(ell)] + ell


# --- tables ----------------------------------------------------------------


@dataclass
class Column:
    key: str
    header: str
    align: str = "left"          # "left" | "right"
    max_width: int | None = None
    format: Callable[[Any], str] | None = None

    def cell(self, row: dict[str, Any]) -> str:
        raw = row.get(self.key)
        return self.format(raw) if self.format else fmt_value(raw)


def table(
    rows: list[dict[str, Any]],
    columns: list[Column],
    indent: str = INDENT,
    width: int | None = None,
) -> str:
    """Render rows as a box-drawn table that always fits the terminal.

    Columns are shrunk widest-first until the table fits, then over-long
    cells are truncated with an ellipsis — so output never wraps into an
    unreadable mess on a narrow terminal.
    """
    if not rows:
        return indent + dim("(no data)")

    box = _BOX_UNICODE if _UNICODE else _BOX_ASCII
    cells = [[c.cell(r) for c in columns] for r in rows]

    widths: list[int] = []
    for i, col in enumerate(columns):
        natural = max([len(col.header)] + [row[i] and len(row[i]) or 0 for row in cells])
        if col.max_width is not None:
            natural = min(natural, col.max_width)
        widths.append(max(natural, 1))

    # Shrink to fit: "| " + cell + " " per column, plus the trailing "|".
    avail = (width or terminal_width()) - len(indent)
    overhead = 3 * len(columns) + 1
    while sum(widths) + overhead > avail:
        widest = max(range(len(widths)), key=lambda i: widths[i])
        if widths[widest] <= MIN_COL_WIDTH:
            break
        widths[widest] -= 1

    def rule(left: str, mid: str, right: str) -> str:
        return left + mid.join(box["h"] * (w + 2) for w in widths) + right

    def row_line(values: list[str]) -> str:
        parts = []
        for value, w, col in zip(values, widths, columns):
            text = truncate(value, w)
            parts.append(text.rjust(w) if col.align == "right" else text.ljust(w))
        sep = " " + box["v"] + " "
        return box["v"] + " " + sep.join(parts) + " " + box["v"]

    lines = [
        dim(rule(box["tl"], box["tm"], box["tr"])),
        bold(row_line([c.header for c in columns])),
        dim(rule(box["ml"], box["mm"], box["mr"])),
    ]
    lines.extend(row_line(row) for row in cells)
    lines.append(dim(rule(box["bl"], box["bm"], box["br"])))

    return "\n".join(indent + line for line in lines)


def columns_for(rows: list[dict[str, Any]]) -> list[Column]:
    """Generic columns for a row set with no bespoke view of its own."""
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    return [
        Column(k, k, align="right" if k in ("value", "count") else "left", max_width=48)
        for k in keys
    ]


# --- block-level output ----------------------------------------------------


def title(text: str) -> None:
    print(bold(text))


def section(text: str) -> None:
    print()
    print(bold(text))


def meta(bits: list[str]) -> None:
    """A single dim line of `a · b · c` metadata under a title."""
    parts = [b for b in bits if b]
    if parts:
        print(dim(f" {bullet_char()} ".join(parts)))


def kv_block(pairs: list[tuple[str, str]], indent: str = INDENT) -> None:
    if not pairs:
        return
    label_w = max(len(label) for label, _ in pairs)
    for label, value in pairs:
        print(f"{indent}{dim(label.ljust(label_w))}  {value}")


def legend(entries: list[tuple[str, str]], indent: str = INDENT) -> None:
    """Code → full-name list, used to keep long names out of table headers."""
    if not entries:
        return
    code_w = max(len(code) for code, _ in entries)
    avail = terminal_width() - len(indent) - code_w - 2
    for code, name in entries:
        print(f"{indent}{cyan(code.ljust(code_w))}  {truncate(name, max(avail, 20))}")


def note(text: str) -> None:
    """Advisory line. Goes to stderr so `-o`/pipes only ever get data."""
    print(dim(text), file=sys.stderr)


def warn(text: str) -> None:
    print(yellow(f"! {text}"), file=sys.stderr)


def error(text: str) -> None:
    print(red(f"Error: {text}"), file=sys.stderr)


def print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))
