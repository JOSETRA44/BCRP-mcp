"""Regenerate the bcrp skill's reference files from the source of truth.

The skill ships a catalog of series codes and an API guide. Both already exist
in the package (`bcrp_mcp.catalog`, `bcrp_mcp.resources.guides`) and are what
the MCP server serves to clients — so we generate the skill's copies from
those rather than maintaining a second hand-written version that would quietly
drift out of date.

Run after changing the catalog or the guides:

    uv run python scripts/gen_skill_refs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bcrp_mcp.catalog import CATALOG  # noqa: E402
from bcrp_mcp.resources.guides import API_GUIDE, PERIOD_FORMAT_GUIDE  # noqa: E402

REFS = ROOT / "skills" / "bcrp" / "references"

HEADER = """<!-- GENERATED FILE — do not edit by hand.
     Regenerate with: uv run python scripts/gen_skill_refs.py -->

"""


def build_series_codes() -> str:
    lines = [
        "# BCRP series catalog",
        "",
        "Curated codes verified active against the live BCRPData API.",
        "All series in a single request must share the same frequency (max 10 codes).",
        "",
    ]

    for category, series_list in CATALOG.items():
        if not series_list:
            continue
        freq = series_list[0].get("frequency", "?")
        period_format = series_list[0].get("period_format", "?")
        lines += [
            f"## {category.replace('_', ' ').title()}",
            "",
            f"`{category}` · {freq} · period format `{period_format}` · "
            f"{len(series_list)} series",
            "",
            "| Code | Name | Unit |",
            "|------|------|------|",
        ]
        for s in series_list:
            lines.append(f"| `{s['code']}` | {s['name']} | {s.get('unit', '—')} |")
        lines.append("")
        for s in series_list:
            if s.get("description"):
                lines.append(f"- **`{s['code']}`** — {s['description']}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Beyond this catalog",
        "",
        "This covers the most commonly used series. The full BCRPData database holds",
        "8,000+ monthly, 2,700+ quarterly and 800+ daily series. Browse them at",
        "<https://estadisticas.bcrp.gob.pe/estadisticas/series/>, then verify any code",
        "you find with `bcrp_describe_series` / `bcrp series describe` before relying on it.",
        "",
    ]
    return "\n".join(lines)


def build_api() -> str:
    return f"{API_GUIDE}\n\n---\n\n{PERIOD_FORMAT_GUIDE}"


def main() -> None:
    REFS.mkdir(parents=True, exist_ok=True)
    targets = {
        "series-codes.md": build_series_codes(),
        "api.md": build_api(),
    }
    for name, body in targets.items():
        path = REFS / name
        path.write_text(HEADER + body, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(body.splitlines())} lines)")


if __name__ == "__main__":
    main()
