"""Per-command presentation for the `bcrp` CLI.

Each `render_*` consumes the same dict its MCP tool counterpart returns, then
lays it out for a human. Fields that exist purely to steer an LLM (`tip`,
`note`) are deliberately dropped here — they stay available via `--json`.
"""

from __future__ import annotations

from typing import Any

from .render import (
    Column,
    fmt_number,
    kv_block,
    legend,
    meta,
    note,
    placeholder,
    section,
    table,
    title,
    warn,
)


def _series_legend(series: list[dict[str, Any]]) -> list[tuple[str, str]]:
    return [
        (s.get("code", f"series_{i}"), s.get("name", ""))
        for i, s in enumerate(series)
    ]


def _data_table(series: list[dict[str, Any]], data: list[dict[str, Any]]) -> str:
    """Turn BCRP's positional {series, data[].values} shape into period × code.

    `series[i]` describes `data[period].values[i]` (see formatters.py); each
    column is formatted at that series' own published precision.
    """
    codes = [s.get("code", f"series_{i}") for i, s in enumerate(series)]

    rows = []
    for point in data:
        values = point.get("values", [])
        row: dict[str, Any] = {"period": point.get("period", "")}
        for i, code in enumerate(codes):
            row[code] = values[i] if i < len(values) else None
        rows.append(row)

    columns = [Column("period", "Period")]
    for i, code in enumerate(codes):
        decimals = series[i].get("decimals") if i < len(series) else None
        columns.append(
            Column(
                code,
                code,
                align="right",
                format=lambda v, d=decimals: fmt_number(v, d),
            )
        )
    return table(rows, columns)


def render_series(result: dict[str, Any]) -> None:
    title(result.get("title") or "BCRP series")
    meta([
        f"{result['frequency']}" if result.get("frequency") else "",
        (
            f"{result['first_period']} → {result['last_period']}"
            if result.get("first_period")
            else ""
        ),
        f"{result['count']} periods" if result.get("count") is not None else "",
    ])

    series = result.get("series", [])
    if series:
        section("Series")
        legend(_series_legend(series))

    section("Data")
    print(_data_table(series, result.get("data", [])))

    if result.get("warning"):
        print()
        warn(result["warning"])


def render_describe(result: dict[str, Any]) -> None:
    title(result.get("title") or "BCRP series metadata")

    series = result.get("series", [])
    if series:
        section("Series")
        print(
            table(
                series,
                [
                    Column("code", "Code", max_width=12),
                    Column("name", "Name", max_width=70),
                    Column("decimals", "Dec", align="right"),
                ],
            )
        )

    section("Availability")
    kv_block([
        ("Frequency", result.get("frequency") or placeholder()),
        ("First period", result.get("first_available") or placeholder()),
        ("Last period", result.get("last_available") or placeholder()),
        ("Total periods", str(result.get("total_available_periods", placeholder()))),
    ])


def render_catalog_search(result: dict[str, Any]) -> None:
    results = result.get("results", [])
    if not results:
        title("No matches")
        note(result.get("message", ""))
        return

    count = result.get("count", len(results))
    title(f"{count} series found")

    # `description` is intentionally omitted — it is long, duplicates `name`,
    # and would starve every other column of width. It stays in --json.
    print()
    print(
        table(
            results,
            [
                Column("code", "Code", max_width=12),
                Column("name", "Name", max_width=48),
                Column("frequency", "Frequency", max_width=10),
                Column("unit", "Unit", max_width=24),
                Column("category", "Category", max_width=28),
            ],
        )
    )
    print()
    note("Use a code with `bcrp series latest <CODE>` or `bcrp series get <CODE>`.")


def render_catalog_categories(result: dict[str, Any]) -> None:
    categories = result.get("categories", [])
    title(f"{len(categories)} catalog categories")

    print()
    print(
        table(
            categories,
            [
                Column("id", "Category", max_width=34),
                Column("series_count", "Series", align="right"),
                Column("frequency", "Frequency", max_width=12),
            ],
        )
    )
    print()
    note(
        f"{result.get('total_catalogued_series', 0)} curated series total "
        "· filter with `bcrp catalog search <query> --category <id>`."
    )


def render_macro_snapshot(result: dict[str, Any]) -> None:
    title("Peru · macroeconomic snapshot")
    meta([f"as of {result.get('snapshot_date', 'unknown')}"])

    daily = result.get("daily_indicators", [])
    if daily:
        section("Daily indicators")
        rows = [
            {
                "code": d.get("code", ""),
                "name": d.get("name", ""),
                "period": d.get("latest_period", ""),
                # Pre-formatted per series so each prints at its own precision.
                "value": fmt_number(d.get("latest_value"), d.get("decimals")),
            }
            for d in daily
        ]
        print(
            table(
                rows,
                [
                    Column("code", "Code", max_width=12),
                    Column("name", "Indicator", max_width=52),
                    Column("period", "Period", max_width=12),
                    Column("value", "Value", align="right"),
                ],
            )
        )

    monthly = result.get("monthly_indicators", {})
    m_series = monthly.get("series", [])
    if m_series:
        section(f"Monthly indicators · latest {monthly.get('latest_period', placeholder())}")
        legend(_series_legend(m_series))
        print()
        print(_data_table(m_series, monthly.get("data", [])))


def render_cache(result: dict[str, Any]) -> None:
    """Human view for `bcrp cache stats|clear|path`.

    The disk cache is invisible until something goes wrong with it, so this
    view leads with the location — that is the first thing anyone diagnosing a
    stale or missing entry actually needs.
    """
    title("BCRP disk cache")
    print()
    for label, key in (
        ("Location", "path"),
        ("Entries", "entries"),
        ("Live", "live_entries"),
        ("Expired", "expired_entries"),
        ("Size (bytes)", "size_bytes"),
        ("Oldest entry", "oldest_entry"),
        ("Removed", "removed_entries"),
    ):
        if key in result:
            print(f"  {label:<14} {result[key]}")
    print()
    note("Bypass it with `--refresh`, or disable it entirely with `--no-cache`.")
