"""Bulk extraction: full histories and tidy long-format multi-series exports.

BCRP is not a paginated API — a series is addressed by *date range*, and a
request with no range silently returns only a trailing window (the last ~60
monthly or ~97 daily observations). "Fetch everything" therefore means
"request the widest range this frequency allows, then trim the `n.d.` padding
BCRP puts on both ends".

The long-format export is the piece an analyst agent actually wants: many
series, any mix of frequencies, collapsed into one tidy
``series_code, period, date, value`` table. Each code is fetched on its own —
BCRP reorders series in multi-code requests, so one-code-per-request is the
only way to guarantee a correct code → value mapping.
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, AsyncIterator, Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from ..client import BCRPClient
from ..exceptions import BCRPAPIError, BCRPNotFoundError, BCRPValidationError
from ..formatters import format_series_response
from ..periods import frequency_from_code, full_history_range, label_to_iso
from .series import get_series

MAX_EXPORT_CODES = 50
DEFAULT_MAX_ROWS = 1000

ProgressFn = Callable[[str], None]


def _trim_padding(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop leading/trailing periods where every series is ``n.d.``.

    A full-history request asks for a window far wider than the series, and
    BCRP answers with one padded row per calendar period. Interior gaps are
    real data (a holiday, a suspended series) and are kept.
    """
    first, last = 0, len(data) - 1
    while first <= last and not any(v is not None for v in data[first].get("values", [])):
        first += 1
    while last >= first and not any(v is not None for v in data[last].get("values", [])):
        last -= 1
    return data[first : last + 1]


async def get_series_full(
    client: BCRPClient,
    series_codes: list[str],
    language: str = "esp",
    max_rows: int | None = DEFAULT_MAX_ROWS,
) -> dict:
    """Fetch a series' entire published history (what ``--all`` maps to)."""
    frequency = frequency_from_code(series_codes[0])
    start, end = full_history_range(frequency)

    result = await get_series(client, series_codes, start, end, language)
    data = _trim_padding(result.get("data", []))

    truncated = False
    if max_rows is not None and len(data) > max_rows:
        # Keep the most recent rows — the tail is what analysis usually needs.
        data = data[-max_rows:]
        truncated = True

    result["data"] = data
    result["count"] = len(data)
    result["requested_range"] = {"start": start, "end": end}
    if data:
        result["first_period"] = data[0]["period"]
        result["last_period"] = data[-1]["period"]
        result["latest"] = data[-1]
    if truncated:
        result["truncated"] = True
        result["warning"] = (
            f"Truncated to the most recent {max_rows} periods. Raise the ceiling with --max N."
        )
    return result


async def _fetch_one(
    client: BCRPClient,
    code: str,
    start: str | None,
    end: str | None,
    language: str,
    all_history: bool,
    sem: asyncio.Semaphore,
) -> dict:
    async with sem:
        if all_history:
            span_start, span_end = full_history_range(frequency_from_code(code))
        else:
            span_start, span_end = start, end
        raw = await client.fetch([code], span_start, span_end, language)
        return format_series_response(raw, [code])


async def iter_series_long(
    client: BCRPClient,
    series_codes: list[str],
    start_period: str | None = None,
    end_period: str | None = None,
    language: str = "esp",
    all_history: bool = False,
    keep_null: bool = False,
    skip_missing: bool = False,
    concurrency: int = 4,
    max_rows: int | None = DEFAULT_MAX_ROWS,
    on_progress: ProgressFn | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream ``{series_code, period, date, value}`` rows for many series.

    Codes may mix frequencies freely. Rows arrive grouped by code in the order
    the codes were given, while the fetches themselves run ``concurrency``-wide,
    so a 30-series harvest is not 30 sequential round trips.
    """
    if not series_codes:
        raise BCRPValidationError("Provide at least one series code.")
    if len(series_codes) > MAX_EXPORT_CODES:
        raise BCRPValidationError(
            f"Maximum {MAX_EXPORT_CODES} series codes per export "
            f"({len(series_codes)} given). Split the harvest into batches."
        )
    if end_period and not start_period and not all_history:
        raise BCRPValidationError("Provide --start when specifying --end.")

    sem = asyncio.Semaphore(max(1, concurrency))
    tasks = [
        asyncio.ensure_future(
            _fetch_one(client, code, start_period, end_period, language, all_history, sem)
        )
        for code in series_codes
    ]

    emitted = 0
    try:
        for code, task in zip(series_codes, tasks):
            try:
                result = await task
            except (BCRPNotFoundError, BCRPAPIError) as exc:
                if not skip_missing:
                    raise
                if on_progress:
                    on_progress(f"skipped {code}: {exc}")
                continue

            data = _trim_padding(result.get("data", [])) if all_history else result.get("data", [])
            for point in data:
                values = point.get("values") or [None]
                value = values[0]
                if value is None and not keep_null:
                    continue
                if max_rows is not None and emitted >= max_rows:
                    if on_progress:
                        on_progress(f"row ceiling {max_rows} reached; stopping (raise it with --max N)")
                    return
                emitted += 1
                period = point.get("period", "")
                yield {
                    "series_code": code.upper(),
                    "period": period,
                    "date": label_to_iso(period),
                    "value": value,
                }
            if on_progress:
                on_progress(f"{code}: {len(data)} periods")
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()


async def get_series_long(
    client: BCRPClient,
    series_codes: list[str],
    start_period: str | None = None,
    end_period: str | None = None,
    language: str = "esp",
    all_history: bool = False,
    max_rows: int | None = DEFAULT_MAX_ROWS,
    skip_missing: bool = False,
) -> dict:
    """Buffered form of :func:`iter_series_long`, for MCP tool callers."""
    rows = [
        row
        async for row in iter_series_long(
            client,
            series_codes,
            start_period,
            end_period,
            language,
            all_history=all_history,
            skip_missing=skip_missing,
            max_rows=max_rows,
        )
    ]
    codes_seen = sorted({r["series_code"] for r in rows})
    return {
        "columns": ["series_code", "period", "date", "value"],
        "count": len(rows),
        "series_codes": codes_seen,
        "truncated": max_rows is not None and len(rows) >= max_rows,
        "rows": rows,
        "tip": (
            "Tidy long format: one row per (series, period). Pivot on 'series_code' "
            "for a wide table; 'date' is an ISO-sortable rendering of 'period'."
        ),
    }


# ---------------------------------------------------------------------------
# MCP tool wrapper
# ---------------------------------------------------------------------------


def register_bulk_tools(mcp: FastMCP, client: BCRPClient) -> None:

    @mcp.tool(
        name="bcrp_get_series_long",
        description=(
            "Fetch MANY BCRP series at once as one tidy long-format table.\n\n"
            "Unlike `bcrp_get_series`, the codes do NOT have to share a frequency and the\n"
            "limit is 50 rather than 10 — each series is fetched separately, so the\n"
            "code→value mapping is always correct.\n\n"
            "Returns `rows` of `{series_code, period, date, value}`. `date` is an\n"
            "ISO-sortable rendering of BCRP's human period label. Missing observations\n"
            "are omitted rather than emitted as nulls.\n\n"
            "Set `all_history=true` to pull each series' entire published history "
            "(bounded by `max_rows`)."
        ),
    )
    async def bcrp_get_series_long(
        series_codes: Annotated[
            list[str],
            Field(
                description="1–50 BCRP series codes; frequencies may be mixed.",
                min_length=1,
                max_length=MAX_EXPORT_CODES,
            ),
        ],
        start_period: Annotated[
            str | None,
            Field(default=None, description="Start of range (Daily DD-MM-YYYY, Monthly/Quarterly YYYY-M)."),
        ] = None,
        end_period: Annotated[
            str | None,
            Field(default=None, description="End of range, same format as start_period."),
        ] = None,
        all_history: Annotated[
            bool,
            Field(default=False, description="Fetch each series' full published history."),
        ] = False,
        max_rows: Annotated[
            int,
            Field(default=DEFAULT_MAX_ROWS, ge=1, le=100000, description="Hard ceiling on returned rows."),
        ] = DEFAULT_MAX_ROWS,
        language: Annotated[
            str,
            Field(default="esp", description="'esp' (Spanish) or 'ing' (English)"),
        ] = "esp",
    ) -> dict:
        try:
            return await get_series_long(
                client,
                series_codes,
                start_period,
                end_period,
                language,
                all_history=all_history,
                max_rows=max_rows,
                skip_missing=True,
            )
        except BCRPValidationError as exc:
            raise ToolError(str(exc)) from exc
        except (BCRPNotFoundError, BCRPAPIError) as exc:
            raise ToolError(str(exc)) from exc
