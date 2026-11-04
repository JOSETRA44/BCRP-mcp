<img width="1600" height="500" alt="BCRP MCP" src="https://github.com/user-attachments/assets/79323612-ebec-49ea-91d5-321b5950bbbc" />

[![PyPI](https://img.shields.io/pypi/v/bcrp-mcp?logo=pypi&logoColor=white)](https://pypi.org/project/bcrp-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/bcrp-mcp?logo=python&logoColor=white)](https://pypi.org/project/bcrp-mcp/)
[![Publish](https://github.com/JOSETRA44/BCRP-mcp/actions/workflows/publish.yml/badge.svg)](https://github.com/JOSETRA44/BCRP-mcp/actions/workflows/publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# BCRP MCP

<!-- mcp-name: io.github.JOSETRA44/bcrp-mcp -->

Servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) para
consultar **BCRPData**, la base oficial de estadísticas económicas del
[Banco Central de Reserva del Perú (BCRP)](https://www.bcrp.gob.pe/).

Permite a clientes MCP y agentes de IA consultar tipos de cambio, tasas de
interés, reservas internacionales, liquidez, crédito, commodities, bolsa y PBI.
La API del BCRP es pública: **no se necesita API key ni registro**.

## Instalación rápida

Se requiere Python 3.11 o posterior.

### Con `uvx` (recomendado para clientes MCP)

```bash
uvx bcrp-mcp
```

### Con `pip`

```bash
python -m pip install bcrp-mcp
bcrp-mcp
```

La instalación también proporciona el CLI `bcrp`:

```bash
bcrp --help
bcrp catalog search "tipo de cambio"
bcrp series latest PD04637PD --n 5
```

### Desde el código fuente

```bash
git clone https://github.com/JOSETRA44/BCRP-mcp.git
cd BCRP-mcp
uv sync
uv run bcrp-mcp
```

## Configuración en clientes MCP

El servidor usa transporte stdio. Con `uvx`, la configuración es la misma en
Claude Desktop, Claude Code, Cursor y otros clientes compatibles:

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

En VS Code + GitHub Copilot (`.vscode/mcp.json`):

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

## Herramientas MCP

| Herramienta | Uso |
|---|---|
| `bcrp_get_series` | Obtiene 1–10 series con un rango opcional; deben compartir frecuencia. |
| `bcrp_get_latest` | Obtiene los últimos valores de 1–10 series. |
| `bcrp_get_series_long` | Exporta hasta 50 series en una tabla larga, incluso con frecuencias mixtas. |
| `bcrp_describe_series` | Consulta nombre, frecuencia y rango disponible de una serie. |
| `bcrp_search_catalog` | Busca códigos en el catálogo curado de indicadores. |
| `bcrp_list_catalog_categories` | Lista las categorías disponibles. |
| `bcrp_get_macro_snapshot` | Devuelve un resumen de indicadores macroeconómicos clave. |

Ejemplos de preguntas:

```text
¿Cuál es el tipo de cambio actual en Perú?
Compara la tasa de referencia y las reservas internacionales desde 2020.
Obtén un snapshot de los principales indicadores de la economía peruana.
```

## CLI

El comando `bcrp` usa la misma lógica que el servidor MCP y admite salida para
terminal o automatización:

```bash
bcrp series describe PD04637PD
bcrp series latest PD04637PD PD12301MD --n 5
bcrp series get PN00196MM --start 2020-1 --end 2024-12
bcrp catalog categories
bcrp macro snapshot
```

Opciones útiles:

```bash
bcrp series latest PD04637PD --n 5 --json
bcrp series latest PD04637PD --n 5 --ascii --no-color
```

Los formatos de período dependen de la frecuencia: diario
`DD-MM-YYYY`, mensual `YYYY-M`, trimestral `YYYY-Q` y anual `YYYY`.
Las series de una misma consulta deben tener la misma frecuencia, salvo
`bcrp_get_series_long`.

## Configuración opcional

Todos los valores tienen valores predeterminados razonables y pueden definirse
con variables de entorno o un archivo `.env`:

| Variable | Predeterminado | Descripción |
|---|---:|---|
| `BCRP_CACHE_TTL` | `300` | Duración de la caché en segundos; `0` la desactiva. |
| `BCRP_TIMEOUT` | `30` | Timeout HTTP en segundos. |
| `BCRP_MAX_RETRIES` | `3` | Reintentos ante errores transitorios. |
| `BCRP_LANGUAGE` | `esp` | Idioma de nombres: `esp` o `ing`. |
| `LOG_LEVEL` | `INFO` | Nivel de logging. |

No se configura ninguna credencial: BCRPData es de acceso abierto.

## Desarrollo

```bash
uv sync
uv run pytest -q
uv run python -m build
```

El proyecto usa `src/` layout, Hatchling para construir el paquete y publica
dos entry points: `bcrp-mcp` (servidor) y `bcrp` (CLI).

## Publicación

Las versiones se publican mediante GitHub Actions al crear un release de
GitHub. El workflow `.github/workflows/publish.yml` ejecuta las pruebas,
construye los artefactos y publica en PyPI usando Trusted Publishing (OIDC);
no requiere un token de PyPI almacenado en secretos.

## Datos y licencia

Los datos provienen de [BCRPData](https://estadisticas.bcrp.gob.pe/estadisticas/series/).
Consulte sus [condiciones de uso](https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/condicionesUso).

MIT — consulte [LICENSE](LICENSE).

## Documentación del proyecto

- [CHANGELOG.md](CHANGELOG.md): historial de cambios.
- [CONTRIBUTING.md](CONTRIBUTING.md): guía para contribuir.
- [SECURITY.md](SECURITY.md): reporte de vulnerabilidades.
- [server.json](server.json): metadatos para el registro MCP.
