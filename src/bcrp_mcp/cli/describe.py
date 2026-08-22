"""`bcrp describe` — the manifest that lets an agent learn the CLI cold.

Everything here is walked out of the live ``argparse`` tree: add a subcommand
and it shows up in ``describe --json`` without anyone remembering to update a
document. Per-command extras (``row_fields``, ``supports_all``, ``examples``)
are attached at registration time with ``set_defaults`` so they travel with the
parser too.
"""

from __future__ import annotations

import argparse
from typing import Any

from .. import __version__
from ..client import BASE_URL
from ..exceptions import EXIT_CODE_MEANINGS
from .output import FORMATS

_HIDDEN_DESTS = {"func", "render", "rows", "needs_client", "row_fields", "supports_all", "examples"}


def _type_name(action: argparse.Action) -> str:
    if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return "bool"
    base = getattr(action.type, "__name__", None) or "string"
    base = {"str": "string", "int": "integer", "float": "number"}.get(base, base)
    if action.nargs in ("+", "*") or isinstance(action.nargs, int):
        return f"list[{base}]"
    return base


def _describe_action(action: argparse.Action) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "name": action.option_strings[0] if action.option_strings else action.dest,
        "type": _type_name(action),
        "help": (action.help or "").replace("\n", " ").strip(),
    }
    if action.option_strings:
        entry["aliases"] = action.option_strings[1:]
        entry["default"] = action.default
        entry["repeatable"] = action.nargs in ("+", "*")
    else:
        entry["required"] = action.nargs not in ("?", "*")
        entry["default"] = action.default
    if action.choices:
        entry["choices"] = list(action.choices)
    return entry


def _subparser_actions(parser: argparse.ArgumentParser) -> list[argparse._SubParsersAction]:
    return [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]


def _walk(parser: argparse.ArgumentParser, path: list[str], helps: dict[str, str]) -> list[dict[str, Any]]:
    """Depth-first walk yielding one manifest entry per leaf command."""
    children = _subparser_actions(parser)
    if children:
        commands: list[dict[str, Any]] = []
        for action in children:
            sub_helps = {c.dest: (c.help or "") for c in action._get_subactions()}
            for name, sub in action.choices.items():
                commands.extend(_walk(sub, path + [name], sub_helps))
        return commands

    name = " ".join(path)
    arguments, options = [], []
    for action in parser._actions:
        if action.dest in _HIDDEN_DESTS or isinstance(action, argparse._HelpAction):
            continue
        if action.dest == argparse.SUPPRESS:
            continue
        (options if action.option_strings else arguments).append(_describe_action(action))

    entry: dict[str, Any] = {
        "name": name,
        "summary": (parser.description or helps.get(path[-1], "") or "").replace("\n", " ").strip(),
        "arguments": arguments,
        "options": options,
        "row_fields": parser.get_default("row_fields") or [],
        "supports_all": bool(parser.get_default("supports_all")),
        "examples": parser.get_default("examples") or [],
        # `needs_client` already records which commands call the API, so it
        # doubles as the "does this touch the network?" signal a caller needs
        # to know whether a result can be cached or is answered offline.
        "network": bool(parser.get_default("needs_client")),
    }
    return [entry]


def build_manifest(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Machine-readable description of the whole CLI (spec section 4)."""
    global_options = [
        _describe_action(a)
        for a in parser._actions
        if a.option_strings
        and not isinstance(a, (argparse._HelpAction, argparse._VersionAction))
        and a.dest not in _HIDDEN_DESTS
    ]
    return {
        "name": "bcrp",
        "version": __version__,
        "source": {
            "api": "BCRPData (Banco Central de Reserva del Perú)",
            "base_url": BASE_URL,
            "auth": "none",
        },
        "formats": list(FORMATS),
        "exit_codes": dict(EXIT_CODE_MEANINGS),
        "global_options": global_options,
        "commands": _walk(parser, [], {}),
    }


def render_manifest(manifest: dict[str, Any]) -> None:
    """Human summary of the manifest — what a bare `bcrp describe` prints."""
    from . import render

    render.title(f"{manifest['name']} {manifest['version']}")
    render.meta([
        manifest["source"]["api"],
        f"auth: {manifest['source']['auth']}",
        "formats: " + ", ".join(manifest["formats"]),
    ])

    render.section("Commands")
    for cmd in manifest["commands"]:
        args = " ".join(
            (a["name"].upper() if a.get("required") else f"[{a['name'].upper()}]")
            for a in cmd["arguments"]
        )
        header = f"{cmd['name']} {args}".strip()
        print(f"  {render.cyan(header)}")
        if cmd["summary"]:
            print(f"    {render.dim(render.truncate(cmd['summary'], render.terminal_width() - 6))}")
        if cmd["row_fields"]:
            print(f"    {render.dim('rows: ' + ', '.join(cmd['row_fields']))}")

    render.section("Exit codes")
    render.kv_block([(code, meaning) for code, meaning in manifest["exit_codes"].items()])

    render.section("Examples")
    for cmd in manifest["commands"]:
        for example in cmd["examples"]:
            print(f"  {example}")
    print()
    print(render.dim("Machine-readable manifest: bcrp describe --json"))


def filter_manifest(manifest: dict[str, Any], command: str) -> dict[str, Any] | None:
    """Narrow the manifest to a single command (``describe <command> --json``)."""
    wanted = command.strip().replace("-", " ").lower()
    for cmd in manifest["commands"]:
        if cmd["name"] == wanted or cmd["name"].replace(" ", "-") == command.strip().lower():
            return {**manifest, "commands": [cmd]}
    return None
