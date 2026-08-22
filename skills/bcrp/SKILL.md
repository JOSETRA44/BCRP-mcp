---
name: bcrp
description: >-
  Get real Peruvian economic data from BCRPData, the Banco Central de Reserva del Perú's
  official statistics database — exchange rates (USD/PEN, sol, dólar), the BCRP policy
  rate (tasa de referencia), inflation, GDP (PBI), international reserves (RIN), monetary
  liquidity (M1/M2), private-sector credit, copper/gold/oil prices, and the BVL index.
  Use this skill whenever the user asks about Peru's economy, the Peruvian sol, the BCRP,
  Peruvian interest rates, tipo de cambio, reservas, or any Peruvian macroeconomic
  indicator or time series — including when they just say "how much is the dollar in
  Peru", "cuánto está el dólar", "grafica el PBI", or ask for Peruvian economic history,
  charts, or analysis. Also use it whenever a BCRP series code (like PD04637PD or
  PN00196MM) appears. Prefer this skill over web search or recalling figures from
  memory: BCRP data changes daily and only these tools return authoritative current
  values.
---

# BCRP — Peruvian central bank economic data

BCRPData is the open statistics database of Peru's central bank. It is fully public —
no API key, no account, no rate limit to negotiate. This skill covers how to pull data
from it reliably and how to avoid the handful of quirks that silently produce wrong
answers.

## Which interface to use

The same functionality is exposed two ways, backed by identical code:

- **MCP tools** (`bcrp_get_series`, `bcrp_get_latest`, …) — use these when the `bcrp`
  MCP server is connected. Preferred: structured data comes straight back to you.
- **`bcrp` CLI** — use when there is no MCP server but the command exists in the shell.
  Add `--json` to any data command to get the exact same payload the MCP tool returns,
  which is what you want when you plan to parse it.

Check which is available before planning a multi-step analysis. If neither exists, the
underlying API is a plain public GET — see `references/api.md` to call it directly.

| Task | MCP tool | CLI |
|------|----------|-----|
| Historical range | `bcrp_get_series` | `bcrp series get CODE --start P --end P` |
| Current values | `bcrp_get_latest` | `bcrp series latest CODE --n 5` |
| Verify a code / date range | `bcrp_describe_series` | `bcrp series describe CODE` |
| Find a code by keyword | `bcrp_search_catalog` | `bcrp catalog search "query"` |
| Browse categories | `bcrp_list_catalog_categories` | `bcrp catalog categories` |
| Everything at once | `bcrp_get_macro_snapshot` | `bcrp macro snapshot` |

## Core workflow

1. **Find the code.** Search the catalog by keyword rather than guessing a code —
   invented codes fail with a "not found" error, and the code format (`PD04637PD`) is
   not guessable. The catalog covers ~35 of the most-used series; the full database has
   8,000+ monthly, 2,700+ quarterly and 800+ daily series browsable at
   <https://estadisticas.bcrp.gob.pe/estadisticas/series/>.
2. **Describe before fetching a long range.** `describe` returns the frequency and the
   real first/last available period without pulling every data point. This tells you
   which period format to use and stops you requesting years that don't exist.
3. **Fetch.** Use `latest` for "what is it now", `get` with a range for history.
4. **Report the period alongside the value.** These series are revised and published on
   a lag; a number without its period is not a usable answer.

For a broad "how is Peru's economy doing" question, the macro snapshot answers it in one
call — exchange rate, policy rate, reserves, copper, BVL, plus monthly liquidity and
credit. Reach for individual series only when the snapshot doesn't cover what was asked.

## Things that will silently give you wrong answers

These are the failure modes worth internalizing — the API returns *plausible-looking*
output in each case rather than an error.

**Values are positional, not keyed.** A response gives you `series` (metadata) and
`data[].values` (numbers). `series[i]` describes `data[period].values[i]`. They are
matched by *index*, never by code. The API also reorders series when you combine codes
from different categories, so never assume `values[0]` belongs to the first code you
typed — read it off the `series` array that came back.

**All codes in one call must share a frequency.** Mixing a daily and a monthly code does
not error; the API just drops the ones that don't match the first series' frequency and
returns the rest. Split into separate calls per frequency. Maximum 10 codes per call.

**The period format depends on the frequency**, and using the wrong one returns empty
data rather than an error:

| Frequency | You send | Example | Comes back as |
|-----------|----------|---------|---------------|
| Daily | `DD-MM-YYYY` | `01-06-2025` | `01.Jun.25` |
| Monthly | `YYYY-M` | `2024-1` | `Ene.2024` |
| Quarterly | `YYYY-Q` | `2024-3` | `T3.2024` |
| Annual | `YYYY` | `2024` | `2024` |

Do **not** zero-pad month numbers — `2024-1`, never `2024-01`. Daily dates use hyphens
and are day-first. Month labels come back as Spanish abbreviations (Ene, Abr, Ago, Dic).

**Missing values are real.** `n.d.` in the raw API (surfaced as `null`/`—`) means the
figure wasn't published for that period — a market holiday, or a not-yet-released month.
Skip those points; don't read them as zero, and don't treat the last row as current if
its value is null.

**Omitting the date range does not mean "all history."** It returns the most recent
window (~90 points for daily series). To get history, pass an explicit range — and get
the range from `describe` first so you don't request periods that predate the series.

## Reading the numbers correctly

Each series carries a `decimals` field — the precision the BCRP actually publishes it
at. Round to it when reporting; extra digits are noise, not accuracy.

Units are not interchangeable and the series name states them. Watch especially for:
levels vs. percent-change variants of the same indicator (`PN00496MM` is credit *in
millions of soles*, `PN00500MM` is its *12-month % change*); copper quoted in US cents
per pound, not dollars; and reserves in millions of USD. Picking the wrong variant is
the most common way to produce a confidently wrong chart.

When the user asks for "the exchange rate", the interbank buy rate `PD04637PD` is the
standard reference; `PD04638PD` is the sell rate. Quote which one you used.

## Series codes worth knowing

The most commonly requested indicators:

| Code | Indicator | Freq |
|------|-----------|------|
| `PD04637PD` | Exchange rate USD/PEN, interbank buy | daily |
| `PD12301MD` | BCRP policy rate (tasa de referencia) | daily |
| `PD04650MD` | Net international reserves (RIN) | daily |
| `PD04701XD` | Copper price | daily |
| `PD38026MD` | Lima stock exchange index (BVL) | daily |
| `PN00196MM` | Total liquidity (M2) | monthly |
| `PN00496MM` | Private-sector credit | monthly |
| `PN00500MM` | Credit, 12-month % change | monthly |
| `PN03503MQ` | Nominal GDP % change (PBI) | quarterly |

`references/series-codes.md` has the full curated catalog by category with units and
descriptions — read it when the indicator you need isn't in the table above, or when you
want to confirm a unit before charting. Searching the catalog at runtime works too and
stays current with the installed version.

## Analysis conventions

Peruvian macro questions usually have a standard framing worth following:

- **Inflation / monetary policy**: pair the policy rate with liquidity (M2) and credit
  growth. The BCRP targets inflation in a 1–3% range, so read the rate path against it.
- **Exchange rate**: pair USD/PEN with international reserves — BCRP intervenes to smooth
  volatility, so reserve movements explain rate movements.
- **Growth**: GDP is quarterly while credit and liquidity are monthly; when combining
  them, aggregate the monthly series to quarters rather than comparing mismatched points.

Cite BCRPData as the source and state the as-of period. If a request needs a series
outside the catalog, say so and point to the BCRP series browser rather than substituting
a number from memory — stale or invented macro figures are worse than a gap.

## Reference files

- `references/series-codes.md` — full curated catalog: codes, names, units, frequencies,
  by category.
- `references/api.md` — raw HTTP API (URL structure, response schema, POST form) for when
  neither the MCP server nor the CLI is available.
