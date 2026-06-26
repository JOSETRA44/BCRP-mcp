from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:

    @mcp.prompt(
        name="inflation_and_monetary_analysis",
        description=(
            "Generate a structured analysis workflow for Peru's monetary policy and inflation using BCRP data. "
            "Returns ready-to-run tool calls for policy rate tracking, liquidity monitoring, "
            "credit growth, and currency in circulation trends."
        ),
    )
    def inflation_and_monetary_analysis(
        start_year: int = 2022,
        end_year: int = 2026,
    ) -> str:
        return f"""# Análisis Monetario y de Inflación — BCRP

## Contexto
Usando los datos del Banco Central de Reserva del Perú (BCRPData) para analizar
la política monetaria y el entorno inflacionario de Perú entre {start_year} y {end_year}.

---

## Paso 1 — Tasa de referencia (política monetaria)

Llama a `bcrp_get_series` con:
```json
{{
  "series_codes": ["PD12301MD"],
  "start_period": "01-01-{start_year}",
  "end_period": "31-12-{end_year}",
  "language": "esp"
}}
```

Esto muestra la evolución de la tasa de política monetaria del BCRP (%).
Identifica los ciclos de endurecimiento y relajamiento monetario.

---

## Paso 2 — Tasa interbancaria y transmisión

Llama a `bcrp_get_series` con ambas series para ver la transmisión de la política monetaria:
```json
{{
  "series_codes": ["PD12301MD", "PD04692MD"],
  "start_period": "01-01-{start_year}",
  "end_period": "31-12-{end_year}"
}}
```

Compara la tasa de referencia con la tasa interbancaria real.

---

## Paso 3 — Liquidez del sistema (M2 y circulante)

Llama a `bcrp_get_series` con:
```json
{{
  "series_codes": ["PN00196MM", "PN00178MM", "PN00180MM"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-12"
}}
```

**Series:**
- `PN00196MM` — Liquidez total (M2, millones S/)
- `PN00178MM` — Circulante (billetes y monedas)
- `PN00180MM` — Variación % 12 meses de liquidez

---

## Paso 4 — Crédito al sector privado

Llama a `bcrp_get_series` con:
```json
{{
  "series_codes": ["PN00496MM", "PN00500MM"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-12"
}}
```

**Series:**
- `PN00496MM` — Saldo de crédito (millones S/)
- `PN00500MM` — Crecimiento % anual del crédito

---

## Paso 5 — Contexto externo: tipo de cambio

Llama a `bcrp_get_latest` con:
```json
{{
  "series_codes": ["PD04637PD"],
  "n_periods": 30
}}
```

El tipo de cambio afecta la inflación importada — un sol débil presiona precios al alza.

---

## Marco de interpretación

| Indicador | Señal expansiva | Señal contractiva |
|-----------|----------------|-------------------|
| Tasa referencia | Baja o estable | Alta o subiendo |
| Liquidez M2 | Creciendo rápido | Crecimiento lento |
| Crédito privado | Expansión >5% anual | Contracción o <2% |
| Tipo de cambio | Sol fuerte (bajo TC) | Sol débil (alto TC) |

---

## Recomendaciones adicionales

- Usa `bcrp_get_macro_snapshot` para un resumen instantáneo de todos los indicadores.
- Busca series adicionales con `bcrp_search_catalog` usando términos como 'tasas activas', 'depósitos', 'emisión'.
- Consulta `bcrp://series-catalog` para el catálogo completo de series disponibles.
"""

    @mcp.prompt(
        name="exchange_rate_analysis",
        description=(
            "Generate a structured workflow to analyze Peru's exchange rate dynamics and "
            "dollarization using BCRP daily and monthly data. "
            "Covers USD/PEN rate trends, international reserves, and external shocks."
        ),
    )
    def exchange_rate_analysis(
        start_date: str = "01-01-2024",
        end_date: str = "30-06-2026",
    ) -> str:
        return f"""# Análisis del Tipo de Cambio y Dolarización — BCRP

## Período de análisis: {start_date} → {end_date}

---

## Paso 1 — Tipo de cambio interbancario (diario)

Llama a `bcrp_get_series` con:
```json
{{
  "series_codes": ["PD04637PD", "PD04638PD"],
  "start_period": "{start_date}",
  "end_period": "{end_date}"
}}
```

- `PD04637PD` — TC Compra (precio al que el banco compra USD)
- `PD04638PD` — TC Venta (precio al que el banco vende USD)

El spread entre compra y venta indica liquidez del mercado cambiario.

---

## Paso 2 — Reservas internacionales (ancla del tipo de cambio)

```json
{{
  "series_codes": ["PD04650MD", "PD04649MD"],
  "start_period": "{start_date}",
  "end_period": "{end_date}"
}}
```

- `PD04650MD` — Reservas internacionales netas (millones US$)
- `PD04649MD` — Posición de cambio del BCRP

El BCRP interviene en el mercado FX usando estas reservas para suavizar volatilidad.

---

## Paso 3 — Contexto: tasa de referencia y tipo de cambio

```json
{{
  "series_codes": ["PD12301MD", "PD04692MD"],
  "start_period": "{start_date}",
  "end_period": "{end_date}"
}}
```

Las tasas internas afectan los flujos de capital y el tipo de cambio.

---

## Paso 4 — Precios internacionales (shocks externos)

```json
{{
  "series_codes": ["PD04701XD", "PD04705XD"],
  "start_period": "{start_date}",
  "end_period": "{end_date}"
}}
```

- `PD04701XD` — Cobre (principal exportación peruana)
- `PD04705XD` — Petróleo crudo (principal importación)

Un cobre alto fortalece el sol; un petróleo alto lo debilita.

---

## Paso 5 — Dolarización del crédito

```json
{{
  "series_codes": ["PN00496MM", "PN00505MM"],
  "start_period": "2024-1"
}}
```

- `PN00496MM` — Crédito total sector privado
- `PN00505MM` — Crédito en MN (soles)

La diferencia indica el crédito en ME (dólares) — proxy de dolarización.

---

## Señales de alerta cambiaria

| Condición | Riesgo |
|-----------|--------|
| TC Venta > TC Compra + 0.05 | Volatilidad elevada |
| Reservas < 3 meses de importaciones | Vulnerabilidad externa |
| Cobre < 300 cUS$/lb + sol débil | Doble presión exportadora |
| Reservas cayendo + TC subiendo | Presión depreciación intensa |

---

## Evaluación del BVL como proxy de confianza

```json
{{
  "series_codes": ["PD38026MD"],
  "start_period": "{start_date}",
  "end_period": "{end_date}"
}}
```

La correlación entre el BVL y el tipo de cambio indica el apetito de riesgo de inversores.
"""

    @mcp.prompt(
        name="economic_growth_analysis",
        description=(
            "Generate a structured economic growth analysis workflow for Peru using BCRP quarterly and "
            "monthly data. Covers GDP growth, monetary multiplier, credit expansion, and liquidity trends."
        ),
    )
    def economic_growth_analysis(
        start_year: int = 2020,
        end_year: int = 2026,
    ) -> str:
        return f"""# Análisis del Crecimiento Económico — BCRP

## Período: {start_year} – {end_year}

---

## Paso 1 — PBI Nominal (variación trimestral)

Llama a `bcrp_get_series` con:
```json
{{
  "series_codes": ["PN03503MQ", "PN03501MQ"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-4",
  "language": "esp"
}}
```

- `PN03503MQ` — PBI Nominal variación % trimestral
- `PN03501MQ` — Liquidez MN variación % trimestral

**Formato de períodos trimestrales:** `YYYY-Q` donde Q = 1 (T1), 2 (T2), 3 (T3), 4 (T4)

---

## Paso 2 — Multiplicador monetario y velocidad del dinero

```json
{{
  "series_codes": ["PN03504MQ", "PN03505MQ", "PN03502MQ"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-4"
}}
```

- `PN03504MQ` — Multiplicador monetario var% trimestral
- `PN03505MQ` — Velocidad del dinero var% trimestral
- `PN03502MQ` — Emisión primaria var% trimestral

El multiplicador monetario mide cuánto crédito genera cada sol de base monetaria.

---

## Paso 3 — Expansión del crédito privado (motor de crecimiento)

```json
{{
  "series_codes": ["PN00496MM", "PN00500MM", "PN00505MM"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-12"
}}
```

El crédito privado lidera el ciclo económico — típicamente cae 2-3 trimestres antes que el PBI.

---

## Paso 4 — Base monetaria y liquidez

```json
{{
  "series_codes": ["PN00178MM", "PN00190MM", "PN00196MM"],
  "start_period": "{start_year}-1",
  "end_period": "{end_year}-12"
}}
```

- `PN00178MM` — Circulante (M0)
- `PN00190MM` — Liquidez en soles
- `PN00196MM` — Liquidez total M2

---

## Paso 5 — Condiciones externas

```json
{{
  "series_codes": ["PD04701XD", "PD04650MD"],
  "start_period": "01-01-{start_year}",
  "end_period": "31-12-{end_year}"
}}
```

- Precio del cobre → ingresos de exportaciones → crecimiento sectorial
- Reservas internacionales → capacidad de respuesta a shocks externos

---

## Marco de ciclo económico

| Fase | Crédito | Liquidez | Tasa ref | TC (sol) |
|------|---------|----------|----------|----------|
| Expansión | Creciendo >5% | Alta | Neutral/baja | Fuerte |
| Pico | Desacelerando | Alta | Subiendo | Variable |
| Contracción | Negativo o 0% | Cayendo | Alta | Débil |
| Recuperación | Empezando crecer | Estabilizando | Bajando | Recuperando |

---

## Análisis complementario

- Usa `bcrp_get_macro_snapshot` para el estado actual instantáneo.
- Consulta `bcrp://series-catalog` para explorar series adicionales por categoría.
- Para comercio exterior, busca en `bcrp_search_catalog` con 'exportaciones', 'importaciones'.
"""
