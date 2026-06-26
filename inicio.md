API para Desarrolladores
La Base de Datos de Estadísticas del BCRP (BCRPData) proporciona interfaces API para consultar series estadísticas desde otras aplicaciones Web. Las API pueden generar resultados en diversos formatos de salida como HTML, Gráficos en FLASH, XLS, XML, JSON, JSONP, TXT y CSV.

Consulte instrucciones en la Guía de Uso de API para Desarrolladores . Además, se recomienda revisar información sobre la actualización de contenidos en Acerca de BCRPData, así como las Condiciones de Uso de la información.

Fuente de la información
La información consultada desde las API se encuentra registrada en BCRPData, con ello se asegura la obtención de series estadísticas actualizadas. No se requiere ingresar previamente a BCRPData para consultar series, solo es necesario utilizar correctamente los parámetros y contar con acceso a Internet.

Uso de las API
Se pueden realizar consultas directas a BCRPData a través de los métodos de envío de datos GET y POST.

Método GET
La estructura de la consulta mediante este método es la siguiente:

https://estadisticas.bcrp.gob.pe/estadisticas/series/api/[códigos de series]/[formato de salida]/[periodo inicial]/[periodo final]/[idioma]
Código de series
Es el único parámetro obligatorio, se requiere al menos un código de serie y como máximo diez. Las series deben corresponder a una misma frecuencia y los códigos deben estar separados por un guion.

Ejemplos:
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01270PM
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico/2010-1/2016-9/esp
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xml
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM-PN01290PM-PN01291PM

Nota: Si se colocan series de diversas frecuencias, se considerará la frecuencia de la primera serie y sólo se mostrarán las series que correspondan a esa frecuencia.
Formatos de salida
Se tiene los siguientes formatos de salida:

HTML: Formato de salida por defecto, esta opción muestra una tabla en formato HTML.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/html
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM

Gráfico: Esta opción mostrará un gráfico en formato flash.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/grafico
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico

XLS: Esta opción generará un archivo en formato XLS.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/xls
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xls/2013-1/2016-9

XML: Esta opción mostrará un archivo en formato XML.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/xml
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/xml/2013-1/2016-9

JSON y JSONP: Estas opciones mostrarán salidas en formato JSON (sin paréntesis) y JSONP (con paréntesis).
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/json
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/json/2013-1/2016-9
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/jsonp
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/jsonp/2013-1/2016-9

TXT: Esta opción generará un archivo en formato TXT.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/txt
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/txt/2013-1/2016-9

CSV: Esta opción imprimirá en pantalla un archivo con valores separadores por coma.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/csv
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/csv/2013-1/2016-9
Periodo inicial y periodo final
Estos parámetros representan el rango de la consulta a través del método GET. Si no se colocan los periodos, por defecto se mostrarán los datos más actuales de las series. En el caso que se coloque un solo periodo, se asumirá como una consulta de una fecha.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/grafico/2010-1/2016-9/esp
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/csv/2016-9
Idioma
Los resultados se pueden generar en idioma español (esp) o inglés (ing). Por defecto se mostrará en idioma español.
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/csv/2010-1/2016-9
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM-PN01289PM/grafico/2010-1/2016-9/ing
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01288PM/json/2010-1/2016-9/ing

Método POST
En las consultas mediante el método POST se requiere enviar las siguientes variables equivalentes al método GET:

"series": Similar a [códigos de series]. Sólo esta variable es obligatoria.

"formato": Similar a [formato de salida].

"fechaini": Equivalente a [periodo inicial].

"fechafin": Equivalente a [periodo final].

"idioma": Similar a [idioma].

Ejemplo 1:
series = 'PN01288PM-PN01289PM'
formato = 'xml'
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/

Ejemplo 2:
series = 'PN01288PM-PN01289PM-PN01290PM-PN01291PM'
formato = 'jsonp'
fechaini = '2010-1'
fechafin = '2016-9'
idioma = 'ing'
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/