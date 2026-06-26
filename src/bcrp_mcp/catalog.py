"""Curated catalog of important BCRP series codes.

All codes verified active against the live BCRPData API (June 2026).
"""

from typing import Any

CATALOG: dict[str, list[dict[str, str]]] = {
    "exchange_rates_daily": [
        {
            "code": "PD04637PD",
            "name": "TC Interbancario Compra (S/ por US$)",
            "description": "Tipo de cambio interbancario - precio compra del dólar, en soles",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "S/ por US$",
        },
        {
            "code": "PD04638PD",
            "name": "TC Interbancario Venta (S/ por US$)",
            "description": "Tipo de cambio interbancario - precio venta del dólar, en soles",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "S/ por US$",
        },
        {
            "code": "PD04700XD",
            "name": "Euro / Dólar",
            "description": "Tipo de cambio Euro por Dólar estadounidense",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "EUR per USD",
        },
        {
            "code": "PD04647PD",
            "name": "TC Euro (S/ por Euro)",
            "description": "Tipo de cambio del Euro en soles peruanos",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "S/ por Euro",
        },
    ],
    "interest_rates_daily": [
        {
            "code": "PD12301MD",
            "name": "Tasa de Referencia BCRP (%)",
            "description": "Tasa de referencia de la política monetaria del BCRP",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "% anual",
        },
        {
            "code": "PD04692MD",
            "name": "Tasa Interbancaria, S/ (%)",
            "description": "Tasa de interés interbancaria en moneda nacional",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "% anual",
        },
        {
            "code": "PD04693MD",
            "name": "Tasa Interbancaria, US$ (%)",
            "description": "Tasa de interés interbancaria en dólares",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "% anual",
        },
    ],
    "international_reserves_daily": [
        {
            "code": "PD04650MD",
            "name": "Reservas Internacionales Netas (millones US$)",
            "description": "Reservas internacionales netas del Perú en millones de dólares",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "Millones US$",
        },
        {
            "code": "PD04649MD",
            "name": "Posición de Cambio del BCRP (millones US$)",
            "description": "Posición de cambio del Banco Central",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "Millones US$",
        },
    ],
    "financial_markets_daily": [
        {
            "code": "PD38026MD",
            "name": "Índice General Bursátil BVL",
            "description": "Índice General de la Bolsa de Valores de Lima",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "Índice",
        },
        {
            "code": "PD04721XD",
            "name": "Índice Dow Jones (DJIA)",
            "description": "Índice bursátil Dow Jones Industrial Average de Estados Unidos",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "Índice",
        },
    ],
    "commodities_daily": [
        {
            "code": "PD04701XD",
            "name": "Precio del Cobre (cUS$ por libra)",
            "description": "Precio del cobre en la Bolsa de Metales de Londres",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "Centavos US$ por libra",
        },
        {
            "code": "PD04705XD",
            "name": "Precio del Petróleo Crudo WTI (US$ por barril)",
            "description": "Precio del petróleo crudo West Texas Intermediate",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "US$ por barril",
        },
        {
            "code": "PD04706XD",
            "name": "Precio del Oro (US$ por onza troy)",
            "description": "Precio del oro en mercados internacionales",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "US$ por onza troy",
        },
        {
            "code": "PD04703XD",
            "name": "Precio del Zinc (US$ por TM)",
            "description": "Precio del zinc en la Bolsa de Metales de Londres",
            "frequency": "daily",
            "period_format": "DD-MM-YYYY",
            "unit": "US$ por tonelada métrica",
        },
    ],
    "monetary_accounts_monthly": [
        {
            "code": "PN00001MM",
            "name": "Activos Totales - Cuentas Monetarias",
            "description": "Activos totales de las sociedades creadoras de depósito",
            "frequency": "monthly",
            "period_format": "YYYY-M (e.g. 2024-1 = January)",
            "unit": "Millones S/",
        },
        {
            "code": "PN00003MM",
            "name": "Activos Externos Netos",
            "description": "Activos externos netos de las sociedades creadoras de depósito",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00010MM",
            "name": "Activos Internos Netos",
            "description": "Activos internos netos de las sociedades creadoras de depósito",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00050MM",
            "name": "Obligaciones BCRP",
            "description": "Obligaciones del Banco Central de Reserva del Perú",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
    ],
    "liquidity_monthly": [
        {
            "code": "PN00178MM",
            "name": "Circulante (Millones S/)",
            "description": "Billetes y monedas en circulación — componente de M1",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00190MM",
            "name": "Liquidez en Soles (Millones S/)",
            "description": "Liquidez de las sociedades creadoras de depósito en moneda nacional",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00196MM",
            "name": "Liquidez Total (Millones S/)",
            "description": "Liquidez total (M2) de las sociedades creadoras de depósito",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00180MM",
            "name": "Liquidez var% 12 meses",
            "description": "Variación porcentual de la liquidez en 12 meses",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "% anual",
        },
        {
            "code": "PN00185MM",
            "name": "Liquidez var% mensual",
            "description": "Variación porcentual mensual de la liquidez",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "% mensual",
        },
        {
            "code": "PN00100MM",
            "name": "Liquidez Sistema Bancario (fin de periodo)",
            "description": "Liquidez total del sistema bancario al fin del período",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00200MM",
            "name": "Liquidez Sistema Financiero var% mensual",
            "description": "Variación mensual de la liquidez del sistema financiero",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "% mensual",
        },
    ],
    "credit_monthly": [
        {
            "code": "PN00496MM",
            "name": "Crédito Sector Privado (Millones S/)",
            "description": "Crédito de las sociedades creadoras de depósito al sector privado",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00500MM",
            "name": "Crédito Sector Privado var% 12 meses",
            "description": "Variación porcentual anual del crédito al sector privado",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "% anual",
        },
        {
            "code": "PN00505MM",
            "name": "Crédito Sector Privado en MN (Millones S/)",
            "description": "Crédito al sector privado en moneda nacional",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
        {
            "code": "PN00550MM",
            "name": "Crédito por Tipo de Crédito (Millones S/)",
            "description": "Crédito al sector privado desagregado por tipo",
            "frequency": "monthly",
            "period_format": "YYYY-M",
            "unit": "Millones S/",
        },
    ],
    "gdp_quarterly": [
        {
            "code": "PN03503MQ",
            "name": "PBI Nominal var% trimestral",
            "description": "Variación porcentual del PBI nominal trimestral",
            "frequency": "quarterly",
            "period_format": "YYYY-Q (e.g. 2024-1 = Q1)",
            "unit": "% trimestral",
        },
        {
            "code": "PN03501MQ",
            "name": "Liquidez MN var% trimestral",
            "description": "Variación porcentual de la liquidez en moneda nacional",
            "frequency": "quarterly",
            "period_format": "YYYY-Q",
            "unit": "% trimestral",
        },
        {
            "code": "PN03502MQ",
            "name": "Emisión Primaria var% trimestral",
            "description": "Variación porcentual de la emisión primaria",
            "frequency": "quarterly",
            "period_format": "YYYY-Q",
            "unit": "% trimestral",
        },
        {
            "code": "PN03504MQ",
            "name": "Multiplicador Monetario var% trimestral",
            "description": "Variación porcentual del multiplicador monetario",
            "frequency": "quarterly",
            "period_format": "YYYY-Q",
            "unit": "% trimestral",
        },
        {
            "code": "PN03505MQ",
            "name": "Velocidad del Dinero var% trimestral",
            "description": "Variación porcentual de la velocidad del dinero",
            "frequency": "quarterly",
            "period_format": "YYYY-Q",
            "unit": "% trimestral",
        },
    ],
}

# Key macroeconomic snapshot series (confirmed active)
MACRO_SNAPSHOT_SERIES: dict[str, list[str]] = {
    "daily": [
        "PD04637PD",  # Exchange rate
        "PD12301MD",  # Policy rate
        "PD04650MD",  # International reserves
        "PD04701XD",  # Copper price
        "PD38026MD",  # BVL index
    ],
    "monthly": [
        "PN00196MM",  # Total liquidity
        "PN00496MM",  # Private sector credit
        "PN00178MM",  # Currency in circulation
        "PN00500MM",  # Credit growth 12m
    ],
}


def search_catalog(
    query: str,
    category: str | None = None,
    frequency: str | None = None,
) -> list[dict[str, Any]]:
    """Search the catalog by keyword, optional category, and optional frequency."""
    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for cat_key, series_list in CATALOG.items():
        if category and category.lower() not in cat_key.lower():
            continue

        for s in series_list:
            if frequency and frequency.lower() not in s.get("frequency", "").lower():
                continue

            searchable = (
                s.get("name", "") + " " +
                s.get("description", "") + " " +
                s.get("code", "") + " " +
                cat_key
            ).lower()

            if query_lower in searchable or any(
                word in searchable for word in query_lower.split()
            ):
                results.append({**s, "category": cat_key})

    return results


def list_categories() -> list[dict[str, str]]:
    """Return all available catalog categories."""
    return [
        {
            "id": key,
            "series_count": str(len(val)),
            "frequency": val[0].get("frequency", "unknown") if val else "unknown",
        }
        for key, val in CATALOG.items()
    ]
