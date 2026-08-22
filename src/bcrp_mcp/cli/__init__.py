"""`bcrp` command-line interface.

This is a second transport on top of the exact same tool-core functions the
MCP server exposes (see ``bcrp_mcp.tools.*``): `bcrp series get`, `bcrp
catalog search`, `bcrp macro snapshot`, etc. all call the identical
fetch/validate/format logic an MCP client triggers via `bcrp_get_series`,
`bcrp_search_catalog`, `bcrp_get_macro_snapshot`, so results never drift
between the CLI and the MCP tools. Pass ``--json`` on any data command to
get the exact tool-output dict.
"""

from .app import main

__all__ = ["main"]
