"""Unified output layer: one envelope, five formats, one place that writes.

Every command produces the same two things — ``data`` (the full nested dict an
MCP client would get) and ``rows`` (the flat projection that feeds
``table``/``csv``/``md``/``jsonl``). This module turns that pair into whichever
format was asked for and puts it in the right place: **data on stdout, notes
and progress on stderr**, so ``bcrp ... -f jsonl | jq`` never sees decoration.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterator, TextIO

from ..exceptions import error_code_for
from . import render

FORMATS = ("table", "json", "jsonl", "csv", "md")
SOURCE = "bcrp"


@dataclass
class Options:
    """Resolved global flags for one invocation."""

    fmt: str = "table"
    output: Path | None = None
    quiet: bool = False
    no_color: bool = False
    ascii_mode: bool = False
    refresh: bool = False
    no_cache: bool = False


@dataclass
class CommandResult:
    """What every ``cmd_*`` returns: nested payload plus its flat projection."""

    data: Any
    rows: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    view: Callable[[Any], None] | None = None
    title: str = "Result"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def note(message: str, opts: Options) -> None:
    """A progress/status line — stderr only, silenced by ``--quiet``."""
    if not opts.quiet:
        print(message, file=sys.stderr)


def envelope(
    command: str,
    data: Any,
    rows: list[dict[str, Any]],
    cached: bool = False,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The success envelope from spec section 1."""
    return {
        "ok": True,
        "command": command,
        "source": SOURCE,
        "fetched_at": now_iso(),
        "cached": bool(cached),
        "count": len(rows),
        "meta": meta or {},
        "data": data,
        "rows": rows,
    }


def error_envelope(command: str, exc: BaseException) -> dict[str, Any]:
    """The error envelope from spec section 1."""
    return {
        "ok": False,
        "command": command,
        "source": SOURCE,
        "fetched_at": now_iso(),
        "error": {
            "code": error_code_for(exc),
            "message": str(exc) or exc.__class__.__name__,
            "hint": getattr(exc, "hint", "Run `bcrp describe --json` for the command manifest."),
        },
    }


# --- row serialisation -----------------------------------------------------


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    """Union of keys, first-seen order — keeps ragged rows rectangular."""
    names: list[str] = []
    for row in rows:
        for key in row:
            if key not in names:
                names.append(key)
    return names


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    names = _fieldnames(rows)
    writer = csv.DictWriter(buf, fieldnames=names, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _cell(row.get(k)) for k in names})
    return buf.getvalue()


def rows_to_md(rows: list[dict[str, Any]]) -> str:
    """GitHub-flavoured Markdown table."""
    if not rows:
        return "_(no rows)_\n"
    names = _fieldnames(rows)
    lines = [
        "| " + " | ".join(names) + " |",
        "| " + " | ".join("---" for _ in names) + " |",
    ]
    for row in rows:
        cells = [_cell(row.get(name)).replace("|", "\\|") for name in names]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def rows_to_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows)


def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


# --- sinks -----------------------------------------------------------------


@contextmanager
def open_sink(opts: Options) -> Iterator[TextIO]:
    """stdout, or ``-o FILE`` opened for writing."""
    if opts.output is None:
        yield sys.stdout
        return
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    handle = opts.output.open("w", encoding="utf-8", newline="")
    try:
        yield handle
    finally:
        handle.close()


def _write(sink: TextIO, text: str) -> None:
    sink.write(text)
    if text and not text.endswith("\n"):
        sink.write("\n")


# --- buffered emit ---------------------------------------------------------


def emit(command: str, result: CommandResult, opts: Options, cached: bool = False) -> None:
    """Render ``result`` in ``opts.fmt`` to the configured sink."""
    if opts.fmt == "table" and opts.output is None:
        # The human view stays exactly as it was before the arsenal upgrade.
        if result.view is not None:
            result.view(result.data)
        else:
            render.title(result.title)
            print(render.table(result.rows, render.columns_for(result.rows)))
        return

    with open_sink(opts) as sink:
        if opts.fmt == "json":
            _write(sink, to_json(envelope(command, result.data, result.rows, cached, result.meta)))
        elif opts.fmt == "jsonl":
            sink.write(rows_to_jsonl(result.rows))
        elif opts.fmt == "md":
            _write(sink, rows_to_md(result.rows))
        else:  # csv, and `table` redirected to a file
            _write(sink, rows_to_csv(result.rows))

    if opts.output is not None:
        note(f"Wrote {len(result.rows)} rows -> {opts.output}", opts)


def emit_error(command: str, exc: BaseException, opts: Options) -> None:
    """Machine-readable failure on stdout, one human line on stderr."""
    if opts.fmt in ("json", "jsonl"):
        # Errors always go to stdout so a pipeline can parse the failure,
        # even when -o was requested for the (never written) data.
        print(to_json(error_envelope(command, exc)))
    print(f"Error [{error_code_for(exc)}]: {exc}", file=sys.stderr)
    hint = getattr(exc, "hint", None)
    if hint and not opts.quiet:
        print(f"Hint: {hint}", file=sys.stderr)


# --- streaming emit (bulk extraction) --------------------------------------


async def emit_stream(
    command: str,
    rows: AsyncIterator[dict[str, Any]],
    opts: Options,
    cached_fn: Callable[[], bool],
    meta: dict[str, Any] | None = None,
    view: Callable[[list[dict[str, Any]]], None] | None = None,
) -> int:
    """Write rows as they arrive; returns how many were written.

    ``jsonl`` and ``csv`` stream straight through without buffering the whole
    harvest. ``json``/``md``/``table`` need the complete row set before they
    can render, so those buffer.
    """
    if opts.fmt in ("jsonl", "csv"):
        count = 0
        with open_sink(opts) as sink:
            writer: csv.DictWriter | None = None
            async for row in rows:
                if opts.fmt == "jsonl":
                    sink.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
                else:
                    if writer is None:
                        writer = csv.DictWriter(
                            sink, fieldnames=list(row), lineterminator="\n", extrasaction="ignore"
                        )
                        writer.writeheader()
                    writer.writerow({k: _cell(v) for k, v in row.items()})
                count += 1
        if opts.output is not None:
            note(f"Wrote {count} rows -> {opts.output}", opts)
        return count

    buffered = [row async for row in rows]
    result = CommandResult(
        data={"columns": ["series_code", "period", "date", "value"], "rows": buffered},
        rows=buffered,
        meta=meta or {},
        view=(lambda _data: view(buffered)) if view else None,
        title="BCRP long-format export",
    )
    emit(command, result, opts, cached=cached_fn())
    return len(buffered)
