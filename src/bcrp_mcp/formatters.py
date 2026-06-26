"""Pure formatting functions: raw BCRP JSON → clean AI-friendly dicts.

Design note: The BCRP API reorders series when codes from different categories are combined.
Values are returned positionally matching the API's config.series array order, which may
differ from the requested codes order. The 'series' list and 'data[].values' list always
correspond by position — series[i] describes data[period].values[i].
"""

from typing import Any


def _safe_float(value: str | None) -> float | None:
    """Convert a string value to float; return None for n.d./null/empty."""
    if not value or value.strip() in ("n.d.", "n.d", "-", ""):
        return None
    try:
        return float(value.replace(",", "."))
    except (ValueError, TypeError):
        return None


def _detect_frequency(period_name: str) -> str:
    """Infer frequency from the period label returned by the API."""
    if not period_name:
        return "unknown"
    name = period_name.strip()
    # Daily: "01.Ene.25", "24.Jun.26"
    if len(name) >= 8 and name[2] == "." and name[6] == ".":
        return "daily"
    # Quarterly: "T4.25", "T1.2024"
    if name.startswith("T") and "." in name:
        return "quarterly"
    # Weekly
    if name.lower().startswith("sem"):
        return "weekly"
    # Annual: "2024"
    if len(name) == 4 and name.isdigit():
        return "annual"
    # Monthly: "Ene.2024", "Dic.2021"
    return "monthly"


def format_series_response(
    raw: dict[str, Any],
    series_codes: list[str],
) -> dict[str, Any]:
    """Format raw BCRP JSON response into a structured dict.

    Values are stored as positional lists. series[i] describes data[period].values[i].
    This avoids misalignment when the API reorders codes from different categories.
    """
    config = raw.get("config", {})
    raw_series = config.get("series", [])
    periods = raw.get("periods", [])

    # Build series metadata — use API's ordering and names
    # Codes assigned positionally from the input list (may not match API order if reordered)
    series_meta = []
    for i, s in enumerate(raw_series):
        # Assign the user's code if available at this position; otherwise unknown
        code = series_codes[i].upper() if i < len(series_codes) else f"series_{i}"
        series_meta.append({
            "code": code,
            "name": s.get("name", "").strip(),
            "decimals": int(s.get("dec", "2")),
        })

    frequency = "unknown"
    if periods:
        frequency = _detect_frequency(periods[0]["name"])

    data_points = []
    for period in periods:
        pname = period.get("name", "")
        raw_values = period.get("values", [])
        # Values as list (positional, matching series_meta order)
        values = [_safe_float(v) for v in raw_values]
        data_points.append({"period": pname, "values": values})

    result: dict[str, Any] = {
        "title": config.get("title", "").strip(),
        "frequency": frequency,
        "series": series_meta,
        "count": len(data_points),
        "data": data_points,
    }

    if data_points:
        result["first_period"] = data_points[0]["period"]
        result["last_period"] = data_points[-1]["period"]
        result["latest"] = data_points[-1]

    cleaned = {k: v for k, v in result.items() if v not in (None, "", {}) and k != "data"}
    cleaned["data"] = data_points
    return cleaned


def format_latest_response(
    raw: dict[str, Any],
    series_codes: list[str],
    n: int,
) -> dict[str, Any]:
    """Format response keeping only the most recent n data points."""
    full = format_series_response(raw, series_codes)
    data = full.get("data", [])
    if n < len(data):
        full["data"] = data[-n:]
        full["count"] = len(full["data"])
        if full["data"]:
            full["first_period"] = full["data"][0]["period"]
    return full


def format_metadata_only(
    raw: dict[str, Any],
    series_codes: list[str],
) -> dict[str, Any]:
    """Return only series metadata without data points."""
    config = raw.get("config", {})
    raw_series = config.get("series", [])
    periods = raw.get("periods", [])

    series_meta = []
    for i, s in enumerate(raw_series):
        code = series_codes[i].upper() if i < len(series_codes) else f"series_{i}"
        series_meta.append({
            "code": code,
            "name": s.get("name", "").strip(),
            "decimals": int(s.get("dec", "2")),
        })

    result: dict[str, Any] = {
        "title": config.get("title", "").strip(),
        "series": series_meta,
        "total_available_periods": len(periods),
    }

    if periods:
        freq = _detect_frequency(periods[0]["name"])
        result["frequency"] = freq
        result["first_available"] = periods[0]["name"]
        result["last_available"] = periods[-1]["name"]

    return {k: v for k, v in result.items() if v not in (None, "", [], {})}


def format_single_series_latest(
    raw: dict[str, Any],
    series_code: str,
) -> dict[str, Any]:
    """Compact format for a single series - returns latest value with metadata."""
    config = raw.get("config", {})
    raw_series = config.get("series", [{}])
    periods = raw.get("periods", [])

    s = raw_series[0] if raw_series else {}
    result: dict[str, Any] = {
        "code": series_code.upper(),
        "name": s.get("name", "").strip(),
        "decimals": int(s.get("dec", "2")),
    }

    if periods:
        result["frequency"] = _detect_frequency(periods[0]["name"])
        result["available_periods"] = len(periods)
        last = periods[-1]
        result["latest_period"] = last["name"]
        result["latest_value"] = _safe_float(last["values"][0]) if last.get("values") else None

    return {k: v for k, v in result.items() if v is not None}
