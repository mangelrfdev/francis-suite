# CV AI Context — Francis Suite

## Propósito de este documento

Este documento está pensado para dárselo a una IA que ayude a redactar CV, LinkedIn, cartas de presentación o respuestas de entrevista relacionadas con el proyecto `Francis Suite`.

El objetivo es que la IA entienda:

- qué es realmente `Francis Suite`
- cómo funciona su arquitectura
- qué problemas resuelve
- cómo debe posicionarse correctamente
- qué decisiones de carrera y tecnología se están tomando alrededor del proyecto
- qué se puede afirmar con honestidad en un CV y qué conviene presentar con más cuidado

La IA debe priorizar fidelidad técnica, claridad y honestidad profesional. No debe inventar features no implementadas como si ya existieran en producción.

---

## Resumen ejecutivo del proyecto

`Francis Suite` es un framework universal de extracción y procesamiento de datos.

Sus atributos clave son:

- low-code
- declarativo
- extensible
- cloud-ready

No debe describirse solo como un framework de scraping web.
Aunque puede trabajar con extracción web, su visión es más amplia: procesar datos provenientes de múltiples fuentes, como:

- web
- PDF
- Excel
- JSON
- APIs
- imágenes con IA
- bases de datos

La mejor forma de describirlo es como un framework que permite definir procesos declarativos de obtención, transformación, limpieza, normalización, estructuración y exportación de datos.

---

## Qué es Francis Suite

Forma corta recomendada:

`Francis Suite` es un framework universal de extracción y procesamiento de datos, low-code, declarativo, extensible y cloud-ready.

Forma explicativa recomendada:

Es un framework desarrollado en Python para definir y ejecutar flujos declarativos de extracción y procesamiento de datos desde múltiples fuentes. Permite obtener información, transformarla, estructurarla y exportarla como resultados reutilizables, apoyándose en workflows XML, unidades ejecutables llamadas `hands`, almacenamiento intermedio en `boxes` y estructuras tabulares llamadas `records`.

No debe reducirse a frases como:

- "un scraper"
- "una herramienta para páginas web"
- "solo genera archivos"

Eso sería incompleto.

---

## Qué problema intenta resolver

`Francis Suite` intenta unificar en una sola arquitectura varias capacidades que en muchas empresas suelen estar repartidas entre scripts, librerías y plataformas separadas.

Capacidades que busca unificar:

- extracción desde múltiples fuentes
- conversión entre formatos
- parsing
- limpieza y normalización de datos
- estructuración de resultados
- persistencia de outputs
- trazabilidad de ejecución
- extensibilidad por nuevas capacidades

La idea central no es solo extraer datos, sino poder ejecutar procesos de datos repetibles, declarativos y mantenibles.

---

## Arquitectura real del proyecto

Este resumen está alineado con `docs/architecture.md`.

### Pipeline de ejecución

El pipeline principal es:

- `workflow.xml`
- `FParser` lee el XML y construye un árbol de `FNode`
- `FRuntime` recorre el árbol y ejecuta cada `hand`
- `Hand.execute()` devuelve un `FVariable`
- `FContext` guarda resultados en variables
- `EventBus` comunica inicio, fin o error

### Lenguaje del workflow

El lenguaje de workflow del framework es XML.
La raíz es `<francis-workflow>`.
Según la arquitectura actual, no hay plan de soportar un segundo lenguaje de workflow como YAML.

### Filosofía central

La arquitectura tiene una filosofía explícita:

- todo se guarda en `boxes`
- una `box` es la unidad de datos del framework
- todo resultado reutilizable vive en una `box`

### Conceptos clave

#### Hand

Una `hand` es la unidad ejecutable del framework.
Cada etiqueta XML ejecutable corresponde a una operación implementada en Python.

Ejemplos actuales de hands:

- HTTP con `httpx`
- parsing HTML/XML/JSON
- XPath
- regex
- control de flujo
- lectura y escritura de archivos
- records
- logging
- composición de texto

Las `hands` son también la base de la extensibilidad. En el futuro pueden encapsular otras tecnologías como Playwright, OCR, IA, conectores documentales o integraciones de persistencia.

#### Box

Una `box` es la unidad de almacenamiento de datos dentro del workflow.
Se usa para guardar resultados intermedios o finales reutilizables dentro del contexto.

#### Record

Un `record` es la estructura orientada a filas, schema, validación, metadata y persistencia.
Permite construir datasets estructurados y exportarlos en distintos formatos.

### Ejecución y sesión

El framework tiene el concepto de sesión de ejecución.
La sesión contiene:

- `id` tipo UUID
- `status`
- `context`
- timestamps
- duración
- error

Estados definidos:

- `CREATED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

Esto es importante para hablar de trazabilidad, operación y futura exposición por API.

### Eventos

Existe un `EventBus` para comunicar eventos de ejecución.
Hay eventos de sesión y eventos de `hands`.
Eso refuerza la idea de que el proyecto no es solo un conjunto de scripts, sino un motor con observabilidad interna.

---

## Estado actual del framework

Según la documentación actual, el core implementado incluye:

- parser XML
- runtime
- registry de hands
- contexto con scopes
- sistema de variables
- records con schema y metadata
- CLI de ejecución
- event bus
- expression engine
- soporte multi-formato en `record-save`
- metadata privada automática por sesión
- deduplicación por hash con `RecordKey`
- tests multiplataforma

También existe una lista clara de futuros componentes o áreas en evolución, entre ellas:

- `FastAPI REST`
- nuevas fuentes como Playwright, PDF, Excel, IA
- storage cloud
- plugin VS Code
- schema/contrato XML más completo

La IA no debe presentar esas capacidades futuras como si ya estuvieran completamente implementadas, salvo que el usuario le diga explícitamente que ya se desarrollaron después.

---

## Qué genera Francis Suite

`Francis Suite` puede generar:

- datos estructurados en memoria
- `records`
- archivos de salida
- metadata privada por sesión
- trazabilidad de ejecución
- estado de proceso
- errores y métricas operativas

Formatos de salida actualmente soportados en `record-save`:

- JSON
- CSV
- NDJSON
- XML
- HTML
- TXT
- Excel/XLSX
- Parquet

La IA debe evitar decir simplemente que "genera archivos". La forma más correcta es indicar que genera resultados estructurados y artefactos de ejecución.

---

## Cómo posicionarlo correctamente en CV o entrevista

### Posicionamiento correcto

La mejor manera de posicionar `Francis Suite` es como:

- framework universal de extracción y procesamiento de datos
- motor declarativo de workflows XML
- sistema extensible basado en `hands`
- arquitectura con `boxes`, `records`, runtime y trazabilidad de sesión

### Posicionamiento incorrecto o incompleto

Evitar describirlo solo como:

- scraper web
- bot simple
- generador de CSV
- script personal

Esas frases pierden valor y no reflejan la arquitectura real.

### Forma profesional de explicarlo

`Francis Suite` es un framework desarrollado en Python para definir y ejecutar workflows XML orientados a extracción y procesamiento de datos desde múltiples fuentes. Su arquitectura declarativa y extensible permite encapsular operaciones en `hands`, manejar estado y contexto de ejecución, estructurar datasets mediante `records` y generar outputs reutilizables con metadata y trazabilidad por sesión.

---

## Comparaciones útiles con otras tecnologías

La IA puede usar comparaciones conceptuales, pero sin exagerar.

Referencias útiles:

- `Scrapy`: por la parte de extracción
- `Apache Tika`: por la parte de extracción de contenido documental
- `Apache NiFi`: por la parte de movimiento y orquestación de flujos de datos
- `Prefect`, `Dagster`, `Airflow`: por la parte de ejecución y observabilidad de procesos
- `n8n`: por la parte declarativa y de automatización conectada

La idea no es decir que `Francis Suite` sea una copia de una de esas herramientas, sino que combina capacidades que normalmente aparecen separadas.

Una comparación prudente sería:

`Francis Suite` puede entenderse como una arquitectura propia que combina ideas de extracción multi-fuente, procesamiento declarativo y estructuración de datos, en lugar de limitarse a una sola categoría de herramienta.

---

## Qué no debe afirmar una IA sin cuidado

La IA debe evitar afirmar como hecho consolidado cosas que hoy están descritas como futuro o evolución, por ejemplo:

- que la API FastAPI ya está en producción, si no se confirma
- que Playwright ya está implementado como `hands`, si aún está pendiente
- que el framework ya soporta totalmente todas las fuentes listadas, si algunas siguen como visión o roadmap
- que existe una plataforma cloud completa u orquestación empresarial cerrada, si todavía está en diseño

Sí puede hablar de estas cosas como:

- dirección de evolución
- diseño coherente con la arquitectura actual
- roadmap técnico natural del proyecto

---

## Decisiones que se están tomando para carrera y CV

El usuario quiere alinear el proyecto con vacantes tipo:

- desarrollador RPA
- automatización de procesos
- Python automation
- integración de microservicios
- cloud deployment

En particular, hay interés en calzar con ofertas que piden:

- Python
- Playwright
- UiPath como deseable
- n8n como deseable
- Appian como deseable
- microservicios
- Git/GitHub
- cloud, idealmente GCP

### Decisión estratégica actual

La estrategia recomendada no es meter todas las tecnologías posibles en `Francis Suite`, sino priorizar las que mejor conversan con la arquitectura y además permiten escribir un CV honesto.

Tecnologías priorizadas para evolución real del proyecto:

- Python
- Playwright
- FastAPI
- n8n
- Git/GitHub
- despliegue cloud
- Supabase como caso práctico de persistencia/actualización

Tecnologías secundarias o de estudio complementario:

- UiPath
- Appian

Razón:

- `Playwright` encaja naturalmente como futura familia de `hands` para automatización browser-based
- `FastAPI` encaja con el roadmap de API de ejecución y comunicación de estado
- `n8n` encaja muy bien como capa externa de automatización e integración
- `UiPath` y `Appian` son valiosas para contexto de empleabilidad, pero menos naturales como base técnica del proyecto actual

---

## Dirección técnica recomendada para evolucionar el proyecto

### 1. Capa de ejecución por API

Evolución natural recomendada:

- `POST /run`
- `GET /status/{session_id}`
- `GET /context/{session_id}` o resultados relacionados
- `WS /ws/{session_id}` para estado en tiempo real

Esto está alineado con la existencia de:

- sesiones con UUID
- estados de ejecución
- event bus
- metadata por sesión

### 2. Hands de Playwright

Dirección sugerida:

- `playwright-open`
- `playwright-click`
- `playwright-fill`
- `playwright-wait-for`
- `playwright-extract-text`

Esto permitiría acercar `Francis Suite` a automatización web moderna y a vacantes orientadas a RPA/Python automation.

### 3. Integración con n8n

Uso recomendado de `n8n`:

- disparar ejecuciones
- consultar estado
- tomar outputs
- mover archivos
- cargar o actualizar datos en Supabase o DB
- enviar notificaciones y alertas

### 4. Persistencia automatizada

No depender de subida manual de CSV.
La evolución deseable es:

- persistencia directa desde Python
- o `hands` dedicadas a persistencia
- o capa externa de integración que tome outputs estructurados y los cargue en destino

---

## Qué puede decir el CV con honestidad

Si el usuario continúa esta dirección y construye estas piezas de verdad, el CV puede enfatizar:

- Python
- automatización de procesos
- Playwright
- diseño de framework declarativo
- microservicios con FastAPI
- integración de flujos con n8n
- Git/GitHub
- despliegue cloud
- estructuración y exportación de datasets
- trazabilidad de ejecución y manejo de estado por sesión

### Stack sugerido para CV si esas piezas se implementan o usan realmente

Opción más técnica:

`Python · Playwright · FastAPI · n8n · httpx · lxml · XPath · XML · Regex · Git/GitHub · Supabase · Cloud`

Opción más alineada al tipo de vacante:

`Python · Process Automation · Playwright · FastAPI · Microservices · n8n · Git/GitHub · Cloud Deployment`

La IA debe evitar agregar `UiPath` o `Appian` como stack principal si el usuario aún no los ha usado de forma práctica.

---

## Cómo debería ayudar una IA a redactar el CV

La IA que reciba este documento debería:

- traducir la arquitectura del proyecto a lenguaje comprensible para reclutadores y entrevistadores
- mantener una versión más técnica para entrevistas de ingeniería
- no minimizar el proyecto llamándolo solo "scraper"
- no exagerar capacidades futuras como si ya estuvieran productizadas
- enfatizar impacto, arquitectura y extensibilidad
- resaltar alineación con automatización, microservicios y operación de procesos

### Tono recomendado para reclutador

Claro, simple, profesional, sin exceso de jerga.

### Tono recomendado para entrevista técnica

Más énfasis en:

- XML workflows
- runtime
- hands
- boxes
- records
- sesiones
- eventos
- outputs multi-formato
- extensibilidad

---

## Frases útiles que una IA puede reutilizar

### Versión breve

Desarrollé un framework en Python para extracción y procesamiento de datos desde múltiples fuentes, basado en workflows XML declarativos, con arquitectura extensible, manejo de estado de ejecución y generación de outputs estructurados.

### Versión media

Desarrollé `Francis Suite`, un framework en Python orientado a automatizar procesos de extracción, transformación y estructuración de datos desde múltiples fuentes. El proyecto utiliza workflows XML declarativos, un runtime propio basado en unidades ejecutables llamadas `hands`, almacenamiento contextual mediante `boxes` y datasets estructurados mediante `records`, incorporando además trazabilidad de sesión, metadata operativa y exportación multi-formato.

### Versión alineada a automatización/RPA

Desarrollé un framework en Python orientado a automatización de procesos de datos, capaz de ejecutar workflows declarativos, estructurar resultados, gestionar estado de ejecución por sesión y evolucionar hacia integraciones con browser automation, microservicios y capas de orquestación externa.

---

## Instrucción final para la IA

Si vas a redactar un CV, LinkedIn o pitch profesional a partir de este documento:

- mantén la fidelidad técnica
- usa el proyecto como evidencia de capacidad arquitectónica y de automatización
- evita simplificarlo en exceso
- evita vender roadmap como implementación final
- prioriza claridad, honestidad y alineación con roles de automatización, RPA, data processing y microservicios
