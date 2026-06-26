from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from ..catalog import list_categories, search_catalog


def register_catalog_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="bcrp_search_catalog",
        description=(
            "Search the built-in catalog of important BCRP series by keyword.\n\n"
            "Returns matching series codes, names, descriptions, frequency, units, and\n"
            "the period format needed to query them with `bcrp_get_series`.\n\n"
            "**Example queries:**\n"
            "- 'tipo de cambio' → exchange rate series\n"
            "- 'tasa referencia' → BCRP policy rate\n"
            "- 'reservas internacionales' → international reserves\n"
            "- 'cobre' → copper price\n"
            "- 'liquidez' → monetary liquidity (M1/M2)\n"
            "- 'credito' → private sector credit\n"
            "- 'BVL' → Lima stock exchange index\n"
            "- 'PBI' → GDP quarterly series\n\n"
            "Use `bcrp_list_catalog_categories` to see all available categories."
        ),
    )
    async def bcrp_search_catalog(
        query: Annotated[
            str,
            Field(description="Search term (Spanish or English). E.g. 'exchange rate', 'tipo de cambio'"),
        ],
        category: Annotated[
            str | None,
            Field(
                default=None,
                description=(
                    "Filter by category ID. E.g. 'exchange_rates_daily', 'liquidity_monthly'. "
                    "Use bcrp_list_catalog_categories to see all options."
                ),
            ),
        ] = None,
        frequency: Annotated[
            str | None,
            Field(
                default=None,
                description="Filter by frequency: 'daily', 'monthly', 'quarterly', 'annual'",
                pattern="^(daily|monthly|quarterly|annual|weekly)?$",
            ),
        ] = None,
    ) -> dict:
        results = search_catalog(query, category, frequency)
        if not results:
            return {
                "results": [],
                "count": 0,
                "message": (
                    f"No series found for '{query}'. "
                    "Try broader terms or use bcrp_list_catalog_categories to explore available categories. "
                    "Note: the catalog contains only commonly used series; the full BCRP database has 8,000+ series "
                    "discoverable at https://estadisticas.bcrp.gob.pe"
                ),
            }
        return {
            "results": results,
            "count": len(results),
            "tip": "Use the 'code' field with bcrp_get_series or bcrp_get_latest to fetch data.",
        }

    @mcp.tool(
        name="bcrp_list_catalog_categories",
        description=(
            "List all available categories in the BCRP series catalog.\n\n"
            "Returns category IDs (usable as the `category` filter in `bcrp_search_catalog`),\n"
            "the number of series per category, and their frequency.\n\n"
            "Categories include: exchange rates, interest rates, international reserves,\n"
            "liquidity (M1/M2), credit, financial markets, commodities, and GDP."
        ),
    )
    async def bcrp_list_catalog_categories() -> dict:
        categories = list_categories()
        return {
            "categories": categories,
            "total_catalogued_series": sum(int(c["series_count"]) for c in categories),
            "note": (
                "This catalog covers the most commonly used BCRP series. "
                "The full BCRPData database contains 8,000+ monthly series, 2,700+ quarterly, and 800+ daily. "
                "Discover more at https://estadisticas.bcrp.gob.pe/estadisticas/series/"
            ),
        }
