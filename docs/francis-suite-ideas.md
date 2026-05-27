# Francis Suite — Ideas y notas de posicionamiento

## Qué es

Francis Suite es un framework universal de extracción y procesamiento de datos.
Es low-code, declarativo, extensible y cloud-ready.

No está limitado al scraping web: puede trabajar con múltiples fuentes, como web, PDF, Excel, JSON, APIs, imágenes con IA y bases de datos.

## Cómo pensarlo correctamente

No es solo una herramienta que genera archivos.
Es un motor de ejecución que permite definir procesos declarativos en XML para obtener datos, transformarlos, estructurarlos y producir resultados reutilizables.

La lógica general es:

- el usuario define un workflow XML
- el parser construye un árbol interno de nodos
- el runtime ejecuta cada hand
- los resultados se guardan en boxes
- los datos estructurados se acumulan en records
- el proceso genera outputs, metadata y estado de ejecución

## Conceptos clave

### Hand

Un hand es la unidad ejecutable del framework.
Cada hand representa una acción que el motor puede ejecutar a partir de una etiqueta XML.

Ejemplos:

- llamadas HTTP
- extracción con XPath
- regex
- lectura y escritura de archivos
- creación y guardado de records
- control de flujo
- conversiones entre formatos

Los hands también permiten extender el framework e integrar tecnologías externas.
Por ejemplo, conceptualmente se podría crear un hand para usar Scrapy, Tika, OCR, IA o conectores a bases de datos.

### Box

La box es la unidad de datos del framework.
Todo lo que se quiere reutilizar después en el flujo se guarda en una box.

### Record

El record es la estructura orientada a filas, schema y metadata.
Permite acumular datos estructurados y luego exportarlos en distintos formatos.

## Qué genera

Francis Suite puede generar:

- datos estructurados en memoria
- records
- archivos de salida
- metadata privada
- trazabilidad de sesión
- estado de ejecución
- errores y métricas

Formatos soportados actualmente en record-save:

- json
- csv
- ndjson
- xml
- html
- txt
- excel
- parquet

## Qué problema resuelve

Busca unificar en una sola arquitectura cosas que en muchas empresas suelen estar separadas:

- extracción desde múltiples fuentes
- limpieza y normalización de datos
- transformación de formatos
- estructuración de resultados
- persistencia de outputs
- trazabilidad de ejecución
- extensibilidad

## Diferencia frente a herramientas conocidas

No parece una copia directa de una sola herramienta.
Se puede entender como una combinación de ideas que normalmente viven separadas.

Referencias conceptuales útiles:

- Scrapy: por la parte de extracción
- Apache Tika: por la parte de extracción multi-formato documental
- Apache NiFi: por la parte de movimiento/orquestación de flujos de datos
- Prefect / Dagster / Airflow: por la parte de ejecución de procesos y observabilidad
- n8n: por la parte declarativa/extensible

La diferencia es que Francis Suite intenta reunir extracción, procesamiento y estructuración de datos dentro de un framework propio con modelo interno basado en XML, hands, boxes, records, context y runtime.

## Sobre Tika y NiFi

Tika y NiFi no son lo mismo.

- Tika se enfoca en extraer contenido y metadata desde documentos.
- NiFi se enfoca en mover, enrutar y transformar flujos de datos entre sistemas.

Pueden complementarse entre sí, y también pueden complementarse con Francis Suite.

Formas posibles de mezcla:

- Francis Suite usando Tika como motor especializado para extracción documental
- NiFi usando los outputs de Francis Suite para mover archivos, enrutar data o cargar a bases de datos
- NiFi disparando ejecuciones de Francis Suite dentro de una arquitectura mayor

## Sobre scraping

Francis Suite no debe describirse solo como scraping.
Scraping es solo una de las posibles formas de extracción.

La descripción correcta es que se trata de un framework universal de extracción y procesamiento de datos desde múltiples fuentes.

## Sobre fallos y operación

El framework no solo produce archivos: ejecuta procesos.
Por eso puede fallar en distintos puntos.

Tipos de fallos posibles:

- errores del workflow
- errores del código
- configuraciones incorrectas
- timeouts
- caída de internet
- bloqueo de una página
- cambios en la fuente de datos
- errores de parsing
- problemas al guardar archivos
- errores del entorno de ejecución

Esto implica que necesita una mirada operativa, no solo de generación de outputs.
Idealmente debe poder:

- identificar el estado de ejecución
- registrar errores
- reintentar si aplica
- dejar trazabilidad
- asociar outputs a una ejecución específica

## Ejecución y comunicación de estado

La forma más natural de evolucionar el framework es agregar una capa de ejecución por API.

La opción más coherente con la arquitectura actual es:

- FastAPI como capa de ejecución
- session_id por ejecución
- endpoints para iniciar y consultar estado
- posibilidad de polling o WebSocket
- persistencia de sesión, errores y resultados

Conceptualmente:

- POST /run
- GET /status/{session_id}
- GET /context/{session_id}
- WS /ws/{session_id}

Cada ejecución debería tener un session_id único, idealmente UUID.
Ese ID permite rastrear:

- estado
- duración
- error
- metadata
- outputs generados
- contexto o resultados

## Sobre Supabase

Si el objetivo es dejar de subir CSV manualmente, lo ideal no es depender siempre de carga manual de archivos.

La evolución más natural sería:

- Francis Suite genera y estructura los datos
- luego persiste directamente a Supabase o deja los outputs listos para una capa de integración

Posibilidades:

- carga directa desde Python
- un hand dedicado a persistencia
- una capa externa que tome los outputs y los suba
- uso de NiFi para mover y cargar esos resultados

## Sobre NiFi en el caso de uso

NiFi puede ser útil para:

- mover archivos generados
- detectar nuevos outputs
- enrutar resultados
- transformar datos antes del destino final
- cargar datos a bases de datos
- automatizar el flujo operativo entre sistemas

No reemplaza a Francis Suite, sino que podría complementar la parte operativa de integración.

## Sobre si fue mala idea crear Francis Suite

No está mal haber creado un framework así.
Combinar ideas existentes para resolver mejor un problema real es normal en software.

Lo valioso del proyecto no es que invente cada componente desde cero, sino que:

- resuelve un problema real
- propone una arquitectura propia
- unifica capacidades dispersas
- tiene extensibilidad
- tiene potencial como plataforma

## Sobre uso en empresas

Sí podría usarse en empresas, pero no siempre será fácil que lo adopten directamente.
Las empresas suelen ser conservadoras por razones como:

- propiedad intelectual
- seguridad
- compliance
- soporte y mantenimiento
- riesgo operativo

También es importante separar:

- el framework base como proyecto preexistente
- las adaptaciones específicas hechas para una empresa

Si se quiere proteger la propiedad del framework, conviene dejar clara su preexistencia y revisar cuidadosamente los contratos laborales o de prestación de servicios.

## Qué usan normalmente las empresas

Muchas empresas no tienen una sola herramienta unificada para resolver esto.
Suelen usar combinaciones de:

- Python
- Playwright
- Selenium
- Scrapy
- requests/httpx
- pandas
- openpyxl
- Apache Tika
- Apache NiFi
- Airflow / Prefect / Dagster
- cron jobs
- scripts propios
- bases de datos y storage cloud

Eso refuerza la idea de que Francis Suite puede tener valor como intento de unificación.

## Formas útiles de describir Francis Suite

### Descripción general

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible y cloud-ready.

### Descripción más explicativa

Es un framework diseñado para automatizar la obtención, transformación, limpieza, normalización y estructuración de datos desde múltiples fuentes, generando resultados reutilizables y listos para integrarse con otros sistemas.

### Comparación conceptual breve

Puede entenderse como una combinación entre extracción multi-fuente y procesamiento declarativo de datos, dentro de una arquitectura propia basada en workflows XML y unidades extensibles llamadas hands.
