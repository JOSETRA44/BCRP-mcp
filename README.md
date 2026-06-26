[![MCP Badge](https://lobehub.com/badge/mcp/josetra44-bcrp-mcp)](https://lobehub.com/mcp/josetra44-bcrp-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen.svg)]()

# BCRP MCP Server

Connects any MCP-compatible AI agent to **BCRPData** — the official open-access economic statistics database of the [Banco Central de Reserva del Perú (BCRP)](https://www.bcrp.gob.pe/).

Access real-time and historical data for **exchange rates, interest rates, international reserves, monetary liquidity, private sector credit, commodity prices, stock market indicators, and GDP** — no API key required.

**Works with:** Claude Desktop · Claude Code · Cursor · VS Code Copilot · Windsurf · Zed · Continue.dev · any MCP client

---

## Quickstart (2 minutes)

**1. Install the server**

```bash
# Option A: uvx (recommended — zero setup)
uvx bcrp-mcp

# Option B: pip
pip install bcrp-mcp
```

> No API key needed. BCRPData is a fully public API.

**2. Add to your AI client** — see the [Configuration](#configuration-by-client) section.

**3. Start using it:**

```
> What is the current BCRP policy rate and exchange rate?

> Use bcrp_get_macro_snapshot to get a snapshot of Peru's key economic indicators.

> Show me the evolution of Peru's international reserves since 2020.
```

---

## Prerequisites

### Python 3.11+
```bash
python --version   # needs 3.11 or higher
```

### uv (recommended)
```bash
# Windows
winget install astral-sh.uv

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Installation

### Option A — uvx (zero configuration)
```bash
uvx bcrp-mcp

# Upgrade later
uv tool upgrade bcrp-mcp
```

### Option B — pip
```bash
pip install bcrp-mcp
bcrp-mcp   # starts the server
```

### Option C — From source (development)
```bash
git clone https://github.com/JOSETRA44/bcrp-mcp.git
cd bcrp-mcp
uv sync
cp .env.example .env    # optional — customize settings
uv run bcrp-mcp
```

---

## Configuration (Optional)

All settings have sensible defaults. Override via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `BCRP_CACHE_TTL` | `300` | Response cache in seconds (0 = disabled) |
| `BCRP_TIMEOUT` | `30` | HTTP timeout in seconds |
| `BCRP_MAX_RETRIES` | `3` | Retries on transient errors |
| `BCRP_LANGUAGE` | `esp` | Default language: `esp` (Spanish) or `ing` (English) |
| `LOG_LEVEL` | `INFO` | `DEBUG` · `INFO` · `WARNING` · `ERROR` |

> No API key required — BCRPData is fully open access.

---

## Configuration by Client

### Claude Desktop

**Config file:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bcrp": {
      "command": "uvx",
      "args": ["bcrp-mcp"]
    }
  }
}
```

Restart Claude Desktop after saving. You'll see a hammer icon (🔨) confirming the server is loaded.

### Claude Code (CLI)

Add to your `.mcp.json` or `.antigravity.json`:

```json
{
  "mcpServers": {
    "bcrp": {
      "command": "uvx",
      "args": ["bcrp-mcp"]
    }
  }
}
```

**From source:**
```json
{
  "mcpServers": {
    "bcrp": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/bcrp-mcp",
        "run", "bcrp-mcp"
      ]
    }
  }
}
```

Run `/mcp` in the Claude Code prompt to confirm — you should see `bcrp` with 6 tools.

### Cursor

```json
{
  "mcpServers": {
    "bcrp": {
      "command": "uvx",
      "args": ["bcrp-mcp"]
    }
  }
}
```

### VS Code + GitHub Copilot

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "bcrp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["bcrp-mcp"]
    }
  }
}
```

### Windsurf

Config: `%APPDATA%\Codeium\windsurf\mcp_config.json`

```json
{
  "mcpServers": {
    "bcrp": {
      "command": "uvx",
      "args": ["bcrp-mcp"]
    }
  }
}
```

### Zed

Edit `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "bcrp": {
      "command": {
        "path": "uvx",
        "args": ["bcrp-mcp"]
      }
    }
  }
}
```

### Continue.dev

Edit `.continue/config.yaml`:

```yaml
mcpServers:
  - name: bcrp
    command: uvx
    args:
      - bcrp-mcp
```

### Generic stdio

```
command:  uvx
args:     ["bcrp-mcp"]
```

---

## Available Tools (6)

| Tool | Description |
|------|-------------|
| `bcrp_get_series` | Fetch 1–10 series with optional date range (all same frequency) |
| `bcrp_get_latest` | Get the most recent N data points for 1–10 series |
| `bcrp_describe_series` | Metadata only: series names, frequency, available date range |
| `bcrp_search_catalog` | Search built-in catalog of important series by keyword |
| `bcrp_list_catalog_categories` | List all catalog categories with series counts |
| `bcrp_get_macro_snapshot` | Real-time snapshot of Peru's key macroeconomic indicators |

---

## Available Prompts (3)

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `inflation_and_monetary_analysis` | `start_year`, `end_year` | Structured workflow: policy rate, liquidity (M2), credit growth |
| `exchange_rate_analysis` | `start_date`, `end_date` | Exchange rate dynamics, reserves, dollarization |
| `economic_growth_analysis` | `start_year`, `end_year` | GDP growth, monetary multiplier, credit cycle |

---

## Available Resources (3)

| Resource URI | Contents |
|-------------|----------|
| `bcrp://api-guide` | Complete API reference: URL structure, period formats, response schema |
| `bcrp://period-formats` | Quick reference table for all period formats by frequency |
| `bcrp://series-catalog` | Curated catalog of important series with codes, names, units |

---

## Key Series Codes

### Daily (format: `DD-MM-YYYY`)

| Code | Indicator | Unit |
|------|-----------|------|
| `PD04637PD` | TC Interbancario Compra (USD/PEN) | S/ por US$ |
| `PD04638PD` | TC Interbancario Venta (USD/PEN) | S/ por US$ |
| `PD12301MD` | Tasa de Referencia BCRP | % anual |
| `PD04692MD` | Tasa Interbancaria, S/ | % anual |
| `PD04650MD` | Reservas Internacionales Netas | Millones US$ |
| `PD38026MD` | Índice General Bursátil BVL | Índice |
| `PD04701XD` | Precio del Cobre | cUS$ por libra |
| `PD04705XD` | Precio del Petróleo WTI | US$ por barril |
| `PD04721XD` | Índice Dow Jones | Índice |

### Monthly (format: `YYYY-M`)

| Code | Indicator | Unit |
|------|-----------|------|
| `PN00196MM` | Liquidez Total (M2) | Millones S/ |
| `PN00178MM` | Circulante (M0) | Millones S/ |
| `PN00190MM` | Liquidez en Soles | Millones S/ |
| `PN00180MM` | Liquidez var% 12 meses | % anual |
| `PN00496MM` | Crédito Sector Privado | Millones S/ |
| `PN00500MM` | Crédito var% 12 meses | % anual |

### Quarterly (format: `YYYY-Q`)

| Code | Indicator | Unit |
|------|-----------|------|
| `PN03503MQ` | PBI Nominal var% | % trimestral |
| `PN03501MQ` | Liquidez MN var% | % trimestral |
| `PN03502MQ` | Emisión Primaria var% | % trimestral |
| `PN03504MQ` | Multiplicador Monetario var% | % trimestral |

---

## Example Queries

```python
# Get the current exchange rate (last 5 trading days)
bcrp_get_latest(series_codes=["PD04637PD", "PD04638PD"], n_periods=5)

# BCRP policy rate since 2022
bcrp_get_series(
    series_codes=["PD12301MD"],
    start_period="01-01-2022",
    end_period="30-06-2026"
)

# Monthly liquidity (M2) and credit growth last 2 years
bcrp_get_series(
    series_codes=["PN00196MM", "PN00496MM", "PN00500MM"],
    start_period="2024-1",
    end_period="2026-6"
)

# Complete macro snapshot
bcrp_get_macro_snapshot()

# Search for more series
bcrp_search_catalog(query="tipo de cambio", frequency="monthly")
bcrp_search_catalog(query="exportaciones")
```

---

## API Notes

- **No authentication required** — BCRPData is fully public.
- **Multiple series** in one call must be the **same frequency** (all daily, all monthly, etc.).
- **Period formats** differ by frequency — see `bcrp://period-formats` resource.
- The BCRP database has **8,000+ monthly, 2,700+ quarterly, and 800+ daily** series.
  Browse the full catalog at [estadisticas.bcrp.gob.pe](https://estadisticas.bcrp.gob.pe/estadisticas/series/).

---

## Verify It's Working

```bash
# Interactive browser UI
npx @modelcontextprotocol/inspector uvx bcrp-mcp

# Quick smoke test
echo "" | uvx bcrp-mcp

# Unit tests (from source)
uv sync --group dev
uv run pytest tests/ -v
```

---

## Troubleshooting

**`command not found: uvx`**
Install uv: https://docs.astral.sh/uv/getting-started/installation/

**Empty results for a series**
The series code may be discontinued or the period range may not have data.
Run `bcrp_describe_series` first to check available date range.

**Series codes with mismatched frequencies**
All series in a single call must share the same frequency.
Daily and monthly series cannot be mixed — make two separate calls.

**Slow first start**
uv downloads and caches the package on first run. Subsequent starts take ~0.2s.

---

## Project Structure

```
bcrp-mcp/
├── src/bcrp_mcp/
│   ├── server.py          # FastMCP entry point
│   ├── config.py          # Settings (pydantic-settings, no auth required)
│   ├── client.py          # Async HTTP client + TTL cache + retry
│   ├── exceptions.py      # Error hierarchy
│   ├── formatters.py      # Raw BCRP JSON → clean AI-friendly dicts
│   ├── catalog.py         # Curated series catalog + search
│   ├── tools/             # 6 MCP tools
│   ├── prompts/           # 3 MCP prompts (analysis workflows)
│   └── resources/         # 3 MCP resources (guides + catalog)
├── tests/                 # Unit tests (no network required)
├── .env.example           # Optional configuration
└── pyproject.toml
```

---

## License

[MIT](LICENSE) — © 2026 JOSETRA44

---

## Data Source

All data comes from **BCRPData** — the official open statistics platform of the
Banco Central de Reserva del Perú. For terms of use, see:
https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/condicionesUso
