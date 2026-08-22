"""CLI command implementations.

Each function is a thin adapter: parse `argparse.Namespace` → call the
shared tool-core function from `bcrp_mcp.tools.*` or `bcrp_mcp.catalog` →
wrap the same dict an MCP client would receive in a `CommandResult`, adding
the flat row projection the non-table formats need. No business logic lives
here — that would risk the CLI and the MCP tools drifting apart.
"""

from __future__ import annotations

import argparse

from ..cache import DiskCache
from ..catalog import list_categories, search_catalog
from ..client import BCRPClient
from ..tools.bulk import get_series_full
from ..tools.macro import get_macro_snapshot
from ..tools.series import describe_series, get_latest, get_series
from . import rows as R
from . import views
from .output import CommandResult


async def cmd_series_get(client: BCRPClient, args: argparse.Namespace) -> CommandResult:
    if getattr(args, "all", False):
        result = await get_series_full(client, args.codes, args.lang, _max_rows(args, default=1000))
    else:
        result = await get_series(client, args.codes, args.start, args.end, args.lang)
        result = _apply_ceiling(result, _max_rows(args, default=None))

    return CommandResult(
        data=result,
        rows=R.rows_series(result),
        meta=_series_meta(result),
        view=views.render_series,
        title=result.get("title", "BCRP series"),
    )


async def cmd_series_latest(client: BCRPClient, args: argparse.Namespace) -> CommandResult:
    result = await get_latest(client, args.codes, args.n, args.lang)
    return CommandResult(
        data=result,
        rows=R.rows_series(result),
        meta=_series_meta(result),
        view=views.render_series,
        title=result.get("title", "BCRP series"),
    )


async def cmd_series_describe(client: BCRPClient, args: argparse.Namespace) -> CommandResult:
    result = await describe_series(client, args.codes, args.lang)
    return CommandResult(
        data=result,
        rows=R.rows_describe(result),
        meta={
            "frequency": result.get("frequency"),
            "total_available_periods": result.get("total_available_periods"),
        },
        view=views.render_describe,
        title=result.get("title", "BCRP series metadata"),
    )


async def cmd_catalog_search(client: BCRPClient | None, args: argparse.Namespace) -> CommandResult:
    results = search_catalog(args.query, args.category, args.frequency)
    if not results:
        data = {
            "results": [],
            "count": 0,
            "message": (
                f"No series found for '{args.query}'. "
                "Try broader terms or run `bcrp catalog categories` to explore available categories."
            ),
        }
    else:
        data = {
            "results": results,
            "count": len(results),
            "tip": "Use the 'code' field with `bcrp series get` / `bcrp series latest` to fetch data.",
        }
    return CommandResult(
        data=data,
        rows=R.rows_catalog_search(data),
        meta={"query": args.query, "category": args.category, "frequency": args.frequency},
        view=views.render_catalog_search,
        title="Catalog search",
    )


async def cmd_catalog_categories(client: BCRPClient | None, args: argparse.Namespace) -> CommandResult:
    categories = list_categories()
    data = {
        "categories": categories,
        "total_catalogued_series": sum(int(c["series_count"]) for c in categories),
    }
    return CommandResult(
        data=data,
        rows=R.rows_catalog_categories(data),
        meta={"total_catalogued_series": data["total_catalogued_series"]},
        view=views.render_catalog_categories,
        title="Catalog categories",
    )


async def cmd_macro_snapshot(client: BCRPClient, args: argparse.Namespace) -> CommandResult:
    result = await get_macro_snapshot(client, args.lang)
    return CommandResult(
        data=result,
        rows=R.rows_macro(result),
        meta={"snapshot_date": result.get("snapshot_date")},
        view=views.render_macro_snapshot,
        title="Peru · macroeconomic snapshot",
    )


async def cmd_cache(client: BCRPClient | None, args: argparse.Namespace) -> CommandResult:
    """`cache stats|clear|path` — inspect or wipe the cross-process disk cache."""
    cache = DiskCache(getattr(args, "cache_dir", None))

    if args.cache_action == "path":
        data = {"path": str(cache.dir)}
        rows = [data]
    elif args.cache_action == "clear":
        removed = cache.clear()
        data = {"path": str(cache.dir), "removed_entries": removed}
        rows = [data]
    else:  # stats
        data = cache.stats()
        rows = [data]

    return CommandResult(
        data=data,
        rows=rows,
        meta={"action": args.cache_action},
        view=views.render_cache,
        title="Cache",
    )


# --- helpers ---------------------------------------------------------------


def _max_rows(args: argparse.Namespace, default: int | None) -> int | None:
    """`--max N`, or the command's own default when the flag was not given."""
    value = getattr(args, "max_rows", None)
    return default if value is None else value


def _apply_ceiling(result: dict, max_rows: int | None) -> dict:
    """Trim a buffered result to the most recent ``max_rows`` periods."""
    data = result.get("data", [])
    if max_rows is None or len(data) <= max_rows:
        return result
    data = data[-max_rows:]
    result["data"] = data
    result["count"] = len(data)
    result["first_period"] = data[0]["period"]
    result["truncated"] = True
    result["warning"] = f"Truncated to the most recent {max_rows} periods (raise with --max N)."
    return result


def _series_meta(result: dict) -> dict:
    return {
        "frequency": result.get("frequency"),
        "first_period": result.get("first_period"),
        "last_period": result.get("last_period"),
        "series_codes": [s.get("code") for s in result.get("series", [])],
        "truncated": bool(result.get("truncated")),
    }
