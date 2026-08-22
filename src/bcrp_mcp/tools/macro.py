import asyncio
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from ..catalog import MACRO_SNAPSHOT_SERIES
from ..client import BCRPClient
from ..exceptions import BCRPAPIError, BCRPNotFoundError
from ..formatters import format_single_series_latest, format_latest_response

# ---------------------------------------------------------------------------
# Core logic — shared by the MCP tool below and by `bcrp_mcp.cli`.
# ---------------------------------------------------------------------------


async def get_macro_snapshot(client: BCRPClient, language: str = "esp") -> dict:
    """Fetch a real-time snapshot of Peru's key macroeconomic indicators."""
    daily_codes = MACRO_SNAPSHOT_SERIES["daily"]
    monthly_codes = MACRO_SNAPSHOT_SERIES["monthly"]

    # Fetch each daily series individually to guarantee correct code→value alignment.
    # The BCRP API reorders series from different categories in multi-series requests,
    # so we cannot reliably map codes to positions in a combined call.
    daily_tasks = [client.fetch([code], language=language) for code in daily_codes]
    monthly_task = client.fetch(monthly_codes, language=language)

    *daily_raws, monthly_raw = await asyncio.gather(
        *daily_tasks, monthly_task, return_exceptions=False
    )

    # Build daily section as a flat list of {code, name, period, value}
    daily_indicators = []
    snapshot_date = None
    for code, raw in zip(daily_codes, daily_raws):
        entry = format_single_series_latest(raw, code)
        daily_indicators.append(entry)
        if snapshot_date is None and entry.get("latest_period"):
            snapshot_date = entry["latest_period"]

    # Monthly section with last 3 periods
    monthly_result = format_latest_response(monthly_raw, monthly_codes, n=3)

    return {
        "snapshot_date": snapshot_date or "unknown",
        "daily_indicators": daily_indicators,
        "monthly_indicators": {
            "series": monthly_result.get("series", []),
            "latest_period": monthly_result.get("last_period"),
            "data": monthly_result.get("data", []),
        },
        "tip": (
            "Use bcrp_get_series with specific codes and date ranges for historical analysis. "
            "Use bcrp_search_catalog to find additional series codes. "
            "Monthly values are positional: data[period].values[i] corresponds to series[i]."
        ),
    }


# ---------------------------------------------------------------------------
# MCP tool wrapper
# ---------------------------------------------------------------------------


def register_macro_tools(mcp: FastMCP, client: BCRPClient) -> None:

    @mcp.tool(
        name="bcrp_get_macro_snapshot",
        description=(
            "Fetch a real-time snapshot of Peru's key macroeconomic indicators in one call.\n\n"
            "Returns the latest values for:\n"
            "**Daily indicators:**\n"
            "- Exchange rate (TC Interbancario S/ por US$)\n"
            "- BCRP policy rate (%)\n"
            "- International reserves (millions US$)\n"
            "- Copper price (cUS$ per pound)\n"
            "- Lima stock market index (BVL)\n\n"
            "**Monthly indicators (last 3 months):**\n"
            "- Total liquidity M2 (millions S/)\n"
            "- Private sector credit (millions S/)\n"
            "- Currency in circulation (millions S/)\n"
            "- Credit growth 12-month (%)\n\n"
            "Use `bcrp_get_series` for custom date ranges or additional series."
        ),
    )
    async def bcrp_get_macro_snapshot(
        language: Annotated[
            str,
            Field(default="esp", description="'esp' (Spanish) or 'ing' (English)"),
        ] = "esp",
    ) -> dict:
        try:
            return await get_macro_snapshot(client, language)
        except (BCRPNotFoundError, BCRPAPIError) as exc:
            raise ToolError(f"Failed to fetch macro snapshot: {exc}") from exc
