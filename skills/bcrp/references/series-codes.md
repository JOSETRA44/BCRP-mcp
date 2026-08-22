<!-- GENERATED FILE — do not edit by hand.
     Regenerate with: uv run python scripts/gen_skill_refs.py -->

# BCRP series catalog

Curated codes verified active against the live BCRPData API.
All series in a single request must share the same frequency (max 10 codes).

## Exchange Rates Daily

`exchange_rates_daily` · daily · period format `DD-MM-YYYY` · 4 series

| Code | Name | Unit |
|------|------|------|
| `PD04637PD` | TC Interbancario Compra (S/ por US$) | S/ por US$ |
| `PD04638PD` | TC Interbancario Venta (S/ por US$) | S/ por US$ |
| `PD04700XD` | Euro / Dólar | EUR per USD |
| `PD04647PD` | TC Euro (S/ por Euro) | S/ por Euro |

- **`PD04637PD`** — Tipo de cambio interbancario - precio compra del dólar, en soles
- **`PD04638PD`** — Tipo de cambio interbancario - precio venta del dólar, en soles
- **`PD04700XD`** — Tipo de cambio Euro por Dólar estadounidense
- **`PD04647PD`** — Tipo de cambio del Euro en soles peruanos

## Interest Rates Daily

`interest_rates_daily` · daily · period format `DD-MM-YYYY` · 3 series

| Code | Name | Unit |
|------|------|------|
| `PD12301MD` | Tasa de Referencia BCRP (%) | % anual |
| `PD04692MD` | Tasa Interbancaria, S/ (%) | % anual |
| `PD04693MD` | Tasa Interbancaria, US$ (%) | % anual |

- **`PD12301MD`** — Tasa de referencia de la política monetaria del BCRP
- **`PD04692MD`** — Tasa de interés interbancaria en moneda nacional
- **`PD04693MD`** — Tasa de interés interbancaria en dólares

## International Reserves Daily

`international_reserves_daily` · daily · period format `DD-MM-YYYY` · 2 series

| Code | Name | Unit |
|------|------|------|
| `PD04650MD` | Reservas Internacionales Netas (millones US$) | Millones US$ |
| `PD04649MD` | Posición de Cambio del BCRP (millones US$) | Millones US$ |

- **`PD04650MD`** — Reservas internacionales netas del Perú en millones de dólares
- **`PD04649MD`** — Posición de cambio del Banco Central

## Financial Markets Daily

`financial_markets_daily` · daily · period format `DD-MM-YYYY` · 2 series

| Code | Name | Unit |
|------|------|------|
| `PD38026MD` | Índice General Bursátil BVL | Índice |
| `PD04721XD` | Índice Dow Jones (DJIA) | Índice |

- **`PD38026MD`** — Índice General de la Bolsa de Valores de Lima
- **`PD04721XD`** — Índice bursátil Dow Jones Industrial Average de Estados Unidos

## Commodities Daily

`commodities_daily` · daily · period format `DD-MM-YYYY` · 4 series

| Code | Name | Unit |
|------|------|------|
| `PD04701XD` | Precio del Cobre (cUS$ por libra) | Centavos US$ por libra |
| `PD04705XD` | Precio del Petróleo Crudo WTI (US$ por barril) | US$ por barril |
| `PD04706XD` | Precio del Oro (US$ por onza troy) | US$ por onza troy |
| `PD04703XD` | Precio del Zinc (US$ por TM) | US$ por tonelada métrica |

- **`PD04701XD`** — Precio del cobre en la Bolsa de Metales de Londres
- **`PD04705XD`** — Precio del petróleo crudo West Texas Intermediate
- **`PD04706XD`** — Precio del oro en mercados internacionales
- **`PD04703XD`** — Precio del zinc en la Bolsa de Metales de Londres

## Monetary Accounts Monthly

`monetary_accounts_monthly` · monthly · period format `YYYY-M (e.g. 2024-1 = January)` · 4 series

| Code | Name | Unit |
|------|------|------|
| `PN00001MM` | Activos Totales - Cuentas Monetarias | Millones S/ |
| `PN00003MM` | Activos Externos Netos | Millones S/ |
| `PN00010MM` | Activos Internos Netos | Millones S/ |
| `PN00050MM` | Obligaciones BCRP | Millones S/ |

- **`PN00001MM`** — Activos totales de las sociedades creadoras de depósito
- **`PN00003MM`** — Activos externos netos de las sociedades creadoras de depósito
- **`PN00010MM`** — Activos internos netos de las sociedades creadoras de depósito
- **`PN00050MM`** — Obligaciones del Banco Central de Reserva del Perú

## Liquidity Monthly

`liquidity_monthly` · monthly · period format `YYYY-M` · 7 series

| Code | Name | Unit |
|------|------|------|
| `PN00178MM` | Circulante (Millones S/) | Millones S/ |
| `PN00190MM` | Liquidez en Soles (Millones S/) | Millones S/ |
| `PN00196MM` | Liquidez Total (Millones S/) | Millones S/ |
| `PN00180MM` | Liquidez var% 12 meses | % anual |
| `PN00185MM` | Liquidez var% mensual | % mensual |
| `PN00100MM` | Liquidez Sistema Bancario (fin de periodo) | Millones S/ |
| `PN00200MM` | Liquidez Sistema Financiero var% mensual | % mensual |

- **`PN00178MM`** — Billetes y monedas en circulación — componente de M1
- **`PN00190MM`** — Liquidez de las sociedades creadoras de depósito en moneda nacional
- **`PN00196MM`** — Liquidez total (M2) de las sociedades creadoras de depósito
- **`PN00180MM`** — Variación porcentual de la liquidez en 12 meses
- **`PN00185MM`** — Variación porcentual mensual de la liquidez
- **`PN00100MM`** — Liquidez total del sistema bancario al fin del período
- **`PN00200MM`** — Variación mensual de la liquidez del sistema financiero

## Credit Monthly

`credit_monthly` · monthly · period format `YYYY-M` · 4 series

| Code | Name | Unit |
|------|------|------|
| `PN00496MM` | Crédito Sector Privado (Millones S/) | Millones S/ |
| `PN00500MM` | Crédito Sector Privado var% 12 meses | % anual |
| `PN00505MM` | Crédito Sector Privado en MN (Millones S/) | Millones S/ |
| `PN00550MM` | Crédito por Tipo de Crédito (Millones S/) | Millones S/ |

- **`PN00496MM`** — Crédito de las sociedades creadoras de depósito al sector privado
- **`PN00500MM`** — Variación porcentual anual del crédito al sector privado
- **`PN00505MM`** — Crédito al sector privado en moneda nacional
- **`PN00550MM`** — Crédito al sector privado desagregado por tipo

## Gdp Quarterly

`gdp_quarterly` · quarterly · period format `YYYY-Q (e.g. 2024-1 = Q1)` · 5 series

| Code | Name | Unit |
|------|------|------|
| `PN03503MQ` | PBI Nominal var% trimestral | % trimestral |
| `PN03501MQ` | Liquidez MN var% trimestral | % trimestral |
| `PN03502MQ` | Emisión Primaria var% trimestral | % trimestral |
| `PN03504MQ` | Multiplicador Monetario var% trimestral | % trimestral |
| `PN03505MQ` | Velocidad del Dinero var% trimestral | % trimestral |

- **`PN03503MQ`** — Variación porcentual del PBI nominal trimestral
- **`PN03501MQ`** — Variación porcentual de la liquidez en moneda nacional
- **`PN03502MQ`** — Variación porcentual de la emisión primaria
- **`PN03504MQ`** — Variación porcentual del multiplicador monetario
- **`PN03505MQ`** — Variación porcentual de la velocidad del dinero

---

## Beyond this catalog

This covers the most commonly used series. The full BCRPData database holds
8,000+ monthly, 2,700+ quarterly and 800+ daily series. Browse them at
<https://estadisticas.bcrp.gob.pe/estadisticas/series/>, then verify any code
you find with `bcrp_describe_series` / `bcrp series describe` before relying on it.
