````markdown
# Banco Central de Reserva del Perú

## Base de Datos de Estadísticas del BCRP (BCRPData)

### API para Desarrolladores

#### Guía de Uso

Jr. Santa Rosa 441-445, Lima-1, Perú

---

# Guía de Uso de API para Desarrolladores

La Base de Datos de Estadísticas del BCRP (BCRPData) proporciona la herramienta API para Desarrolladores como una de las facilidades que se brindan para la obtención y uso de las series macroeconómicas.

Las API para Desarrolladores contienen interfaces para la obtención de series estadísticas que puedan utilizarse desde otras aplicaciones web.

Las consultas a través de API utilizan los métodos de envío de datos desde HTML denominados `GET` y `POST`.

Se pueden obtener resultados en diversos formatos de salida como:

- HTML
- Gráficos en FLASH
- XLS
- XML
- JSON
- JSONP
- TXT
- CSV

Desde BCRPData también se puede acceder a ejemplos de uso.

---

# Consultas directas mediante API

Las consultas directas a las series de BCRPData a través de las API utilizan los métodos de envío de datos `GET` y `POST`.

## Método GET

La estructura completa de la consulta mediante el método `GET` es la siguiente:

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/[códigos de series]/[formato de salida]/[periodo inicial]/[periodo final]/[idioma]
````

### Uso del código de las series estadísticas

Es la única parte obligatoria de la estructura. Se requiere al menos un código de serie y como máximo diez.

Las series deben corresponder a una misma frecuencia y los códigos deben estar separados por un guion.

#### Ejemplos

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01270PM
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico/2016-1/2022-5/esp
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xml
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM-PN01290PM-PN01291PM
```

> **Nota:** Si se colocan series de diversas frecuencias, se considerará la frecuencia de la primera serie y solo se mostrarán las series que correspondan a esa frecuencia. El resto de las series serán descartadas.

---

## Uso de los formatos de salida

Se tienen los siguientes formatos de salida:

### HTML

Es el formato de salida por defecto. Esta opción muestra una tabla en formato HTML.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/html
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM
```

### Gráfico

Esta opción mostrará un gráfico en formato Flash.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/grafico
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico
```

### XLS

Esta opción generará un archivo en formato XLS.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/xls
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xls/2016-1/2022-5
```

### XML

Esta opción mostrará un archivo en formato XML.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/xml
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xml/2016-1/2022-5
```

### JSON y JSONP

Estas opciones mostrarán salidas en formato JSON, sin paréntesis, y JSONP, con paréntesis.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/json
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/json/2016-1/2022-5
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/jsonp
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/jsonp/2016-1/2022-5
```

### TXT

Esta opción generará un archivo en formato TXT.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/txt
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/txt/2016-1/2022-5
```

### CSV

Esta opción imprimirá en pantalla un archivo con valores separados por coma.

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/csv
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/csv/2016-1/2022-5
```

---

## Uso del periodo inicial y periodo final

Estos valores representan el rango de la consulta a través del método `GET`.

Si no se colocan los periodos, por defecto se mostrarán los datos más actuales de las series.

En el caso de que se coloque un solo periodo, se asumirá como una consulta de series de una fecha.

### Ejemplos

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/grafico/2016-1/2022-5/esp
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/csv/2022-5
```

---

## Uso del idioma

Los resultados se pueden generar en idioma español (`esp`) o inglés (`ing`).

Por defecto, se mostrará en idioma español.

### Ejemplos

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/csv/2016-1/2022-5
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico/2016-1/2022-5/ing
```

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/json/2016-1/2022-5/ing
```

---

# Método POST

En las consultas a través del método `POST` se requiere enviar las siguientes variables, las cuales son equivalentes al método `GET`.

| Variable   | Equivalencia                                                        |
| ---------- | ------------------------------------------------------------------- |
| `series`   | Similar a `[códigos de series]`. Solo esta variable es obligatoria. |
| `formato`  | Similar a `[formato de salida]`.                                    |
| `fechaini` | Equivalente a `[periodo inicial]`.                                  |
| `fechafin` | Equivalente a `[periodo final]`.                                    |
| `idioma`   | Similar a `[idioma]`.                                               |

## Ejemplo 1

```text
series = 'P00305PRM-P00309PRM'
formato = 'xml'

https://estadisticas.bcrp.gob.pe/estadisticas/series/api/
```

## Ejemplo 2

```text
series = 'P00305PRM-P00306PRM-P00307PRM-P00308PRM'
formato = 'jsonp'
fechaini = '2016-1'
fechafin = '2022-5'
idioma = 'ing'

https://estadisticas.bcrp.gob.pe/estadisticas/series/api/
```

---

**Actualización:** 24/05/2022
**Gerencia Central de Estudios Económicos**

```

:contentReference[oaicite:0]{index=0}
```
