"""Period handling: frequency inference, request normalisation, ISO dates.

Three jobs live here, all of them shared by the MCP server and the CLI:

1. **Frequency inference from a series code.** BCRP encodes the frequency in
   the last character of the code (``PD04637PD`` → D → daily, ``PN00196MM`` →
   M → monthly). Knowing the frequency *before* the request lets us pick a
   cache TTL and a full-history window without a round trip.
2. **Request-period normalisation.** The BCRP docs say daily ranges are
   ``DD-MM-YYYY``, but the API silently answers such a range with a wall of
   ``n.d.`` — it actually wants ``YYYY-M-D``. We accept the documented form
   (and the MCP tool signatures keep advertising it) and rewrite it here.
3. **Response-label → ISO date.** BCRP labels periods for humans
   (``02.Ene.25``, ``Ene.2024``, ``T1.26``); a tidy export needs something
   sortable.
"""

from __future__ import annotations

import re
from datetime import date

# Frequency marker → canonical frequency name, keyed by a series code's last char.
_CODE_SUFFIX_FREQ = {
    "D": "daily",
    "W": "weekly",
    "M": "monthly",
    "Q": "quarterly",
    "A": "annual",
}

# How far back a "fetch everything" request should reach, per frequency.
# BCRP pads the response out to the full requested window with `n.d.`, so the
# floors stay tight enough to keep responses small; callers trim the padding.
FULL_HISTORY_FLOOR = {
    "daily": (1970, 1, 1),
    "weekly": (1970, 1, 1),
    "monthly": (1900, 1, 1),
    "quarterly": (1900, 1, 1),
    "annual": (1900, 1, 1),
}

# Cache lifetimes. BCRP publishes daily series once per business day and
# monthly aggregates weeks after the month closes, so slower series may be
# cached far more aggressively than the 5-minute global default.
CACHE_TTL_BY_FREQUENCY = {
    "daily": 3600,        # 1 h  — refreshed intraday on publication days
    "weekly": 21600,      # 6 h
    "monthly": 21600,     # 6 h
    "quarterly": 86400,   # 24 h
    "annual": 86400,      # 24 h
}

_MONTHS = {
    "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8,
    "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
}

_DAILY_LABEL = re.compile(r"^(\d{2})\.([A-Za-zÁÉÍÓÚáéíóú]{3})\.(\d{2,4})$")
_MONTH_LABEL = re.compile(r"^([A-Za-zÁÉÍÓÚáéíóú]{3})\.(\d{2,4})$")
_QUARTER_LABEL = re.compile(r"^T(\d)\.(\d{2,4})$")


def frequency_from_code(code: str) -> str:
    """Infer a series' frequency from the last character of its code."""
    if not code:
        return "unknown"
    return _CODE_SUFFIX_FREQ.get(code.strip().upper()[-1], "unknown")


def frequency_for_codes(codes: list[str]) -> str:
    """Infer one frequency for a batch; ``unknown`` if the batch is mixed."""
    freqs = {frequency_from_code(c) for c in codes}
    if len(freqs) == 1:
        return freqs.pop()
    return "unknown"


def cache_ttl_for_codes(codes: list[str], default: int) -> int:
    """Per-frequency cache TTL, falling back to the configured default."""
    return CACHE_TTL_BY_FREQUENCY.get(frequency_for_codes(codes), default)


def _expand_year(year: int) -> int:
    """Expand a 2-digit BCRP year; 70-99 are last century, 00-69 are this one."""
    if year >= 100:
        return year
    return 1900 + year if year >= 70 else 2000 + year


def normalize_request_period(period: str | None, frequency: str) -> str | None:
    """Rewrite a user-supplied period into the form the API actually honours.

    Only daily/weekly series need rewriting: ``01-01-2025`` (the documented
    form) becomes ``2025-1-1``. Monthly/quarterly/annual periods pass through
    untouched, as do daily periods already written the API's way.
    """
    if not period:
        return period
    text = period.strip()
    if frequency not in ("daily", "weekly", "unknown"):
        return text

    parts = text.replace("/", "-").split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return text
    if len(parts[0]) == 4:          # already YYYY-M-D
        return f"{int(parts[0])}-{int(parts[1])}-{int(parts[2])}"
    if len(parts[2]) == 4:          # documented DD-MM-YYYY
        return f"{int(parts[2])}-{int(parts[1])}-{int(parts[0])}"
    return text


def full_history_range(frequency: str, today: date | None = None) -> tuple[str, str]:
    """Widest ``(start, end)`` pair that returns a series' whole history."""
    today = today or date.today()
    year, month, day = FULL_HISTORY_FLOOR.get(frequency, (1900, 1, 1))
    end_year = today.year + 1

    if frequency in ("daily", "weekly"):
        return f"{year}-{month}-{day}", f"{end_year}-12-31"
    if frequency == "monthly":
        return f"{year}-{month}", f"{end_year}-12"
    if frequency == "quarterly":
        return f"{year}-1", f"{end_year}-4"
    if frequency == "annual":
        return str(year), str(end_year)
    # Unknown frequency: monthly bounds are the most forgiving guess.
    return f"{year}-{month}", f"{end_year}-12"


def label_to_iso(label: str) -> str | None:
    """Turn a BCRP period label into a sortable ISO-ish string.

    ``02.Ene.25`` → ``2025-01-02``, ``Ene.2024`` → ``2024-01``,
    ``T1.26`` → ``2026-Q1``, ``2024`` → ``2024``. Returns ``None`` when the
    label is in a shape we do not recognise.
    """
    if not label:
        return None
    text = label.strip()

    m = _DAILY_LABEL.match(text)
    if m:
        month = _MONTHS.get(m.group(2)[:3].lower())
        if month:
            return f"{_expand_year(int(m.group(3))):04d}-{month:02d}-{int(m.group(1)):02d}"

    m = _MONTH_LABEL.match(text)
    if m:
        month = _MONTHS.get(m.group(1)[:3].lower())
        if month:
            return f"{_expand_year(int(m.group(2))):04d}-{month:02d}"

    m = _QUARTER_LABEL.match(text)
    if m:
        return f"{_expand_year(int(m.group(2))):04d}-Q{m.group(1)}"

    if text.isdigit() and len(text) == 4:
        return text
    return None
