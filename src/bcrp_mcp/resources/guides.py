from mcp.server.fastmcp import FastMCP

from ..catalog import CATALOG

API_GUIDE = """\
# BCRP API Developer Guide

## Overview

**BCRPData** (https://estadisticas.bcrp.gob.pe) is the Banco Central de Reserva del Perú's
open statistics database. No API key or authentication is required — it is fully public.

## Base URL

```
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/
```

## GET Request Structure

```
/api/{series_codes}/json/{start_period}/{end_period}/{language}
```

Only `{series_codes}` is required. All other parameters are optional.

## Parameters

| Parameter | Required | Values | Notes |
|-----------|:--------:|--------|-------|
| `series_codes` | **Yes** | Code1-Code2-... | 1–10 codes, hyphen-separated, same frequency |
| `format` | No | json, xml, csv, txt, xls, html | Default: html; use **json** for MCP |
| `start_period` | No | See period formats below | Omit for most recent data |
| `end_period` | No | Same format as start | Requires start_period |
| `language` | No | `esp`, `ing` | Default: esp (Spanish) |

## Period Format by Frequency

| Frequency | Format | Examples |
|-----------|--------|---------|
| **Daily** | `DD-MM-YYYY` | `01-01-2025`, `30-06-2025` |
| **Monthly** | `YYYY-M` | `2024-1` (Jan), `2024-12` (Dec) |
| **Quarterly** | `YYYY-Q` | `2024-1` (Q1), `2024-4` (Q4) |
| **Annual** | `YYYY` | `2024`, `2020` |
| **Weekly** | `YYYY-W` | `2024-1` (week 1) |

**Important:** All series in a single request must have the same frequency.
If mixed frequencies are provided, only data matching the first series' frequency is returned.

## JSON Response Structure

```json
{
  "config": {
    "title": "Category title",
    "series": [
      {
        "name": "Full series name",
        "dec": "2"
      }
    ]
  },
  "periods": [
    {
      "name": "Ene.2024",
      "values": ["100.5", "n.d."]
    }
  ]
}
```

**Period label formats by frequency:**
- Monthly: `Ene.2024`, `Feb.2024`, `Dic.2025`
- Quarterly: `T1.2024`, `T4.2025`
- Daily: `01.Ene.24`, `30.Jun.26`
- Annual: `2024`

`n.d.` in values means no data (not available) for that period.

## URL Examples

```
# Single monthly series, all available data
/api/PN00196MM/json

# Two daily series, date range
/api/PD04637PD-PD12301MD/json/01-01-2024/30-06-2025/esp

# Five monthly series, year range, English
/api/PN00496MM-PN00500MM/json/2020-1/2025-12/ing

# Quarterly GDP series
/api/PN03503MQ-PN03501MQ/json/2020-1/2025-4/esp

# Ten monthly series (maximum)
/api/PN00001MM-PN00002MM-PN00003MM-PN00004MM-PN00005MM-PN00006MM-PN00007MM-PN00008MM-PN00009MM-PN00010MM/json
```

## POST Method

Equivalent to GET but with form-encoded body:

```
POST https://estadisticas.bcrp.gob.pe/estadisticas/series/api/
Content-Type: application/x-www-form-urlencoded

series=PN00196MM-PN00178MM&formato=json&fechaini=2024-1&fechafin=2024-12&idioma=esp
```

## Error Handling

The API returns an **empty HTML page** (not an error code) when:
- A series code does not exist
- No data exists in the requested period range
- Mixed-frequency series are requested (only matching ones returned)

Always check that `periods` array is non-empty before processing results.

## Rate Limits

BCRPData does not publish official rate limits. For respectful usage:
- Cache responses for at least 5 minutes (default in this MCP)
- Avoid parallel requests to the same series
- Use date ranges to fetch data in batches rather than period-by-period

## Finding Series Codes

The BCRP has 8,000+ monthly series, 2,700+ quarterly, and 800+ daily.
Browse the full catalog at: https://estadisticas.bcrp.gob.pe/estadisticas/series/
"""

PERIOD_FORMAT_GUIDE = """\
# BCRP Period Format Reference

## Quick Reference

| Frequency | Query format | Period label (in response) | Example query |
|-----------|-------------|---------------------------|---------------|
| Daily | `DD-MM-YYYY` | `01.Ene.25`, `24.Jun.26` | `01-06-2025` |
| Monthly | `YYYY-M` | `Ene.2024`, `Dic.2025` | `2024-1` |
| Quarterly | `YYYY-Q` | `T1.2024`, `T4.25` | `2024-3` |
| Annual | `YYYY` | `2024` | `2024` |
| Weekly | `YYYY-W` | `Sem.1.2024` | `2024-1` |

## Monthly Period Numbers

| Month | Number | Spanish abbreviation |
|-------|--------|---------------------|
| January | 1 | Ene |
| February | 2 | Feb |
| March | 3 | Mar |
| April | 4 | Abr |
| May | 5 | May |
| June | 6 | Jun |
| July | 7 | Jul |
| August | 8 | Ago |
| September | 9 | Sep |
| October | 10 | Oct |
| November | 11 | Nov |
| December | 12 | Dic |

## Quarterly Period Numbers

| Quarter | Number |
|---------|--------|
| Q1 (Jan–Mar) | 1 |
| Q2 (Apr–Jun) | 2 |
| Q3 (Jul–Sep) | 3 |
| Q4 (Oct–Dec) | 4 |

## Rules and Gotchas

1. **Omit periods to get latest data**: The API returns the most recent available data
   if no start/end period is specified. For daily series, this is typically ~90 days.

2. **Single period = single-date query**: Providing only `start_period` without `end_period`
   returns data for that single period.

3. **Frequency constraint**: All series in one call must have the same frequency.
   The API silently drops series with mismatched frequency — no error is returned.

4. **Period zero-padding**: Do NOT zero-pad period numbers. Use `2024-1` not `2024-01`.

5. **Daily out-of-range**: If the date range has no trading days (e.g., weekend-only range),
   the periods array will be empty.

6. **Daily date separators**: Use hyphens (`01-01-2025`), not slashes.

## Period Detection from Response Labels

When the API returns data, the `name` field of each period indicates the actual frequency:
- `01.Ene.25` → daily (format: DD.Mon.YY)
- `Ene.2024` → monthly (format: Mon.YYYY)
- `T1.2024` or `T4.25` → quarterly (format: TQ.YYYY or TQ.YY)
- `2024` → annual
"""


def register_resources(mcp: FastMCP) -> None:

    @mcp.resource(
        "bcrp://api-guide",
        name="BCRP API Developer Guide",
        description=(
            "Complete guide for the BCRPData public API: URL structure, period formats, "
            "response schema, error handling, and URL examples for all frequencies."
        ),
        mime_type="text/markdown",
    )
    def api_guide() -> str:
        return API_GUIDE

    @mcp.resource(
        "bcrp://period-formats",
        name="BCRP Period Format Reference",
        description=(
            "Quick reference for BCRP period formats by frequency: "
            "daily (DD-MM-YYYY), monthly (YYYY-M), quarterly (YYYY-Q), annual (YYYY). "
            "Includes month/quarter number tables and common gotchas."
        ),
        mime_type="text/markdown",
    )
    def period_formats() -> str:
        return PERIOD_FORMAT_GUIDE

    @mcp.resource(
        "bcrp://series-catalog",
        name="BCRP Series Catalog",
        description=(
            "Curated catalog of important BCRP series organized by category: "
            "exchange rates, interest rates, international reserves, liquidity, "
            "credit, financial markets, commodities, and GDP. "
            "Each entry includes the series code, name, description, unit, and period format."
        ),
        mime_type="text/markdown",
    )
    def series_catalog() -> str:
        lines = [
            "# BCRP Series Catalog",
            "",
            "Curated catalog of commonly used BCRP series codes, verified active (June 2026).",
            "Use codes with `bcrp_get_series`, `bcrp_get_latest`, or `bcrp_describe_series`.",
            "",
        ]

        for category, series_list in CATALOG.items():
            category_title = category.replace("_", " ").title()
            freq = series_list[0].get("frequency", "?") if series_list else "?"
            lines.append(f"## {category_title}")
            lines.append(f"**Frequency:** {freq}  |  **Series count:** {len(series_list)}")
            lines.append("")
            lines.append("| Code | Name | Unit | Period Format |")
            lines.append("|------|------|------|---------------|")
            for s in series_list:
                lines.append(
                    f"| `{s['code']}` | {s['name']} | {s.get('unit', '—')} | "
                    f"{s.get('period_format', '—')} |"
                )
            lines.append("")
            lines.append("**Descriptions:**")
            for s in series_list:
                lines.append(f"- **{s['code']}**: {s.get('description', '')}")
            lines.append("")

        lines += [
            "---",
            "",
            "## Finding More Series",
            "",
            "The BCRP full database has 8,000+ monthly series, 2,700+ quarterly, and 800+ daily.",
            "Browse all series at: https://estadisticas.bcrp.gob.pe/estadisticas/series/",
            "",
            "Use `bcrp_search_catalog` to search this catalog by keyword.",
            "Use `bcrp_list_catalog_categories` to see all available categories.",
        ]

        return "\n".join(lines)
