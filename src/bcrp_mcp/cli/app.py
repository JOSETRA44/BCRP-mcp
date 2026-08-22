"""Argparse tree, client lifecycle, and entry point for the `bcrp` CLI.

Adding a new command means: write a `cmd_*` function in `commands.py` that
returns a tool-output dict, write a matching `render_*` in `render.py`, and
register a subparser below with `set_defaults(func=..., render=...)`. The
dispatcher and error handling are generic and don't need to change.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from .. import __version__
from ..client import BCRPClient
from ..config import get_settings
from ..exceptions import BCRPError, exit_code_for
from . import commands, describe, output, render, views
from ..cache import DiskCache, MemoryCache
from .output import Options

PROG = "bcrp"


def _setup_console() -> None:
    """Force UTF-8 stdio so accented Spanish series names print correctly
    on Windows terminals whose default code page isn't UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _json_parser() -> argparse.ArgumentParser:
    """Output-style flags shared by every data command (spec section 1)."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "-f",
        "--format",
        choices=list(output.FORMATS),
        default="table",
        help="Output format (default: table). Use json/jsonl/csv for machine use.",
    )
    p.add_argument(
        "-o", "--output", metavar="FILE", help="Write to FILE instead of stdout."
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress notes on stderr."
    )
    p.add_argument(
        "--refresh", action="store_true", help="Ignore any cached copy and refetch."
    )
    p.add_argument(
        "--no-cache", action="store_true", help="Neither read nor write the cache."
    )
    p.add_argument(
        "--json",
        action="store_true",
        # Kept working for scripts written before --format existed.
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour (also honours the NO_COLOR env var).",
    )
    p.add_argument(
        "--ascii",
        action="store_true",
        help="Draw tables with plain ASCII instead of Unicode box characters.",
    )
    return p


def _lang_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--lang",
        choices=["esp", "ing"],
        default="esp",
        help="Language for series names: 'esp' (Spanish, default) or 'ing' (English).",
    )
    return p


def build_parser() -> argparse.ArgumentParser:
    json_p = _json_parser()
    lang_p = _lang_parser()

    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Command-line client for BCRPData — the Banco Central de Reserva del Peru "
            "statistics API. Every command calls the same tool logic the bcrp-mcp MCP "
            "server exposes, so results never differ between the CLI and an MCP client."
        ),
        epilog=(
            "examples:\n"
            "  bcrp series latest PD04637PD PD12301MD\n"
            "  bcrp series get PN00196MM --start 2020-1 --end 2024-12\n"
            "  bcrp series describe PD04637PD --json\n"
            '  bcrp catalog search "tipo de cambio"\n'
            "  bcrp catalog categories\n"
            "  bcrp macro snapshot\n"
            "  bcrp serve                 # run the MCP server over stdio\n"
            "\n"
            "Run `bcrp <command> --help` or `bcrp <command> <subcommand> --help` for details."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="{series,catalog,macro,serve}")
    sub.required = True

    # --- series ---------------------------------------------------------
    series_p = sub.add_parser("series", help="Fetch BCRP time series data.")
    series_sub = series_p.add_subparsers(dest="action", metavar="{get,latest,describe}")
    series_sub.required = True

    get_p = series_sub.add_parser(
        "get",
        parents=[json_p, lang_p],
        help="Fetch historical data for 1-10 same-frequency series (optional date range).",
    )
    get_p.add_argument("codes", nargs="+", metavar="CODE", help="1-10 BCRP series codes, e.g. PD04637PD")
    get_p.add_argument("--start", metavar="PERIOD", help="Start period, e.g. 2020-1 or 01-01-2020")
    get_p.add_argument("--end", metavar="PERIOD", help="End period (same format as --start)")
    get_p.set_defaults(
        func=commands.cmd_series_get,
        render=views.render_series,
        needs_client=True,
        row_fields=["series_code", "series_name", "period", "value"],
        examples=[
            "bcrp series get PN01288PM --start 2015-1 --end 2025-1 -f csv -o pbi.csv",
            "bcrp series get PD04637PD PD04638PD --start 01-01-2024 -f jsonl",
        ],
    )

    latest_p = series_sub.add_parser(
        "latest",
        parents=[json_p, lang_p],
        help="Fetch the most recent N data points for 1-10 same-frequency series.",
    )
    latest_p.add_argument("codes", nargs="+", metavar="CODE")
    latest_p.add_argument("--n", type=int, default=5, metavar="N", help="Periods to return, 1-50 (default: 5)")
    latest_p.set_defaults(
        func=commands.cmd_series_latest,
        render=views.render_series,
        needs_client=True,
        row_fields=["series_code", "series_name", "period", "value"],
        examples=[
            "bcrp series latest PD04637PD --n 10 -f json",
            "bcrp series latest PD04637PD PN01288PM -f md",
        ],
    )

    describe_p = series_sub.add_parser(
        "describe",
        parents=[json_p, lang_p],
        help="Get metadata (name, frequency, available date range) for 1-10 series.",
    )
    describe_p.add_argument("codes", nargs="+", metavar="CODE")
    describe_p.set_defaults(
        func=commands.cmd_series_describe,
        render=views.render_describe,
        needs_client=True,
        row_fields=["series_code", "name", "frequency", "start", "end"],
        examples=["bcrp series describe PD04637PD -f json"],
    )

    # --- catalog ---------------------------------------------------------
    catalog_p = sub.add_parser("catalog", help="Search the built-in curated series catalog (offline).")
    catalog_sub = catalog_p.add_subparsers(dest="action", metavar="{search,categories}")
    catalog_sub.required = True

    search_p = catalog_sub.add_parser("search", parents=[json_p], help="Search the catalog by keyword.")
    search_p.add_argument("query", help="Search term, e.g. 'tipo de cambio' or 'copper'")
    search_p.add_argument("--category", help="Filter by category id (see `bcrp catalog categories`)")
    search_p.add_argument(
        "--frequency",
        choices=["daily", "weekly", "monthly", "quarterly", "annual"],
        help="Filter by frequency",
    )
    search_p.set_defaults(
        func=commands.cmd_catalog_search,
        render=views.render_catalog_search,
        needs_client=False,
        row_fields=["series_code", "name", "category", "frequency", "unit"],
        examples=[
            'bcrp catalog search "tipo de cambio" -f json',
            "bcrp catalog search inflation --frequency monthly -f csv",
        ],
    )

    categories_p = catalog_sub.add_parser("categories", parents=[json_p], help="List all catalog categories.")
    categories_p.set_defaults(
        func=commands.cmd_catalog_categories,
        render=views.render_catalog_categories,
        needs_client=False,
        row_fields=["category", "count"],
        examples=["bcrp catalog categories -f json"],
    )

    # --- macro -------------------------------------------------------------
    macro_p = sub.add_parser("macro", help="Real-time macroeconomic snapshot.")
    macro_sub = macro_p.add_subparsers(dest="action", metavar="{snapshot}")
    macro_sub.required = True

    snapshot_p = macro_sub.add_parser(
        "snapshot", parents=[json_p, lang_p], help="Latest values for Peru's key economic indicators."
    )
    snapshot_p.set_defaults(
        func=commands.cmd_macro_snapshot,
        render=views.render_macro_snapshot,
        needs_client=True,
        row_fields=["indicator", "series_code", "period", "value", "unit"],
        examples=["bcrp macro snapshot -f md", "bcrp macro snapshot -f json"],
    )

    # --- cache -------------------------------------------------------------
    cache_p = sub.add_parser("cache", help="Inspect or wipe the cross-process disk cache.")
    cache_sub = cache_p.add_subparsers(dest="cache_action", metavar="{stats,clear,path}")
    cache_sub.required = True
    for action, blurb in (
        ("stats", "Entry count, size on disk, and TTL."),
        ("clear", "Delete every cached entry."),
        ("path", "Print the cache directory."),
    ):
        action_p = cache_sub.add_parser(action, parents=[json_p], help=blurb)
        action_p.set_defaults(
            func=commands.cmd_cache,
            needs_client=False,
            row_fields=["path", "entries", "bytes", "ttl"],
            examples=[f"bcrp cache {action} -f json"],
        )

    # --- describe ----------------------------------------------------------
    # The manifest is derived from this very parser, so it can only be built
    # once every subparser above has been registered.
    describe_top = sub.add_parser(
        "describe",
        help="Machine-readable manifest of every command, for agents and scripts.",
    )
    describe_top.add_argument(
        "target",
        nargs="?",
        metavar="COMMAND",
        help="Describe only this command (default: the whole CLI).",
    )
    describe_top.add_argument(
        "--json", action="store_true", help="Emit the manifest as JSON."
    )
    describe_top.set_defaults(
        command="describe",
        examples=["bcrp describe --json", "bcrp describe 'series get' --json"],
    )

    # --- serve ---------------------------------------------------------
    sub.add_parser("serve", help="Run the MCP server over stdio (equivalent to `bcrp-mcp`).")

    return parser


def _run_describe(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Print the manifest, or one command's slice of it."""
    manifest = describe.build_manifest(parser)
    if args.target:
        subset = describe.filter_manifest(manifest, args.target)
        if subset is None:
            print(
                f"Unknown command '{args.target}'. "
                f"Run `{PROG} describe --json` to list them all.",
                file=sys.stderr,
            )
            return 2
        manifest = subset
    if args.json:
        render.print_json(manifest)
    else:
        describe.render_manifest(manifest)
    return 0


async def _run_data_command(args: argparse.Namespace, opts: Options) -> int:
    """Execute one command and render it, mapping any failure to an exit code."""
    command = " ".join(p for p in (args.command, getattr(args, "action", None)) if p)
    try:
        if getattr(args, "needs_client", True):
            settings = get_settings()
            # A CLI process is short-lived, so an in-memory cache would never
            # be read; the disk cache is what makes a repeated query instant.
            cache = MemoryCache() if opts.no_cache else DiskCache()
            async with BCRPClient(settings, cache=cache) as client:
                client.refresh = opts.refresh
                result = await args.func(client, args)
                cached = client.all_cached
        else:
            result = await args.func(None, args)
            cached = False
    except BCRPError as exc:
        # exceptions.py owns the code -> exit-status table (spec section 2), so
        # every entry point maps failures the same way.
        output.emit_error(command, exc, opts)
        return exit_code_for(exc)

    output.emit(command, result, opts, cached=cached)
    return 0


def _options_from(args: argparse.Namespace) -> Options:
    """Collapse the parsed flags into the resolved output options."""
    fmt = getattr(args, "format", "table")
    if getattr(args, "json", False):
        fmt = "json"  # legacy alias
    target = getattr(args, "output", None)
    return Options(
        fmt=fmt,
        output=Path(target) if target else None,
        quiet=getattr(args, "quiet", False),
        no_color=getattr(args, "no_color", False),
        ascii_mode=getattr(args, "ascii", False),
        refresh=getattr(args, "refresh", False),
        no_cache=getattr(args, "no_cache", False),
    )


def main(argv: list[str] | None = None) -> None:
    _setup_console()
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "describe":
        sys.exit(_run_describe(parser, args))

    if args.command == "serve":
        from ..server import main as serve_main

        serve_main()
        return

    render.configure(
        color=False if getattr(args, "no_color", False) else None,
        ascii_mode=getattr(args, "ascii", False),
    )

    try:
        exit_code = asyncio.run(_run_data_command(args, _options_from(args)))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        exit_code = 130

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
