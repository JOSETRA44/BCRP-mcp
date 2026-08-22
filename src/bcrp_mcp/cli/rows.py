"""Flat row projections — the `rows` half of every command's output.

A tool-core function returns BCRP's nested, positional shape (``series[i]``
describes ``data[period].values[i]``). Table, CSV, Markdown and JSONL all want
one flat dict per line instead, so each ``rows_*`` here answers the question
"what does one row of this command look like?" — and the same answer is what
``describe --json`` publishes as ``row_fields``.
"""

from __future__ import annotations

from typing import Any

from ..periods import label_to_iso

# Published in the describe manifest so an agent knows the columns up front.
SERIES_ROW_FIELDS = ["period", "date", "<CODE>..."]
DESCRIBE_ROW_FIELDS = ["code", "name", "decimals", "frequency", "first_available", "last_available"]
CATALOG_ROW_FIELDS = ["code", "name", "frequency", "unit", "category", "period_format", "description"]
CATEGORY_ROW_FIELDS = ["id", "series_count", "frequency"]
MACRO_ROW_FIELDS = ["section", "code", "name", "period", "value"]
LONG_ROW_FIELDS = ["series_code", "period", "date", "value"]


def rows_series(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Wide projection: one row per period, one column per series code.

    Mirrors the human table exactly, so `-f csv` and `-f table` describe the
    same grid.
    """
    series = result.get("series", [])
    codes = [s.get("code", f"series_{i}") for i, s in enumerate(series)]

    rows: list[dict[str, Any]] = []
    for point in result.get("data", []):
        values = point.get("values", [])
        period = point.get("period", "")
        row: dict[str, Any] = {"period": period, "date": label_to_iso(period)}
        for i, code in enumerate(codes):
            row[code] = values[i] if i < len(values) else None
        rows.append(row)
    return rows


def rows_describe(result: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per series, with the shared availability block folded in."""
    return [
        {
            "code": s.get("code", ""),
            "name": s.get("name", ""),
            "decimals": s.get("decimals"),
            "frequency": result.get("frequency"),
            "first_available": result.get("first_available"),
            "last_available": result.get("last_available"),
            "total_available_periods": result.get("total_available_periods"),
        }
        for s in result.get("series", [])
    ]


def rows_catalog_search(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "code": r.get("code", ""),
            "name": r.get("name", ""),
            "frequency": r.get("frequency", ""),
            "unit": r.get("unit", ""),
            "category": r.get("category", ""),
            "period_format": r.get("period_format", ""),
            "description": r.get("description", ""),
        }
        for r in result.get("results", [])
    ]


def rows_catalog_categories(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": c.get("id", ""),
            "series_count": int(c.get("series_count", 0)),
            "frequency": c.get("frequency", ""),
        }
        for c in result.get("categories", [])
    ]


def rows_macro(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the two-section snapshot into one indicator-per-row table."""
    rows: list[dict[str, Any]] = []
    for indicator in result.get("daily_indicators", []):
        rows.append(
            {
                "section": "daily",
                "code": indicator.get("code", ""),
                "name": indicator.get("name", ""),
                "period": indicator.get("latest_period", ""),
                "date": label_to_iso(indicator.get("latest_period", "")),
                "value": indicator.get("latest_value"),
            }
        )

    monthly = result.get("monthly_indicators", {})
    series = monthly.get("series", [])
    data = monthly.get("data", [])
    if series and data:
        latest = data[-1]
        values = latest.get("values", [])
        period = latest.get("period", "")
        for i, s in enumerate(series):
            rows.append(
                {
                    "section": "monthly",
                    "code": s.get("code", ""),
                    "name": s.get("name", ""),
                    "period": period,
                    "date": label_to_iso(period),
                    "value": values[i] if i < len(values) else None,
                }
            )
    return rows
