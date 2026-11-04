from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from ..client import BCRPClient
from ..exceptions import BCRPAPIError, BCRPNotFoundError, BCRPValidationError
from ..formatters import format_latest_response, format_metadata_only, format_series_response

# ---------------------------------------------------------------------------
# Core logic — shared by the MCP tools below and by `bcrp_mcp.cli`.
# Keeping fetch/validate/format here means the CLI and the MCP server can
# never drift: both transports call the exact same functions.
# ---------------------------------------------------------------------------


async def get_series(
    client: BCRPClient,
    series_codes: list[str],
    start_period: str | None = None,
    end_period: str | None = None,
    language: str = "esp",
) -> dict:
    """Fetch and format time series data for 1-10 same-frequency BCRP series."""
    if len(series_codes) > 10:
        raise BCRPValidationError("Maximum 10 series codes per request.")
    if end_period and not start_period:
        raise BCRPValidationError("Provide start_period when specifying end_period.")

    raw = await client.fetch(series_codes, start_period, end_period, language)
    result = format_series_response(raw, series_codes)
    if result.get("count", 0) == 0:
        return {
            **result,
            "warning": (
                "No data returned for the specified period range. "
                "The series may be discontinued or the period range may be out of bounds. "
                "Try omitting start_period/end_period to get the latest available data."
            ),
        }
    return result


async def get_latest(
    client: BCRPClient,
    series_codes: list[str],
    n_periods: int = 5,
    language: str = "esp",
) -> dict:
    """Fetch the most recent `n_periods` data points for 1-10 same-frequency series."""
    if len(series_codes) > 10:
        raise BCRPValidationError("Maximum 10 series codes per request.")

    raw = await client.fetch(series_codes, language=language)
    return format_latest_response(raw, series_codes, n_periods)


async def describe_series(
    client: BCRPClient,
    series_codes: list[str],
    language: str = "esp",
) -> dict:
    """Fetch metadata only (name, frequency, date range) for 1-10 series."""
    if len(series_codes) > 10:
        raise BCRPValidationError("Maximum 10 series codes per request.")

    raw = await client.fetch(series_codes, language=language)
    return format_metadata_only(raw, series_codes)


# ---------------------------------------------------------------------------
# MCP tool wrappers — thin adapters that translate the core functions'
# domain exceptions into ToolError for the MCP protocol.
# ---------------------------------------------------------------------------


def register_series_tools(mcp: FastMCP, client: BCRPClient) -> None:

    @mcp.tool(
        name="bcrp_get_series",
        description=(
            "Fetch time series data from the BCRP (Banco Central de Reserva del Perú) API.\n\n"
            "Accepts 1–10 series codes of the SAME frequency. Series codes can be found using\n"
            "`bcrp_search_catalog` or the `bcrp://series-catalog` resource.\n\n"
            "**Period format by frequency:**\n"
            "- Monthly: `YYYY-M` (e.g. `2024-1` = January 2024, `2024-12` = December 2024)\n"
            "- Quarterly: `YYYY-Q` (e.g. `2024-1` = Q1 2024, `2024-4` = Q4 2024)\n"
            "- Daily: `DD-MM-YYYY` (e.g. `01-01-2025`)\n"
            "- Annual: `YYYY` (e.g. `2024`)\n"
            "- Leave both periods empty to get the most recent available data.\n\n"
            "**Important:** All series in one call must have the same frequency (all daily, all monthly, etc.).\n"
            "Need MORE than 10 series, or a mix of frequencies? Use `bcrp_get_series_long`\n"
            "instead — up to 50 codes of any frequencies, returned as one tidy long table.\n\n"
            "Responses are cached on disk between calls, so repeating a query is free.\n"
            "An empty `series` list means the code is valid but has no data in that range,\n"
            "not that the code is wrong — check it with `bcrp_describe_series`.\n\n"
            "**Example codes:** PD04637PD (exchange rate), PD12301MD (policy rate), "
            "PN00196MM (total liquidity), PN03503MQ (GDP var%)"
        ),
    )
    async def bcrp_get_series(
        series_codes: Annotated[
            list[str],
            Field(
                description="List of 1–10 BCRP series codes (same frequency). "
                            "E.g. ['PD04637PD', 'PD12301MD']",
                min_length=1,
                max_length=10,
            ),
        ],
        start_period: Annotated[
            str | None,
            Field(
                default=None,
                description=(
                    "Start of date range. Format depends on series frequency:\n"
                    "- Monthly: YYYY-M (e.g. '2020-1')\n"
                    "- Quarterly: YYYY-Q (e.g. '2020-1')\n"
                    "- Daily: DD-MM-YYYY (e.g. '01-01-2025')\n"
                    "Leave empty for most recent data."
                ),
            ),
        ] = None,
        end_period: Annotated[
            str | None,
            Field(
                default=None,
                description="End of date range. Same format as start_period.",
            ),
        ] = None,
        language: Annotated[
            str,
            Field(
                default="esp",
                description="Language for series names: 'esp' (Spanish) or 'ing' (English)",
                pattern="^(esp|ing)$",
            ),
        ] = "esp",
    ) -> dict:
        try:
            return await get_series(client, series_codes, start_period, end_period, language)
        except BCRPValidationError as exc:
            raise ToolError(str(exc)) from exc
        except (BCRPNotFoundError, BCRPAPIError) as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="bcrp_get_latest",
        description=(
            "Get the most recent data points for 1–10 BCRP series (same frequency).\n\n"
            "Convenience wrapper around `bcrp_get_series` that fetches latest data without\n"
            "specifying a date range, then returns only the last `n_periods` values.\n\n"
            "Prefer this over `bcrp_get_series` when the question is \"what is it now?\" —\n"
            "today's exchange rate, the current policy rate. Use `bcrp_get_series` for a\n"
            "specific historical window, and `bcrp_get_series_long` for many series at once\n"
            "or mixed frequencies.\n\n"
            "Results are cached on disk; `n_periods` accepts 1–50 and defaults to 5.\n\n"
            "**Example codes:**\n"
            "- Daily rates/prices: PD04637PD, PD12301MD, PD04650MD, PD04701XD\n"
            "- Monthly monetary: PN00196MM, PN00496MM, PN00178MM\n"
            "- Quarterly growth: PN03503MQ, PN03501MQ"
        ),
    )
    async def bcrp_get_latest(
        series_codes: Annotated[
            list[str],
            Field(
                description="List of 1–10 BCRP series codes (same frequency)",
                min_length=1,
                max_length=10,
            ),
        ],
        n_periods: Annotated[
            int,
            Field(
                default=5,
                ge=1,
                le=50,
                description="Number of most recent periods to return (1–50). Default: 5.",
            ),
        ] = 5,
        language: Annotated[
            str,
            Field(default="esp", description="'esp' (Spanish) or 'ing' (English)"),
        ] = "esp",
    ) -> dict:
        try:
            return await get_latest(client, series_codes, n_periods, language)
        except BCRPValidationError as exc:
            raise ToolError(str(exc)) from exc
        except (BCRPNotFoundError, BCRPAPIError) as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="bcrp_describe_series",
        description=(
            "Get metadata about 1–10 BCRP series without fetching all data points.\n\n"
            "Returns series names, frequency, decimal precision, and available date range.\n"
            "Use this to verify series codes exist and understand what they measure before\n"
            "fetching large date ranges with `bcrp_get_series`."
        ),
    )
    async def bcrp_describe_series(
        series_codes: Annotated[
            list[str],
            Field(
                description="List of 1–10 BCRP series codes to describe",
                min_length=1,
                max_length=10,
            ),
        ],
        language: Annotated[
            str,
            Field(default="esp", description="'esp' (Spanish) or 'ing' (English)"),
        ] = "esp",
    ) -> dict:
        try:
            return await describe_series(client, series_codes, language)
        except BCRPValidationError as exc:
            raise ToolError(str(exc)) from exc
        except (BCRPNotFoundError, BCRPAPIError) as exc:
            raise ToolError(str(exc)) from exc
