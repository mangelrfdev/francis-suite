# Francis Suite

> Framework **low-code** en XML para extracción y procesamiento de datos, construido en Python.

[![PYTHON 3.11+](https://img.shields.io/badge/PYTHON-3.11%2B-blue)](https://www.python.org/downloads/)
[![LICENCIA MIT](https://img.shields.io/badge/LICENCIA-MIT-yellow)](LICENSE)
[![PRUEBAS 150+](https://img.shields.io/badge/PRUEBAS-150%2B-brightgreen)](tests/)
[![ESTADO Funcional](https://img.shields.io/badge/ESTADO-Funcional%20%C2%B7%20extensible-brightgreen)](docs/roadmap.md)

> Core **funcional** y listo para usar en pipelines reales. Nuevas capacidades se suman como **hands**
> sin reescribir el motor — ver [`docs/roadmap.md`](docs/roadmap.md).

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

## Tests y cobertura

El proyecto incluye **más de 150 tests** con `pytest`. Su objetivo es **asegurar que todo lo
construido en Francis Suite se comporta como se documenta**: el parser que lee el XML, el runtime
que ejecuta cada hand, el flujo de datos entre `box-def` y `box`, las expresiones `${...}`, el
sistema de records (schema, validación, deduplicación, exportación), las llamadas HTTP, las
conversiones de formato y la escritura atómica a disco.

Cada suite ejecuta **workflows XML reales** — el mismo tipo de archivo que correrías con
`francis-suite run` — y comprueba el resultado en cada capa: parser → runtime → hands → contexto
→ artefactos en `output/`. También cubren los **caminos de error** (tags desconocidos, filas
inválidas en un record, timeouts, límites de sesión y RAM) para que un fallo en producción no
sea la primera vez que el motor ve ese caso.

| Suite | Qué valida |
|-------|------------|
| [`test_pipeline.py`](tests/test_pipeline.py) | Pipeline completo: `httpx-call`, conversiones HTML/XML/JSON/CSV, `xpath-extract`, `loop`/`while`, `if`/`else`/`case`, funciones, `regex`, `compose`, `evaluate`, records (`record-create`, `record-add`, `record-save` con `clean-data`, `allow-nested`, `allow-prefix`), archivos, `try`/`catch`, `exit` |
| [`test_expression_chain.py`](tests/test_expression_chain.py) | Motor de expresiones: aritmética, comparaciones, métodos encadenables (`toUpperCase`, `isEmpty`, `toInt`, …) |
| [`test_httpx_auto_cookies.py`](tests/test_httpx_auto_cookies.py) | Cookie jar compartido entre `<httpx-call auto-cookies="true">` |
| [`test_httpx_cookie_jar_close.py`](tests/test_httpx_cookie_jar_close.py) | Cierre de sesión HTTP y bloqueo hasta `set-proxy` |
| [`test_httpx_introspect.py`](tests/test_httpx_introspect.py) | Inspección del último response (status, headers, cookies) |
| [`test_set_proxy.py`](tests/test_set_proxy.py) | Configuración y rotación de proxies |
| [`test_schema_gen.py`](tests/test_schema_gen.py) | Generación de XSD y manifiesto JSON del schema |
| [`test_liveness.py`](tests/test_liveness.py) | Deadline de sesión, `session-pulse`, límites de RAM |
| [`test_box_def_item.py`](tests/test_box_def_item.py) | Boxes en contextos de `loop` |

Para correr toda la suite desde la raíz del repo:

```bash
uv sync --extra dev
uv run pytest
uv run pytest -x    # detener en el primer fallo
```

Los workflows de ejemplo en [`workflows/`](workflows/) y [`examples/`](examples/) complementan
los tests como referencia ejecutable; la fuente de verdad del comportamiento del motor está en
`tests/`.

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
<?xml version="1.0" encoding="UTF-8"?>
<francis-workflow>

    <!-- 1. Pedir la página a la API. El XML expresa la request completa:
         método, timeout, headers de autenticación y formato, y query params.
         Todo a la vista, sin objetos sueltos ni código de pegamento. -->
    <box-def name="pagina_html">
        <httpx-call url="https://api.miportal.com/listings/search" method="GET" timeout="15000">

            <!-- Headers HTTP. ${api_token} viene del CLI (--param api_token=...) y
                 se enmascara automáticamente en logs porque el nombre matchea 'token'. -->
            <httpx-header name="Authorization">Bearer ${api_token}</httpx-header>
            <httpx-header name="Accept">text/html</httpx-header>
            <httpx-header name="Accept-Language">es-CL,es;q=0.9</httpx-header>
            <httpx-header name="User-Agent">francis-suite/1.0</httpx-header>

            <!-- En GET, cada httpx-param se concatena al query string:
                 ?ciudad=santiago&limite=50&orden=precio_desc -->
            <httpx-param name="ciudad">santiago</httpx-param>
            <httpx-param name="limite">50</httpx-param>
            <httpx-param name="orden">precio_desc</httpx-param>
        </httpx-call>
    </box-def>

    <!-- 2. El HTML de la web suele venir sin cerrar bien los tags. convert-html-to-xml lo
         normaliza a XML válido para que XPath pueda recorrerlo sin romperse. Lee del cuerpo:
         <box name="pagina_html"/> entrega el HTML que guardamos arriba. -->
    <box-def name="pagina_xml">
        <convert-html-to-xml>
            <box name="pagina_html"/>
        </convert-html-to-xml>
    </box-def>

    <!-- 3. xpath-extract aplica la expresión sobre el XML que recibe como hijo. Devuelve una
         lista con cada <article class="listing">, que es la tarjeta de una propiedad. -->
    <box-def name="tarjetas_propiedades">
        <xpath-extract expression="//article[@class='listing']">
            <box name="pagina_xml"/>
        </xpath-extract>
    </box-def>

    <!-- 4. loop recorre la lista. 'item' es el nombre de la box que tendrá el elemento actual
         de la iteración; 'index' es la posición (1, 2, 3...). -->
    <loop item="tarjeta_propiedad" index="numero">

        <!-- La lista a iterar se entrega como hijo de loop-list. -->
        <loop-list>
            <box name="tarjetas_propiedades"/>
        </loop-list>

        <!-- Todo lo que va dentro de loop-body se ejecuta una vez por tarjeta. -->
        <loop-body>

            <!-- Sobre la tarjeta actual, sacar el título del <h3 class="title">. -->
            <box-def name="titulo_propiedad">
                <xpath-extract expression="//h3[@class='title']/text()">
                    <box name="tarjeta_propiedad"/>
                </xpath-extract>
            </box-def>

            <!-- Mismo patrón para el precio sobre la tarjeta. -->
            <box-def name="precio_propiedad">
                <xpath-extract expression="//span[@class='price']/text()">
                    <box name="tarjeta_propiedad"/>
                </xpath-extract>
            </box-def>

            <!-- log interpola ${} con el valor actual de cada box y lo imprime. -->
            <log>Propiedad ${numero}: ${titulo_propiedad} — ${precio_propiedad} CLP</log>

        </loop-body>

    </loop>

</francis-workflow>
```

> El endpoint `api.miportal.com` es ilustrativo: la idea es mostrar la forma de una request
> seria (auth + headers + params + timeout) en un solo árbol XML. El workflow **ejecutable**
> equivalente contra un sitio público real (`books.toscrape.com`) vive en
> [`workflows/all_books_pages.xml`](workflows/all_books_pages.xml) y se corre desde el
> [Quick Start](#quick-start).

Cada hand opera sobre la salida del anterior. El anidamiento del XML **es** el flujo de datos:
una `box-def` envuelve el resultado, una `box` lo entrega al siguiente hand.

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

### Llamadas HTTP (GET, POST, headers, query params, body)

`<httpx-call>` cubre el ciclo completo de una request: método, headers, parámetros, timeout,
tipos de respuesta (texto / binario / stream a disco) y una sesión opcional con cookie jar
compartido entre llamadas. Los headers y parámetros van como hijos del tag — uno por línea —
para que el XML siga leyéndose como un árbol de decisiones.

#### GET con headers y query string

```xml
<!-- GET por defecto: si no se pasa 'method', es GET.
     Cada <httpx-header> se vuelve un header HTTP del request.
     Cada <httpx-param> se va al query string: ?ciudad=santiago&limite=50 -->
<box-def name="propiedades_json">
    <httpx-call url="https://api.miportal.com/listings" timeout="15000">
        <httpx-header name="Authorization">Bearer ${api_token}</httpx-header>
        <httpx-header name="Accept">application/json</httpx-header>
        <httpx-header name="User-Agent">francis-suite/1.0</httpx-header>

        <httpx-param name="ciudad">santiago</httpx-param>
        <httpx-param name="limite">50</httpx-param>
        <httpx-param name="orden">precio_desc</httpx-param>
    </httpx-call>
</box-def>
```

Atributos sensibles (`api_token`) viajan como boxes y se enmascaran automáticamente en logs si
el nombre coincide con `api_key`, `token`, `password`, `secret`, etc.

#### POST con cuerpo form-encoded

En cualquier método distinto de GET, los `<httpx-param>` se mandan como **cuerpo del request**
(`application/x-www-form-urlencoded`), no como query string. Los `<httpx-header>` siguen siendo
headers.

```xml
<!-- POST a un endpoint de login. Los params van en el body. -->
<box-def name="respuesta_login">
    <httpx-call url="https://api.miportal.com/auth/login" method="POST" timeout="20000">
        <httpx-header name="Accept">application/json</httpx-header>
        <httpx-header name="X-Client-Id">${client_id}</httpx-header>

        <httpx-param name="usuario">${usuario}</httpx-param>
        <httpx-param name="password">${password}</httpx-param>
    </httpx-call>
</box-def>
```

Métodos válidos: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`. En todos ellos, los hijos
disponibles son los mismos (`httpx-header`, `httpx-param`).

#### Mantener una sesión: `auto-cookies`

`auto-cookies="true"` hace que el runtime use **un solo cliente HTTP por sesión** que conserva el
cookie jar entre llamadas — como si fuera un navegador. Útil para flujos tipo *login + zona
privada + logout* sin reenviar credenciales en cada paso.

```xml
<!-- 1. Login: el servidor responde con Set-Cookie. El cliente las guarda. -->
<httpx-call url="https://api.miportal.com/login" method="POST" auto-cookies="true">
    <httpx-param name="usuario">${usuario}</httpx-param>
    <httpx-param name="password">${password}</httpx-param>
</httpx-call>

<!-- 2. Llamadas siguientes con auto-cookies="true" reenvían esas cookies automáticamente. -->
<box-def name="perfil">
    <httpx-call url="https://api.miportal.com/me" auto-cookies="true"/>
</box-def>
```

#### Otros tipos de respuesta

```xml
<!-- response="binary": descarga bytes crudos (PDF, Excel, imagen, ZIP).
     Se combina con file-write encoding="binary" para guardarlo. -->
<box-def name="reporte_pdf">
    <httpx-call url="https://api.miportal.com/reportes/mensual.pdf" response="binary"/>
</box-def>
<file-write path="downloads/reporte.pdf" encoding="binary">
    <box name="reporte_pdf"/>
</file-write>

<!-- response="stream": para archivos grandes (+50MB). Escribe directo a disco en chunks
     de 1MB. Requiere 'path'. Si falla, el archivo final nunca se crea. -->
<httpx-call url="https://cdn.miportal.com/dataset.csv.gz"
            response="stream"
            path="downloads/dataset.csv.gz"/>
```

#### Atributos y child tags

| Atributo | Default | Para qué |
|----------|---------|----------|
| `url` (req) | — | URL completa del request |
| `method` | `GET` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD` |
| `timeout` | `30000` | Timeout en milisegundos |
| `response` | `text` | `text` (string), `binary` (bytes), `stream` (a disco) |
| `path` | — | Destino en disco — obligatorio si `response="stream"` |
| `auto-cookies` | `false` | Mantener cookie jar entre llamadas de la sesión |

| Child tag | Para qué |
|-----------|----------|
| `<httpx-header name="...">valor</httpx-header>` | Agregar un header HTTP |
| `<httpx-param name="...">valor</httpx-param>` | Parámetro: query string en `GET`, body form-encoded en el resto |

Referencia detallada (cookies, `<httpx-close/>`, casos de uso por tipo de contenido) en
[`docs/guides/httpx-call.md`](docs/guides/httpx-call.md).

### Salida multi-formato declarativa

```xml
<!-- Cada record-save lee el mismo record en memoria y escribe un archivo distinto.
     'from' apunta al record por nombre; 'format' decide el writer; 'path' el destino. -->
<record-save from="propiedadesRecord" format="json" path="output/propiedades.json"/>
<record-save from="propiedadesRecord" format="csv" path="output/propiedades.csv" clean-data="true"/>
<record-save from="propiedadesRecord" format="ndjson" path="output/propiedades.ndjson"/>
<record-save from="propiedadesRecord" format="excel" path="output/propiedades.xlsx" sheet-name="Propiedades"/>
<record-save from="propiedadesRecord" format="parquet" path="output/propiedades.parquet"/>
```

Misma fuente, cinco formatos, sin código de pegamento. Referencia completa en
[`docs/guides/record-save.md`](docs/guides/record-save.md).

Opciones de forma de los datos:

- **`clean-data="true"`** — exporta solo filas, sin metadata embebida.
- **`allow-nested="true"`** — JSON/NDJSON mantienen los grupos anidados.
- **`allow-prefix="true"`** — claves planas con prefijo de grupo (`propiedad.title`).
- *Default:* claves cortas, strings saneados (sin saltos de línea que rompen CSV).

### Lenguaje de expresiones incorporado

Variables, aritmética, comparaciones, operadores lógicos y métodos de string encadenables. Los
métodos se invocan **dentro** de la interpolación `${ ... }`.

```xml
<!-- if evalúa la condición: la box 'precio_libro' tiene que existir, no estar vacía,
     y no ser la cadena '0'. Si pasa, se entra a la rama; si no, salta al <else>. -->
<if condition="${precio_libro.isNotEmpty()} and ${precio_libro} != '0'">
    <log>
        Precio válido: ${precio_libro} ${moneda.toUpperCase()}
    </log>
</if>
<else>
    <log>Fila descartada — precio vacío o cero</log>
</else>
```

Construir valores nuevos con `evaluate` (operaciones) y `compose` (interpolación de texto):

```xml
<!-- evaluate ejecuta una expresión aritmética y devuelve el resultado como número.
     Acá toma el valor actual del contador, le suma 1, y reasigna la box. -->
<box-def name="contador_libros">
    <evaluate>${contador_libros} + 1</evaluate>
</box-def>

<!-- compose es interpolación de texto pura: arma un string juntando literal + ${var}.
     Resultado típico: 'book-1', 'book-2', ... según el contador. -->
<box-def name="record_key">
    <compose>book-${contador_libros}</compose>
</box-def>
```

Métodos disponibles sobre strings: `isEmpty`, `isNotEmpty`, `toUpperCase`, `toLowerCase`, `trim`,
`length`, `contains`, `startsWith`, `endsWith`, `replace`, `toInt`, `toFloat`, `toBoolean`.

Evaluación con `simpleeval` (sin `eval()` nativo, sin acceso a `__builtins__`).

### Records estructurados

Schema, validación, deduplicación y metadata declaradas en el mismo XML.

```xml
<!-- record-create declara la "tabla" en memoria. 'collect-errors' significa que las filas
     inválidas no abortan el workflow: se acumulan para exportarlas aparte al final. -->
<record-create name="propiedadesRecord" record-validation="collect-errors">

    <!-- Un grupo agrupa campos relacionados. Cuando se exporta plano sin allow-prefix,
         los nombres se publican como title/price/...; con allow-nested se publican
         como propiedad.title, propiedad.price, ... -->
    <record-set-group name="propiedad" required="true">
        <!-- Cada record-set-field define un campo del schema: nombre, tipo y si es obligatorio.
             null-if-empty="true" convierte string vacío en null en lugar de fallar la validación. -->
        <record-set-field name="workflow_key" type="string" required="true"/>
        <record-set-field name="source" type="string" required="true"/>
        <record-set-field name="external_id" type="string" required="true"/>
        <record-set-field name="title" type="string" required="true"/>
        <record-set-field name="price" type="integer" required="true"/>
        <record-set-field name="currency" type="string" required="true"/>
        <record-set-field name="bedrooms" type="integer" required="false" null-if-empty="true"/>
        <record-set-field name="surface" type="decimal" required="false" null-if-empty="true"/>
        <record-set-field name="image_url" type="url" required="false" null-if-empty="true"/>
        <record-set-field name="source_url" type="url" required="true"/>
        <record-set-field name="scraped_at" type="datetime" required="false" null-if-empty="true"/>
    </record-set-group>

    <!-- record-key define qué hace única a cada fila. Si entran dos filas con la misma
         combinación (workflow_key + source + external_id), la segunda va a 'duplicates'. -->
    <record-key>
        <key-field name="workflow_key"/>
        <key-field name="source"/>
        <key-field name="external_id"/>
    </record-key>

    <!-- Journal append-only: cada record-add se escribe al instante en este NDJSON.
         Si el workflow crashea a mitad, ya quedó persistido lo que alcanzó a procesar. -->
    <record-journal path="output/run.journal.ndjson" fsync="false"/>

</record-create>
```

Cada fila se inserta con `<record-add>`. Los `record-add-field` reciben las boxes ya construidas:

```xml
<!-- record-add abre una transacción de fila contra el record destino.
     El runtime corre validación + tipado + deduplicación antes de aceptarla. -->
<record-add to="propiedadesRecord">
    <!-- El grupo debe coincidir con el declarado en el schema. -->
    <record-add-group name="propiedad">
        <!-- Cada record-add-field toma el valor de una box (vía ${...}) y lo asigna
             al campo del schema. El tipo se infiere/convierte según record-set-field. -->
        <record-add-field name="workflow_key">${workflow_key}</record-add-field>
        <record-add-field name="source">${source}</record-add-field>
        <record-add-field name="external_id">${id_propiedad}</record-add-field>
        <record-add-field name="title">${titulo_propiedad}</record-add-field>
        <record-add-field name="price">${precio_propiedad}</record-add-field>
        <record-add-field name="currency">${moneda_propiedad}</record-add-field>
        <record-add-field name="source_url">${url_detalle}</record-add-field>
    </record-add-group>
</record-add>
```

Incluye:

- Validación de schema por fila (`strict` o `collect-errors`).
- Deduplicación automática por `record-key` con exportación separada de duplicados.
- Journal NDJSON append-only que se escribe en vivo, sobrevive a crashes.
- Metadata privada por corrida: filas totales, completitud, duración, RAM, errores, OS, versión, session id.
- Metadata pública embebida donde el formato lo soporta (`_metadata` en JSON, hoja en Excel, nodo en XML).

#### Así se ve la data exportada

A partir del schema y del `record-add` de arriba, una fila pasa por validación, tipado y normalización.
La misma fila se exporta en distintas formas según los atributos de `record-save`.

**Default (`clean-data` activo, claves cortas, strings saneados)**

```xml
<record-save from="propiedadesRecord" format="json" path="output/propiedades.json" clean-data="true"/>
```

```json
[
    {
        "workflow_key": "properties-2026-05",
        "source": "books.toscrape.com",
        "external_id": "a-light-in-the-attic",
        "title": "A Light in the Attic",
        "price": 51,
        "currency": "GBP",
        "bedrooms": null,
        "surface": null,
        "image_url": null,
        "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "scraped_at": null
    }
]
```

**Con prefijo de grupo (`allow-prefix="true"`)** — útil cuando se va a hacer join con otras tablas:

```xml
<record-save from="propiedadesRecord" format="json" path="output/propiedades.json" allow-prefix="true"/>
```

```json
[
    {
        "propiedad.workflow_key": "properties-2026-05",
        "propiedad.source": "books.toscrape.com",
        "propiedad.external_id": "a-light-in-the-attic",
        "propiedad.title": "A Light in the Attic",
        "propiedad.price": 51,
        "propiedad.currency": "GBP",
        "propiedad.source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    }
]
```

**Anidado por grupo (`allow-nested="true"`)** — JSON/NDJSON conservan la estructura del schema:

```xml
<record-save from="propiedadesRecord" format="json" path="output/propiedades.json" allow-nested="true"/>
```

```json
[
    {
        "propiedad": {
            "workflow_key": "properties-2026-05",
            "source": "books.toscrape.com",
            "external_id": "a-light-in-the-attic",
            "title": "A Light in the Attic",
            "price": 51,
            "currency": "GBP",
            "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        }
    }
]
```

**El mismo record en CSV** (claves cortas, strings saneados, una fila por propiedad):

```csv
workflow_key,source,external_id,title,price,currency,bedrooms,surface,image_url,source_url,scraped_at
properties-2026-05,books.toscrape.com,a-light-in-the-attic,A Light in the Attic,51,GBP,,,,http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html,
```

**Con `include-metadata="true"`** se embebe la metadata pública (totales, hash del workflow, duración)
en el formato de salida — `_metadata` en JSON, hoja `metadata` en Excel, `<metadata>` en XML.

### Workflows reutilizables

Las funciones declaran su cuerpo en `<function-create>`. Los parámetros viajan vía
`<function-param>` dentro del `<function-call>` y aparecen en el scope de la función como
boxes normales (`${url_objetivo}`).

```xml
<!-- function-create registra la función bajo un nombre; no se ejecuta hasta que alguien
     llama con <function-call>. El cuerpo corre en su propio scope: las boxes que cree
     internamente no contaminan el scope del workflow que la llamó. -->
<function-create name="descargarYConvertir">

    <!-- Dentro del cuerpo, ${url_objetivo} viene del function-param que enviaron al llamarla. -->
    <box-def name="pagina_html">
        <httpx-call url="${url_objetivo}"/>
    </box-def>

    <!-- function-return define el valor que la función entrega al caller. Lo que esté
         envuelto acá (en este caso el resultado de convert-html-to-xml) sale como retorno. -->
    <function-return>
        <convert-html-to-xml>
            <box name="pagina_html"/>
        </convert-html-to-xml>
    </function-return>

</function-create>

<!-- function-call ejecuta la función ya creada y asigna su retorno a una box.
     function-param manda los argumentos por nombre: 'url_objetivo' aparece dentro del cuerpo. -->
<box-def name="pagina_xml">
    <function-call name="descargarYConvertir">
        <function-param name="url_objetivo">http://books.toscrape.com</function-param>
    </function-call>
</box-def>
```

### Unificar fuentes: CSV local + web en un mismo XML

Las fuentes son distintas en origen (un archivo en disco, una página web) pero **idénticas en
tratamiento**: una vez convertidas a XML se consultan con XPath de la misma forma. Esto permite
mezclar feeds, scrapers y APIs en un solo pipeline sin código de pegamento.

#### Paso 1 — Cargar un CSV local y poder consultarlo con XPath

`convert-csv-to-json` devuelve un array; `xmltodict` no acepta arrays crudos en la raíz de un
XML, así que el array se **envuelve en una clave intermedia** (`fila`) con `compose` antes de
pasarlo a `convert-json-to-xml`. Resultado: un `<propiedades>` con varias `<fila>` adentro,
listo para XPath.

```xml
<!-- 1. Leer el CSV desde el disco. file-read devuelve el contenido como texto UTF-8. -->
<box-def name="csv_raw">
    <file-read path="data/propiedades.csv"/>
</box-def>

<!-- 2. Convertir CSV → array JSON. La primera línea del CSV se usa como cabecera,
     y cada fila pasa a ser un objeto con clave por columna.
     Salida tipo: [{"id":"A001","nombre":"Casa Centro","precio":"1500000","moneda":"CLP"}, ...] -->
<box-def name="propiedades_json_array">
    <convert-csv-to-json>
        <box name="csv_raw"/>
    </convert-csv-to-json>
</box-def>

<!-- 3. Envolver el array bajo una clave intermedia 'fila'. compose interpola la box
     ya convertida a JSON y la inyecta como valor de la clave 'fila'. -->
<box-def name="propiedades_json_wrapped">
    <compose>{"fila": ${propiedades_json_array}}</compose>
</box-def>

<!-- 4. JSON → XML. El atributo root="propiedades" define la raíz del documento;
     cada item del array 'fila' del JSON se transforma en un nodo <fila> hermano. -->
<box-def name="propiedades_xml">
    <convert-json-to-xml root="propiedades">
        <box name="propiedades_json_wrapped"/>
    </convert-json-to-xml>
</box-def>
```

Cómo queda `propiedades_xml` después del paso 4 — un XML válido, recorrible por XPath igual que
si hubiera salido de scrapear una web:

```xml
<propiedades>
    <fila>
        <id>A001</id>
        <nombre>Casa Centro</nombre>
        <precio>1500000</precio>
        <moneda>CLP</moneda>
    </fila>
    <fila>
        <id>A002</id>
        <nombre>Depto Costa</nombre>
        <precio>2100000</precio>
        <moneda>CLP</moneda>
    </fila>
    <fila>
        <id>A003</id>
        <nombre>Casa Sur</nombre>
        <precio>990000</precio>
        <moneda>CLP</moneda>
    </fila>
</propiedades>
```

Ahora cualquier consulta XPath funciona sobre el CSV como si fuera HTML:

```xml
<!-- Selector simple: todos los nombres del CSV. -->
<box-def name="nombres_csv">
    <xpath-extract expression="//fila/nombre/text()">
        <box name="propiedades_xml"/>
    </xpath-extract>
</box-def>

<!-- Predicate de XPath: solo filas donde moneda='CLP'. -->
<box-def name="precios_clp">
    <xpath-extract expression="//fila[moneda='CLP']/precio/text()">
        <box name="propiedades_xml"/>
    </xpath-extract>
</box-def>

<!-- Iterar las filas del CSV como si fueran cualquier otra lista. -->
<loop item="fila_csv" index="numero">
    <loop-list>
        <xpath-extract expression="//fila">
            <box name="propiedades_xml"/>
        </xpath-extract>
    </loop-list>
    <loop-body>
        <box-def name="nombre">
            <xpath-extract expression="//nombre/text()">
                <box name="fila_csv"/>
            </xpath-extract>
        </box-def>
        <log>Propiedad ${numero} del CSV: ${nombre}</log>
    </loop-body>
</loop>
```

#### Paso 2 — Descargar una página web y aplicar el mismo patrón

La fuente cambia (HTTP en vez de disco) y el conversor también (`convert-html-to-xml` en vez de
`convert-csv-to-json` + `convert-json-to-xml`). El resto es el mismo lenguaje: `xpath-extract`
sobre una box que contiene XML.

```xml
<box-def name="pagina_html">
    <httpx-call url="http://books.toscrape.com"/>
</box-def>

<box-def name="pagina_xml">
    <convert-html-to-xml>
        <box name="pagina_html"/>
    </convert-html-to-xml>
</box-def>

<box-def name="libros_web">
    <xpath-extract expression="//article[@class='product_pod']">
        <box name="pagina_xml"/>
    </xpath-extract>
</box-def>
```

#### Paso 3 — Insertar las dos fuentes en el mismo record

A esta altura tenemos dos listas en boxes:

- `propiedades_xml` → filas del CSV local.
- `libros_web` → tarjetas extraídas de la web.

Cada una se itera con su propio `loop`, y ambos `loop-body` apuntan al mismo `record-add to="..."`.
El schema se encarga de validar y tipar; el `record-key` deduplica si una fila llegara dos veces.

Asumimos que `catalogoUnificado` ya fue declarado antes con `<record-create>` (mismo patrón que
en [Records estructurados](#records-estructurados): un grupo `item` con campos `source`,
`external_id`, `title`, `price` y un `record-key` que combine `source` + `external_id`).

```xml
<!-- Recorrer las filas del CSV y agregarlas al record común. -->
<loop item="fila_csv" index="i_csv">
    <loop-list>
        <xpath-extract expression="//fila">
            <box name="propiedades_xml"/>
        </xpath-extract>
    </loop-list>
    <loop-body>

        <box-def name="id_csv">
            <xpath-extract expression="//id/text()">
                <box name="fila_csv"/>
            </xpath-extract>
        </box-def>
        <box-def name="nombre_csv">
            <xpath-extract expression="//nombre/text()">
                <box name="fila_csv"/>
            </xpath-extract>
        </box-def>
        <box-def name="precio_csv">
            <xpath-extract expression="//precio/text()">
                <box name="fila_csv"/>
            </xpath-extract>
        </box-def>

        <!-- source="csv" deja la huella de origen en el record. -->
        <record-add to="catalogoUnificado">
            <record-add-group name="item">
                <record-add-field name="source">csv</record-add-field>
                <record-add-field name="external_id">${id_csv}</record-add-field>
                <record-add-field name="title">${nombre_csv}</record-add-field>
                <record-add-field name="price">${precio_csv}</record-add-field>
            </record-add-group>
        </record-add>

    </loop-body>
</loop>

<!-- Recorrer las tarjetas de la web y agregarlas al MISMO record. -->
<loop item="tarjeta" index="i_web">
    <loop-list>
        <box name="libros_web"/>
    </loop-list>
    <loop-body>

        <box-def name="titulo_web">
            <xpath-extract expression="//h3/a/@title">
                <box name="tarjeta"/>
            </xpath-extract>
        </box-def>
        <box-def name="precio_web">
            <xpath-extract expression="//p[@class='price_color']/text()">
                <box name="tarjeta"/>
            </xpath-extract>
        </box-def>

        <record-add to="catalogoUnificado">
            <record-add-group name="item">
                <record-add-field name="source">books.toscrape.com</record-add-field>
                <record-add-field name="external_id">web-${i_web}</record-add-field>
                <record-add-field name="title">${titulo_web}</record-add-field>
                <record-add-field name="price">${precio_web}</record-add-field>
            </record-add-group>
        </record-add>

    </loop-body>
</loop>

<!-- Un único record-save genera el catálogo unificado: filas del CSV + filas de la web,
     todas pasando por el mismo schema, deduplicación y journal. -->
<record-save from="catalogoUnificado" format="json" path="output/catalogo.json" clean-data="true"/>
<record-save from="catalogoUnificado" format="csv" path="output/catalogo.csv" clean-data="true"/>
```

**Idea clave:** una vez que la fuente está en una box que contiene XML — venga de un CSV, una API
JSON, un HTML, un Excel o lo que sea — el resto del workflow no distingue el origen. XPath sirve
para todo, los records reciben filas desde donde sea, y la salida queda unificada en el formato
que el caso de uso pida.

### Pipeline completo (extracto)

Patrón típico: paginar, extraer, normalizar, agregar al record y exportar al final. Cada paso lee
la box anterior, cada `record-add` cierra la fila, y el último bloque persiste todo a disco.

```xml
<!-- 0. Estado inicial del bucle paginado:
     - hay_pagina_siguiente: bandera de salida (true mientras quede catálogo por recorrer).
     - pagina_actual: contador que se incrementa al inicio de cada vuelta.
     - url_pagina: URL que se va a descargar en esta iteración (arranca en page-1). -->
<box-def name="hay_pagina_siguiente">true</box-def>
<box-def name="pagina_actual">0</box-def>
<box-def name="url_pagina">http://books.toscrape.com/catalogue/page-1.html</box-def>

<!-- while corre mientras la condición sea verdadera. max-loops es un seguro:
     aunque el sitio devuelva un loop infinito, el workflow corta a las 60 vueltas. -->
<while condition="${hay_pagina_siguiente.toBoolean()}" max-loops="60">

    <!-- Avanzar el contador antes de procesar (queda en 1 en la primera vuelta, 2 en la segunda...). -->
    <box-def name="pagina_actual">
        <evaluate>${pagina_actual} + 1</evaluate>
    </box-def>

    <log>Scrapeando página ${pagina_actual}: ${url_pagina}</log>

    <!-- 1. Descargar el HTML de la página actual y limpiarlo a XML válido para XPath. -->
    <box-def name="pagina_html">
        <httpx-call url="${url_pagina}"/>
    </box-def>

    <box-def name="pagina_xml">
        <convert-html-to-xml>
            <box name="pagina_html"/>
        </convert-html-to-xml>
    </box-def>

    <!-- 2. Sacar la lista de tarjetas de libro de la página. -->
    <box-def name="tarjetas_libros">
        <xpath-extract expression="//article[@class='product_pod']">
            <box name="pagina_xml"/>
        </xpath-extract>
    </box-def>

    <!-- 3. Por cada tarjeta: extraer campos y persistir como fila del record. -->
    <loop item="tarjeta_libro" index="numero">

        <loop-list>
            <box name="tarjetas_libros"/>
        </loop-list>

        <loop-body>

            <!-- Cada xpath-extract recibe la tarjeta actual y saca título y precio. -->
            <box-def name="titulo_libro">
                <xpath-extract expression="//h3/a/@title">
                    <box name="tarjeta_libro"/>
                </xpath-extract>
            </box-def>

            <box-def name="precio_libro">
                <xpath-extract expression="//p[@class='price_color']/text()">
                    <box name="tarjeta_libro"/>
                </xpath-extract>
            </box-def>

            <!-- record-add inserta una fila contra el schema. record_key se compone con la
                 página y el índice para que sea único por libro y deduplicación funcione. -->
            <record-add to="librosRecord">
                <record-add-group name="libro">
                    <record-add-field name="record_key">book-${pagina_actual}-${numero}</record-add-field>
                    <record-add-field name="titulo">${titulo_libro}</record-add-field>
                    <record-add-field name="precio">${precio_libro}</record-add-field>
                </record-add-group>
            </record-add>

        </loop-body>

    </loop>

    <!-- 4. Resolver paginación: leer el href del botón "next" si existe.
         Si no aparece, ya recorrimos todo el catálogo y salimos del while. -->
    <box-def name="href_siguiente">
        <xpath-extract expression="//li[@class='next']/a/@href">
            <box name="pagina_xml"/>
        </xpath-extract>
    </box-def>

    <if condition="${href_siguiente.isEmpty()}">
        <!-- Sin botón "next": cortamos el while en la próxima evaluación. -->
        <box-def name="hay_pagina_siguiente">false</box-def>
    </if>
    <else>
        <!-- Hay otra página: armamos la URL absoluta y reasignamos url_pagina. -->
        <box-def name="url_pagina">
            <compose>http://books.toscrape.com/catalogue/${href_siguiente}</compose>
        </box-def>
    </else>

    <!-- Pausa cortés entre páginas para no estresar al servidor. -->
    <sleep ms="1000"/>

</while>

<!-- 5. Al salir del while, el record ya tiene todas las filas en memoria + journal.
     Persistir el resultado completo en distintos formatos:
       - NDJSON con clean-data: una línea por fila, sin metadata, ideal para streaming.
       - CSV con clean-data: tabular puro para hojas de cálculo o BI.
       - JSON con include-metadata: snapshot con _metadata embebida para auditar. -->
<record-save from="librosRecord" format="ndjson" path="output/libros.ndjson" clean-data="true"/>
<record-save from="librosRecord" format="csv" path="output/libros.csv" clean-data="true"/>
<record-save from="librosRecord" format="json" path="output/libros.json" include-metadata="true"/>
```

Fuente real: [`workflows/all_books_pages.xml`](workflows/all_books_pages.xml) — paginación completa
del catálogo `books.toscrape.com`, definición del `FRecord`, journal NDJSON, ocho `record-save` y
un `RUN_MANIFEST.JSON` por corrida.

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

**Funcional y listo para usarse.** El core está implementado y testeado: parser, runtime, sistema de records,
expresiones, hands integrados de red, archivos, conversiones, control de flujo y exportación
multi-formato. Podés armar pipelines reales hoy con los workflows en [`workflows/`](workflows/) y
[`examples/`](examples/).

El framework sigue **abierto a crecer**: nuevas capacidades se suman como hands (registradas en el
runtime) sin reescribir el motor. Lo planificado a futuro (PDF nativo, lectura de Excel/JSON, IA,
navegador completo, storage en la nube, plugin del editor, API REST) está en
[**En desarrollo y próximas funcionalidades**](#en-desarrollo-y-próximas-funcionalidades) y en
[`docs/roadmap.md`](docs/roadmap.md).

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
