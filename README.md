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

## Instalación inicial

Se requiere Python 3.11 o posterior. La opción recomendada es
[`uv`](https://docs.astral.sh/uv/), un gestor rápido de Python que crea los
entornos y administra las dependencias automáticamente.

### 1. Instalar `uv` y agregarlo al `PATH`

#### Windows — PowerShell

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

El instalador agrega `uv` a la ruta de usuario, normalmente
`%USERPROFILE%\.local\bin`. Cierra y vuelve a abrir PowerShell, y verifica la
instalación:

```powershell
uv --version
Get-Command uv
```

Si `uv` no se encuentra en una terminal ya abierta, agrega la ruta solo para
la sesión actual:

```powershell
$env:Path = "$HOME\.local\bin;$env:Path"
uv --version
```

#### macOS y Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

Si tu shell no reconoce `uv`, agrega la ruta al `PATH` de forma permanente:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Para Zsh, usa `~/.zshrc` en lugar de `~/.bashrc`. En macOS y Linux, el
instalador normalmente configura esta ruta automáticamente.

### 2. Instalar BCRP MCP

#### Ejecución directa con `uvx` — recomendada para clientes MCP

`uvx` descarga y ejecuta la versión publicada sin modificar el proyecto local:

```bash
uvx bcrp-mcp
```

Para comprobar que el paquete está disponible en PyPI:

```bash
uvx bcrp-mcp --help
```

#### Instalación persistente como herramienta de `uv`

```bash
uv tool install bcrp-mcp
uv tool update-shell
bcrp-mcp --help
```

`uv tool update-shell` agrega el directorio de herramientas de `uv` al
`PATH`. Reinicia la terminal si el comando todavía no aparece.

#### Con `pip`

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

### 3. Configuración inicial

No se requiere API key, cuenta ni archivo de credenciales. La configuración
predeterminada funciona directamente contra la API pública de BCRPData.

Para personalizar el comportamiento, copia el archivo de ejemplo y edita los
valores:

```bash
cp .env.example .env       # macOS/Linux
Copy-Item .env.example .env # Windows PowerShell
```

Las variables disponibles son `BCRP_CACHE_TTL`, `BCRP_TIMEOUT`,
`BCRP_MAX_RETRIES`, `BCRP_LANGUAGE` y `LOG_LEVEL`. Consulta la sección
[Configuración opcional](#configuración-opcional).

Comprueba la instalación y la conexión al catálogo local:

```bash
bcrp --version
bcrp catalog categories
bcrp catalog search "tipo de cambio"
bcrp series latest PD04637PD --n 5
```

### 4. Configurar el cliente MCP

El servidor usa transporte `stdio`. En Claude Desktop, Claude Code, Cursor y
otros clientes compatibles, añade esta configuración:

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

Con `uv tool install`, también puedes usar el ejecutable directamente:

```json
{
  "mcpServers": {
    "bcrp": {
      "command": "bcrp-mcp",
      "args": []
    }
  }
}
```

En VS Code + GitHub Copilot, guarda esta variante en `.vscode/mcp.json`:

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

Reinicia el cliente MCP después de guardar la configuración y verifica que
aparezca el servidor `bcrp` y sus herramientas.

### Instalación desde el código fuente

```bash
git clone https://github.com/JOSETRA44/BCRP-mcp.git
cd BCRP-mcp
uv sync
uv run bcrp-mcp
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
