import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import BCRPClient
from .config import get_settings
from .prompts.economic import register_prompts
from .resources.guides import register_resources
from .tools.bulk import register_bulk_tools
from .tools.catalog import register_catalog_tools
from .tools.macro import register_macro_tools
from .tools.series import register_series_tools

_INSTRUCTIONS = """\
You have access to the BCRPData API — the official open-access statistics database of the
Banco Central de Reserva del Perú (BCRP), Peru's central bank.

No authentication is required. The API is fully public and updated in real time.

## Tools (7)

- **bcrp_get_series** — Fetch time series data for 1–10 BCRP series with optional date range
- **bcrp_get_series_long** — Fetch up to 50 series (mixed frequencies) as one tidy long-format table
- **bcrp_get_latest** — Get the most recent N data points for 1–10 series
- **bcrp_describe_series** — Get series metadata (name, frequency, date range) without all data
- **bcrp_search_catalog** — Search the built-in catalog of important series by keyword
- **bcrp_list_catalog_categories** — List all catalog categories with series counts
- **bcrp_get_macro_snapshot** — Real-time snapshot of key Peruvian economic indicators

## Prompts (3)

- **inflation_and_monetary_analysis** — Monetary policy and inflation analysis workflow
- **exchange_rate_analysis** — Exchange rate dynamics and dollarization analysis
- **economic_growth_analysis** — GDP growth, credit, and liquidity cycle analysis

## Resources (3)

- **bcrp://api-guide** — Complete API reference: URL structure, formats, response schema
- **bcrp://period-formats** — Period format reference table (daily/monthly/quarterly/annual)
- **bcrp://series-catalog** — Curated catalog of important series with codes, names, and units

## Typical Workflow

1. Use a **prompt** for a structured research workflow.
2. Use `bcrp_search_catalog` or `bcrp://series-catalog` to find series codes.
3. Use `bcrp_describe_series` to verify a code exists and see its date range.
4. Use `bcrp_get_series` for historical data or `bcrp_get_latest` for current values.
   For many series at once — or mixed frequencies — use `bcrp_get_series_long`.
5. Use `bcrp_get_macro_snapshot` for a quick overview of all key indicators.

## Period Format Quick Reference

- Daily: DD-MM-YYYY (e.g. '01-01-2025')
- Monthly: YYYY-M (e.g. '2024-1' = January 2024)
- Quarterly: YYYY-Q (e.g. '2024-1' = Q1 2024)
- All series in a single bcrp_get_series call must be the same frequency.
"""


def create_app() -> FastMCP:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(levelname)s [%(name)s] %(message)s",
    )

    client = BCRPClient(settings)

    @asynccontextmanager
    async def lifespan(app: FastMCP) -> AsyncIterator[None]:
        async with client:
            yield

    mcp = FastMCP(
        name="BCRP Economic Data",
        instructions=_INSTRUCTIONS,
        lifespan=lifespan,
    )

    register_series_tools(mcp, client)
    register_bulk_tools(mcp, client)
    register_catalog_tools(mcp)
    register_macro_tools(mcp, client)
    register_resources(mcp)
    register_prompts(mcp)

    return mcp


def main() -> None:
    load_dotenv()
    app = create_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
