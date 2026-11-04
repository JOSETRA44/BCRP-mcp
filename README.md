<img width="1600" height="500" alt="BCRP MCP" src="https://github.com/user-attachments/assets/79323612-ebec-49ea-91d5-321b5950bbbc" />

[![MCP Badge](https://lobehub.com/badge/mcp/josetra44-bcrp-mcp)](https://lobehub.com/mcp/josetra44-bcrp-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen.svg)]()

# BCRP MCP Server

<!-- mcp-name: io.github.JOSETRA44/bcrp-mcp -->

Connects any MCP-compatible AI agent to **BCRPData** — the official open-access economic statistics database of the [Banco Central de Reserva del Perú (BCRP)](https://www.bcrp.gob.pe/).

Access real-time and historical data for **exchange rates, interest rates, international reserves, monetary liquidity, private sector credit, commodity prices, stock market indicators, and GDP** — no API key required.

**Works with:** Claude Desktop · Claude Code · Cursor · VS Code Copilot · Windsurf · Zed · Continue.dev · any MCP client

---



## What you can ask it

| Ask | Tool that answers it |
|---|---|
| "How much is the dollar in Peru today?" | `bcrp_get_latest` |
| "Plot Peru's GDP over the last ten years" | `bcrp_get_series` |
| "What's the current state of the Peruvian economy?" | `bcrp_get_macro_snapshot` |
| "I need the series code for inflation" | `bcrp_search_catalog` |
| "Export FX, inflation and GDP together as one CSV" | `bcrp_get_series_long` |
| "What period does this series actually cover?" | `bcrp_describe_series` |

**No API key, no registration, nothing to configure.** BCRPData is fully public.

Series are identified by opaque codes like `PD04637PD`, which mean nothing on
sight — so start from the catalog:

```bash
bcrp catalog search "tipo de cambio"     # find the code
bcrp series latest PD04637PD --n 5       # then fetch it
```

## Quickstart — one command

```bash
npx bcrp-mcp
```

That installs all three pieces, which are designed to work together:

| Piece | What it is |
|-------|-----------|
| `bcrp-mcp` | The MCP server, so AI clients can query BCRPData |
| `bcrp` | The CLI — same tools, for humans and scripts |
| `bcrp` skill | Teaches agents *how* to use them correctly |

It also registers the server with Claude Code automatically when the `claude` CLI is
present, and prints the config snippet for other clients.

```bash
npx bcrp-mcp --help          # all options
npx bcrp-mcp --skill-only    # just the agent skill
npx bcrp-mcp --no-skill      # just the server + CLI
npx bcrp-mcp --from .        # install the Python side from a local checkout
```

<details>
<summary>Prefer to install the Python package directly?</summary>

```bash
uv tool install bcrp-mcp     # recommended
pipx install bcrp-mcp
pip install bcrp-mcp
```

The npx installer just wraps this and adds the skill. No API key is needed either way —
BCRPData is a fully public API.

</details>

**Then start using it:**

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

## Command-Line Interface

Installing this package also puts a standalone `bcrp` CLI on your PATH. It calls the
**exact same tool-core functions** as the MCP server (`bcrp_mcp.tools.*`), so results
never drift between the two — the CLI is just a second transport on top of one shared
implementation. Useful for scripting, cron jobs, or checking data without an AI client.

```bash
bcrp --help                 # full command tree
bcrp series --help
bcrp series latest PD04637PD PD12301MD --n 3
bcrp series get PN00196MM --start 2020-1 --end 2024-12
bcrp series describe PD04637PD
bcrp catalog search "tipo de cambio"
bcrp catalog categories
bcrp macro snapshot
bcrp serve                  # run the MCP server over stdio (same as `bcrp-mcp`)
```

Output is formatted as box-drawn tables sized to your terminal, with each value rounded
to the precision the BCRP actually publishes it at:

```
Tipo de cambio
daily · 20.Jul.26 → 22.Jul.26 · 3 periods

Series
  PD04637PD  Tipo de cambio - TC Interbancario (S/ por US$) - Compra
  PD12301MD  Tasas de interés - Tasa de Referencia de la Política Monetaria

Data
  ┌───────────┬───────────┬───────────┐
  │ Period    │ PD04637PD │ PD12301MD │
  ├───────────┼───────────┼───────────┤
  │ 20.Jul.26 │     3.402 │      4.25 │
  │ 21.Jul.26 │     3.397 │      4.25 │
  │ 22.Jul.26 │         — │      4.25 │
  └───────────┴───────────┴───────────┘
```

Output flags available on every data command:

| Flag | Effect |
|------|--------|
| `--json` | Raw tool-output dict — identical to what the MCP tool returns |
| `--no-color` | Disable ANSI colour (also honours `NO_COLOR`) |
| `--ascii` | Plain ASCII tables instead of Unicode box characters |
| `--lang esp\|ing` | Language for series names |

Exit codes: `0` success, `2` invalid input, `3` series not found, `4` BCRP API error.

```bash
bcrp series latest PD04637PD --json | jq '.data[-1]'
```

---

## Agent Skill

The `bcrp` skill teaches AI agents how to use these tools *correctly* — the parts that
otherwise produce confidently wrong answers: values are positional rather than keyed,
mixed-frequency requests are silently dropped rather than rejected, period formats differ
per frequency, and `n.d.` means "not published" rather than zero.

It installs to `~/.claude/skills/bcrp` via `npx bcrp-mcp` (or `--skill-only`).

The skill's reference files are **generated from the package's own catalog and API
guides**, so they can't drift from what the server actually serves:

```bash
uv run python scripts/gen_skill_refs.py
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
│   ├── tools/             # 6 MCP tools (thin wrappers around shared core logic)
│   ├── cli/               # `bcrp` CLI — same tool-core functions, argparse transport
│   ├── prompts/           # 3 MCP prompts (analysis workflows)
│   └── resources/         # 3 MCP resources (guides + catalog)
├── skills/bcrp/           # Agent skill (references/ generated from catalog.py)
├── npm/                   # `npx bcrp-mcp` one-command installer
├── scripts/               # gen_skill_refs.py — regenerates skill references
├── tests/                 # Unit tests (no network required)
├── .env.example           # Optional configuration
└── pyproject.toml
```

---

## Data Source

All data comes from **BCRPData** — the official open statistics platform of the
Banco Central de Reserva del Perú. For terms of use, see:
https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/condicionesUso

## CLI for agents

Peru's central bank series, straight from the source and updated daily.

This CLI follows [`ARSENAL-SPEC.md`](../ARSENAL-SPEC.md), the contract every research
tool in this workspace shares: an agent that can drive one can drive all of them.

### Discover it without reading this file

```bash
bcrp describe --json          # every command, argument, row field and example
bcrp describe <command> --json
```

The manifest is derived from the parser itself, so it cannot drift out of date.

### Output

`-f, --format` accepts `table`, `json`, `jsonl`, `csv`, `md`; `-o FILE` writes to a file; `-q` silences notes.
**Data goes to stdout, notes and progress to stderr** — piping to `jq` always yields
parseable JSON.

`--format json` returns the standard envelope:

```json
{
  "ok": true,
  "command": "series get",
  "source": "bcrp",
  "fetched_at": "2026-08-21T14:03:11Z",
  "cached": false,
  "count": 10,
  "meta": {},
  "data": {},
  "rows": []
}
```

`count` always equals `len(rows)`. An empty result is exit 0, not an error. Failures
return an error envelope carrying `error.code`, `error.message` and an actionable
`error.hint`, printed to stdout in machine formats so a pipeline can inspect it.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | success (including an empty result set) |
| 1 | API returned an error or an unexpected response |
| 2 | usage error (bad flag, bad argument, unknown format) |
| 3 | resource not found (unknown series code) |
| 4 | auth or configuration error |
| 5 | rate limited or quota exhausted |
| 6 | network failure or timeout |

### Cache

Results are cached on disk and survive between invocations, so a repeated query is
instant. `--refresh` refetches and rewrites; `--no-cache` skips it entirely; the
envelope reports `cached`.

```bash
bcrp cache stats -f json
bcrp cache clear
```

### Recipes

```bash
bcrp series get PN01288PM --start 2015-1 --end 2025-1 -f csv -o pbi.csv
bcrp series get PD04637PD PD04638PD --start 01-01-2024 -f jsonl
bcrp series latest PD04637PD --n 10 -f json
bcrp series latest PD04637PD PN01288PM -f md
bcrp series describe PD04637PD -f json
```

Or through the workspace-wide entry point: `arsenal run bcrp <command> ...`,
and `arsenal doctor bcrp --live` to check this CLI still honours the contract.

## Troubleshooting

**"I don't know the series code"**
That is what the catalog is for: `bcrp catalog search <keyword>`, or
`bcrp catalog categories` to browse. Codes are not guessable.

**`Not found` for a code that looks right**
BCRP codes encode frequency in their suffix (`...PD` daily, `...PM` monthly).
A code exists only at its own frequency. Confirm with `bcrp series describe`.

**"Cannot mix frequencies"**
A single `series get` call takes series that share one frequency. Split daily and
monthly series into separate calls.

**Accented series names look wrong on Windows**
Fixed — the CLI forces UTF-8 output. If you still see mojibake, you are on an old
installed copy: `uv tool install --force bcrp-mcp`.

## Documentation

| Document | What's in it |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | What changed in each release |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Dev setup, the CLI contract, how to run the tests |
| [`SECURITY.md`](SECURITY.md) | What this server sends and where; how to report a vulnerability |
| [`server.json`](server.json) | Registry metadata for the official MCP registry |
| [`../ARSENAL-SPEC.md`](../ARSENAL-SPEC.md) | The CLI contract shared by every research server here |

## Licence

MIT — see [`LICENSE`](LICENSE).
