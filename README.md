# Francis Suite

> Framework **low-code** en XML para extracción y procesamiento de datos, construido en Python.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-150%2B%20passing-brightgreen)](tests/)
[![Status](https://img.shields.io/badge/estado-en%20desarrollo%20activo-orange)](docs/roadmap.md)

---

## ¿Qué es Francis Suite?

Un **framework universal de extracción, transformación y persistencia de datos**. Cada pipeline
se describe en un único archivo XML: obtener información, procesarla, validarla, transformarla y
guardarla, todo desde la misma definición declarativa.

Cubre el ciclo completo:

- **Adquisición** — peticiones HTTP, lectura de archivos del disco, descarga remota, subida a endpoints.
- **Transformación** — conversiones entre formatos (HTML, XML, JSON, CSV, Base64, binarios), extracción
  por XPath, expresiones regulares, splits y composiciones de texto.
- **Modelado** — boxes tipadas, records con schema, validación por fila, deduplicación por clave.
- **Persistencia** — exportación a JSON, CSV, NDJSON, XML, HTML, TXT/TSV, Excel y Parquet, en cualquier
  combinación, con metadata pública y privada por corrida.
- **Operación** — manejo de archivos (mover, copiar, eliminar, listar), proxies, journals append-only,
  sesiones reproducibles.

Toda la información fluye por un modelo unificado llamado **`boxes`** — predecible, tipada, con
scoping definido y lista para componer. El mismo workflow puede leer un Excel, llamar a una API,
mezclar resultados, deduplicarlos y persistirlos a Parquet para analítica sin escribir Python.

---

## Filosofía

| Principio | Qué significa en la práctica |
|-----------|------------------------------|
| **Declarativo, no imperativo** | El XML describe *qué* hay que hacer, no *cómo*. La lógica vive en los hands del runtime. |
| **Un único modelo de datos** | Todo es una `box`. Una `FVariable` entra, una `FVariable` sale. Sin objetos sueltos por el camino. |
| **El parser no es el motor** | El XML se transforma a un árbol de `FNode` neutro. El runtime no sabe del formato de entrada. |
| **Convención sobre configuración** | Defaults sensatos: si no se declara, no aparece. Si se declara, manda. |
| **Reproducible** | Escrituras atómicas, lockfiles, metadata privada con versión, sesión y entorno por cada corrida. |

---

## Por qué XML

Los workflows son **árboles de decisiones**. XML está pensado para árboles:

- **Schema:** validación estructural antes de ejecutar (XSD generado con `francis-suite schema`).
- **Autocompletado en el editor** (VS Code / Cursor) gracias al schema.
- **Legibilidad horizontal:** cualquier persona del equipo lee el flujo sin tener que leer Python.
- **Composición clara:** anidamiento, atributos y texto separados; sin convenciones implícitas de un YAML.

```xml
<francis-workflow>
    <httpx-call url="http://books.toscrape.com" name="html"/>
    <convert-html-to-xml name="page">${html}</convert-html-to-xml>

    <loop item="libro">
        <loop-list>
            <xpath-extract expression="//article[@class='product_pod']">${page}</xpath-extract>
        </loop-list>
        <loop-body>
            <box-def name="titulo">
                <xpath-extract expression=".//h3/a/@title">${libro}</xpath-extract>
            </box-def>
            <log>Encontrado: ${titulo}</log>
        </loop-body>
    </loop>
</francis-workflow>
```

---

## Quick Start

Requiere [Python 3.11+](https://www.python.org/downloads/) y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/mangelrfdev/francis-suite
cd francis-suite
uv sync
uv run francis-suite run workflows/all_books_pages.xml
```

El workflow scrapea `books.toscrape.com`, pagina hasta el final y exporta los resultados en
**ocho formatos distintos** bajo `output/`.

Para un pipeline orientado a producción ver
[`workflows/properties_workflow_template.xml`](workflows/properties_workflow_template.xml):
plantilla para listings con manifiesto de corrida, validación y salida estructurada.

---

## Capacidades principales

### Salida multi-formato declarativa

```xml
<record-save from="listings" format="json"    path="output/data.json"/>
<record-save from="listings" format="csv"     path="output/data.csv"  clean-data="true"/>
<record-save from="listings" format="ndjson"  path="output/data.ndjson"/>
<record-save from="listings" format="excel"   path="output/data.xlsx" sheet-name="Properties"/>
<record-save from="listings" format="parquet" path="output/data.parquet"/>
```

Misma fuente, cinco formatos, sin código de pegamento. Referencia completa en
[`docs/guides/record-save.md`](docs/guides/record-save.md).

Opciones de forma de los datos:

- **`clean-data="true"`** — exporta solo filas, sin metadata embebida.
- **`allow-nested="true"`** — JSON/NDJSON mantienen los grupos anidados.
- **`allow-prefix="true"`** — claves planas con prefijo de grupo (`listing.title`).
- *Default:* claves cortas, strings saneados (sin saltos de línea que rompen CSV).

### Lenguaje de expresiones incorporado

Variables, aritmética, comparaciones, operadores lógicos y métodos de string encadenables.

```xml
<if condition="${precio.toInt()} > 1000 and ${ciudad.toUpperCase()} == 'SANTIAGO'">
    <log>Listing premium en ${ciudad}</log>
</if>
```

Métodos disponibles: `isEmpty`, `isNotEmpty`, `toUpperCase`, `toLowerCase`, `trim`, `length`,
`contains`, `startsWith`, `endsWith`, `replace`, `toInt`, `toFloat`, `toBoolean`.

Evaluación con `simpleeval` (sin `eval()` nativo, sin acceso a `__builtins__`).

### Records estructurados

Schema, validación, deduplicación y metadata declaradas en el mismo XML.

```xml
<record-create name="listings" record-validation="collect-errors">
    <record-set-group name="listing" required="true">
        <record-set-field name="external_id" type="string"  required="true"/>
        <record-set-field name="title"       type="string"/>
        <record-set-field name="price"       type="integer"/>
        <record-set-field name="currency"    type="string"/>
    </record-set-group>
    <record-key>
        <key-field name="external_id"/>
    </record-key>
    <record-journal path="output/run.journal.ndjson"/>
</record-create>
```

Incluye:

- Validación de schema por fila (`strict` o `collect-errors`).
- Deduplicación automática por `record-key` con exportación separada de duplicados.
- Journal NDJSON append-only que se escribe en vivo, sobrevive a crashes.
- Metadata privada por corrida: filas totales, completitud, duración, RAM, errores, OS, versión, session id.
- Metadata pública embebida donde el formato lo soporta (`_metadata` en JSON, hoja en Excel, nodo en XML).

### Workflows reutilizables

```xml
<function-create name="fetchAndParse">
    <function-param name="url"/>
    <httpx-call url="${url}" name="html"/>
    <function-return>
        <convert-html-to-xml>${html}</convert-html-to-xml>
    </function-return>
</function-create>

<function-call name="fetchAndParse">
    <function-param name="url">https://example.com</function-param>
</function-call>
```

### Listo para producción

- **Imagen Docker** sin workflows ni secretos. Los `.xml` se montan desde el host.
- **Parámetros por CLI**: `--param ciudad=santiago --param paginas=10`.
- **Variables sensibles** enmascaradas automáticamente en logs (`api_key`, `token`, `password`, …).
- **Schema XSD** generado para autocompletado en editores.
- **Escrituras atómicas** en todos los formatos (sin archivos a medias después de un fallo).
- **150+ tests** que cubren parser, runtime, hands, expresiones, exports y casos de error.

---

## Capacidades disponibles hoy

Catálogo de **hands** integrados, agrupados por función. Referencia completa de tags y atributos
en [`docs/architecture.md`](docs/architecture.md).

### Red y HTTP

| Hand | Para qué sirve |
|------|----------------|
| `<httpx-call>` | Peticiones HTTP (GET/POST/…); soporta headers, payloads, cookies, streaming, retries |
| `<httpx-cookie-jar>` | Cookie jar compartido entre llamadas |
| `<httpx-introspect>` | Inspección del último response (status, headers, cookies) |
| `<set-proxy>` | Configurar proxies (manual, archivo, API, rotación, probe) |

### Archivos en disco

| Hand | Para qué sirve |
|------|----------------|
| `<file-read>` | Leer archivos como texto o binario (UTF-8, latin-1, base64) |
| `<file-write>` | Escribir contenido a disco con escritura atómica |
| `<file-manage>` | Eliminar, mover, copiar y listar archivos y carpetas (con `force-*` y filtros) |
| `<file-download>` | Descargar un recurso remoto directo a disco |
| `<file-upload>` | Enviar un archivo a un endpoint HTTP |

### Conversiones entre formatos

| Hand | Conversión |
|------|------------|
| `<convert-html-to-xml>` | HTML "sucio" → XML limpio listo para XPath |
| `<convert-html-entities-to-text>` | Entidades HTML (`&amp;`, `&#xE9;`) → texto |
| `<convert-xml-to-json>` / `<convert-json-to-xml>` | Conversión bidireccional XML ↔ JSON |
| `<convert-xml-to-csv>` | XML tabular → CSV |
| `<convert-csv-to-json>` / `<convert-json-to-csv>` | CSV ↔ JSON |
| `<convert-text-to-base64>` / `<convert-base64-to-text>` | Texto ↔ Base64 |
| `<convert-binary-to-base64>` / `<convert-base64-to-binary>` | Binarios (imágenes, PDFs, blobs) ↔ Base64 |
| `<convert-text-to-url>` / `<convert-url-to-text>` | URL-encoding bidireccional |

### Extracción y manipulación de texto

| Hand | Para qué sirve |
|------|----------------|
| `<xpath-extract>` | Selección sobre XML / HTML convertido (atributos, texto, subárboles) |
| `<regex>` (+ `<regex-pattern>`, `<regex-input>`, `<regex-result>`) | Match, captura de grupos y plantilla de salida |
| `<text-split>` | Tokenización por separador, regex o líneas |
| `<compose>` | Interpolación de variables a texto plano |
| `<evaluate>` | Evaluación de expresiones (`${precio * cantidad}`, comparaciones, métodos de string) |

### Variables y composición de datos

| Hand | Para qué sirve |
|------|----------------|
| `<box-def>` / `<box>` | Definir y reusar variables con scope |
| `<shared-box-def>` / `<shared-box>` | Variables compartidas entre scopes (`replace="true|false"`) |
| `<build-list>` | Construir listas explícitamente desde hijos |

### Records (datos estructurados)

| Hand | Para qué sirve |
|------|----------------|
| `<record-create>` | Definir schema, claves, validación, journal, metadata |
| `<record-add>` | Insertar una fila normalizada según el schema |
| `<record-last-added>` / `<record-count>` | Inspección y conteo |
| `<record-save>` | Exportar a JSON/CSV/NDJSON/XML/HTML/TXT/Excel/Parquet (con `clean-data`, `allow-nested`, `allow-prefix`) |
| `<record-save-duplicates>` | Exportar filas descartadas por clave duplicada |
| `<record-save-validation-errors>` | Exportar filas rechazadas en modo `collect-errors` |
| `<record-save-metadata>` / `<record-private-metadata>` | Persistir metadata pública y privada |

### Control de flujo y composición

| Hand | Para qué sirve |
|------|----------------|
| `<loop>` (+ `<loop-list>`, `<loop-body>`) | Iterar listas con `item`, `index`, `max-loops` |
| `<while>` | Bucle por condición |
| `<if>` / `<else>` / `<case>` | Ramas condicionales y switch-case |
| `<try>` / `<catch>` | Manejo de errores localizado |
| `<exit>` | Detener la ejecución del workflow |
| `<function-create>` / `<function-call>` (+ `<function-param>`, `<function-return>`) | Funciones reutilizables con scope propio |
| `<call-workflow>` | Ejecutar otro workflow XML externo |

### Operación, tiempos y observabilidad

| Hand | Para qué sirve |
|------|----------------|
| `<log>` | Imprimir mensajes con interpolación |
| `<sleep>` / `<sleep-min>` / `<sleep-max>` / `<sleep-avg>` | Pausas fijas y aleatorias |
| `<pause-task>` | Pausar la ejecución a la espera de input/condición |
| `<session-pulse>` | Heartbeat de sesión para procesos largos |

---

## En desarrollo y próximas funcionalidades

El roadmap completo (con criterios de aceptación y decisiones de diseño) vive en
[`docs/roadmap.md`](docs/roadmap.md). Resumen orientado a expectativas:

**Próximas fuentes de datos**

- `pdf-read` — lectura y extracción estructurada desde archivos PDF. Hoy ya se puede cargar el binario con `file-read` y convertirlo con `convert-binary-to-base64` para enviar a un endpoint externo; el hand nativo unificará la parte de parseo.
- `excel-read` — lectura directa de `.xlsx` / `.xls` y `.csv` desde el XML (Excel ya está disponible para **escritura** vía `record-save format="excel"`).
- `json-read` — carga de archivos JSON externos como `box` lista para iterar.
- `use-ia` — invocación a modelos (OCR de imágenes, extracción semántica desde texto/PDF, clasificación) con timeout, retry y contrato de errores.

**Vanguardia / clientes avanzados**

- `playwright-call` — control completo de navegador (clicks, scroll, esperas, intercepción de red) con un contrato declarativo en XML.
- `scrapling-call` — scraping resiliente a cambios de layout, integrado al pipeline.
- `set-proxy` extendido — soporte de credenciales en base de datos, integración con Playwright y Scrapling.

**Infraestructura y entrega**

- **Storage Providers** (fsspec) — guardar y leer de S3, Google Cloud Storage, Azure Blob desde el mismo `record-save` o `file-write`.
- **`fs` helpers de expresión** — `${fs.uuid()}`, `${fs.now()}`, `${fs.env("KEY")}`, `${fs.random(1,100)}`.
- **API REST (FastAPI)** — `POST /run`, `GET /status/:id`, `WS /ws/:id` para orquestar workflows desde otras aplicaciones.
- **Plugin VS Code / Cursor** — autocompletado completo, ejecución paso a paso, tree de eventos en vivo, inspector de variables y visor de records en cascada.
- **Sistema de plugins externos** (`hands/ext/`) — agregar hands propios sin modificar el core.

**Fuera de scope** (para ser explícitos)

- `database-call` — no planificado: la salida estándar son archivos vía `record-save` u object storage.
- `send-mail`, `ftp-call`, `zip` — sin prioridad hasta tener un caso de uso concreto.
- Workflows en YAML — descartado: el formato declarativo es y será XML.

---

## Arquitectura

```
workflow.xml
   │
   ▼
FParser ──► árbol de FNodes (AST universal, agnóstico al formato de entrada)
   │
   ▼
FRuntime ──► ejecuta cada Hand
                  │
                  ▼
                Hand.execute() ──► FVariable
                                       │
                                       ▼
                                  FContext (boxes, scopes)
                                       │
                                       ▼
                                  EventBus (start, end, error)
```

El motor de ejecución no depende del XML. El parser construye un árbol de `FNode` neutros;
todo lo demás — runtime, hands, expresiones, eventos — opera sobre ese árbol. Si en algún momento
se sumara otra forma de definición (editor visual, builder gráfico), solo haría falta un parser
nuevo que produzca el mismo árbol; el motor queda intacto. El formato declarativo escrito a mano
sigue siendo XML por diseño.

Diseño completo en [`docs/architecture.md`](docs/architecture.md). Decisiones de diseño
documentadas en [`docs/decisions/`](docs/decisions/).

---

## Stack técnico

| Componente | Librería | Rol |
|------------|----------|-----|
| Lenguaje | Python 3.11+ | Core |
| XML | lxml | Parsing y XPath |
| HTTP | httpx | Cliente HTTP moderno |
| Browser | Playwright | Páginas con JavaScript |
| Extracción robusta | Scrapling | Resiliencia a cambios de layout |
| Expresiones | simpleeval | Evaluación segura |
| Excel / Parquet | openpyxl, pyarrow | Exportación nativa |
| Métricas | psutil | RAM y entorno para metadata privada |
| Packaging | uv | Instalación y lockfile |
| Tests | pytest, respx | Cobertura del pipeline completo |
| Linting | ruff | Linter y formateador |

Lista completa en [`pyproject.toml`](pyproject.toml).

---

## CLI

```bash
francis-suite run workflow.xml
francis-suite run workflow.xml --param url=https://ejemplo.com --param token=SECRET
francis-suite schema --out schema
francis-suite --help
francis-suite --version
```

---

## Docker

```bash
docker build -t francis-suite:local .
docker compose run --rm francis
```

Los workflows se montan desde el host (no van adentro de la imagen). Output en `./docker-output/`.
Detalles en [`workflows/README.md`](workflows/README.md).

---

## Estructura del proyecto

```
francis_suite/
├── cli.py              # CLI entry point
├── core/               # motor de ejecución
│   ├── parser.py           # XML → FNode tree
│   ├── runtime.py          # ejecución del árbol
│   ├── context.py          # scoping de variables
│   ├── variables.py        # tipos FVariable
│   ├── nodes.py            # definición de FNode
│   ├── registry.py         # HandRegistry + @hand
│   ├── session.py          # FrancisSession
│   ├── events.py           # EventBus
│   ├── expressions.py      # motor de expresiones
│   └── records.py          # sistema de records
└── hands/
    └── core/           # hands integrados
tests/                  # 150+ tests
docs/                   # documentación
schema/                 # XSD y manifiesto JSON (regenerable)
workflows/              # workflows públicos de ejemplo
templates/              # snippets reutilizables (Cursor / Claude)
integrations/web/       # specs de integración con producto web (opcional)
```

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`docs/README.md`](docs/README.md) | Índice general |
| [`docs/architecture.md`](docs/architecture.md) | Capas, FNode, hands, scoping, modelo mental |
| [`docs/roadmap.md`](docs/roadmap.md) | Estado, próximos pasos, fuera de scope |
| [`docs/guides/record-save.md`](docs/guides/record-save.md) | Exportación: formatos, metadata, `clean-data`, `allow-nested`, `allow-prefix` |
| [`docs/guides/httpx-call.md`](docs/guides/httpx-call.md) | HTTP: cookies, reintentos, headers sensibles |
| [`docs/guides/run-output-and-integration.md`](docs/guides/run-output-and-integration.md) | Artefactos por corrida, integración con otros procesos |
| [`docs/guides/workflow-schema.md`](docs/guides/workflow-schema.md) | Setup de editor, generación de XSD |
| [`docs/decisions/`](docs/decisions/) | Architecture Decision Records |

---

## Estado

En **desarrollo activo**. El core está implementado y testeado: parser, runtime, sistema de records,
expresiones, hands integrados de red, archivos, conversiones, control de flujo y exportación
multi-formato.

Lo que sigue (PDF nativo, lectura de Excel/CSV/JSON, integración con IA, navegador completo, storage
en la nube, plugin del editor, API REST) está en la sección
[**En desarrollo y próximas funcionalidades**](#en-desarrollo-y-próximas-funcionalidades) y, con más
detalle técnico, en [`docs/roadmap.md`](docs/roadmap.md).

---

## Desarrollo

```bash
uv sync --extra dev
uv run pytest          # 150+ tests
uv run pytest -x       # detener en la primera falla
uv run ruff check .    # lint
```

---

## Licencia

[MIT](LICENSE).
