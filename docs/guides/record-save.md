# `<record-save>` — referencia (formatos implementados)

Hand que persiste un `FRecord` en disco.

**Diseño avanzado** (metadata-placement por formato, plantillas txt libres, etc.): [record-save-formats.md](record-save-formats.md).

---

## Journal incremental (`record-journal`) — NDJSON en vivo

**Opcional**, bajo `<record-create>`: un archivo NDJSON **append-only** que se va escribiendo **durante** el workflow (no sustituye a `<record-save>`).

| Pieza | `_type` |
|-------|---------|
| Apertura (si el archivo está vacío al crear el record) | `journal_header` — `session_id`, `workflow_name`, `record_name`, `started_at`, `francis_suite_version`, `status` inicial. |
| Cada fila aceptada por `record-add` (tras normalizar; si `record-key` deduplica, **no** se escribe línea) | `record` — `data` (fila aplanada), `row_index`, `session_id`, `status`, `workflow_name`, versión. |
| Al terminar la sesión (éxito o fallo; en el `finally` del runtime) | `process` — `status` (`completed` / `failed` / …), `rows_committed`, `error` si hubo excepción, `finished_at`. |

Atributos del tag: `path` (obligatorio; `fsync="true|false"` para `flush` + `fsync` tras cada línea).

**Uso típico:** path distinto al NDJSON del `<record-save>` (p. ej. `output/run.journal.ndjson` **vivo** vs `output/run.ndjson` **export final** con líneas `_type: export` + datos). Si el proceso corta antes de los `record-save`, el journal sigue siendo evidencia útil.

---

## `<record-save-duplicates>` — filas con clave duplicada

Hand separado de `<record-save>`. Exporta solo las filas que **no** entraron al `FRecord` principal porque **repetían** la misma `<record-key>` que una fila ya aceptada (segunda y siguientes ocurrencias).

| | `<record-save>` | `<record-save-duplicates>` |
|--|-----------------|----------------------------|
| Filas exportadas | Únicas por clave (primera ocurrencia) | Duplicados detectados por clave |
| Requisito | — | Debe existir `<record-key>` en el mismo `<record-create>` |
| `include-metadata` | Opcional (`true` / `false`) | **No soportado** con valor `true` — la metadata pública de sesión va en `<record-save>` / `<record-save-metadata>` |

Si no hubo duplicados, el hand **no escribe** archivo (mensaje en consola y sesión sigue).

**Ejemplo**

```xml
<record-save from="booksRecords" format="ndjson" path="output/books.ndjson" include-metadata="false"/>
<record-save-duplicates from="booksRecords" format="parquet" path="output/books_duplicates.parquet"/>
```

Los mismos `format` y atributos de serialización que `<record-save>` donde apliquen (p. ej. `sheet-name`, `html-title`, flags `xml-include-*`), excepto `include-metadata="true"`.

---

## `record-validation` y `<record-save-validation-errors>`

En **`<record-create>`**, atributo opcional **`record-validation`**:

| Valor | Comportamiento |
|-------|----------------|
| **`strict`** (default) | Si un `record-add` no puede normalizar (tipo inválido, required vacío, etc.), la sesión **falla** como hasta ahora. |
| **`collect-errors`** | Esa fila **no** entra al record; se guarda internamente con el mensaje de error; la corrida **sigue**. |

**`<record-save-validation-errors from="..." format="..." path="..."/>`** exporta esas filas rechazadas (columnas `validation_error` + `raw_*` por cada campo del `record-add`). Si no hubo errores, **no escribe** archivo. No soporta `include-metadata="true"` — la metadata pública va en `<record-save>`.

En **metadata privada** automática aparecen **`filas_duplicadas_por_clave`** y **`filas_rechazadas_validacion`** (además de los contadores ya existentes).

---

## Metadatos de exportación (`record-export-*`)

Declarás **pares clave/valor** (y valores de sistema) **una vez**, como **hijos de `<record-create>`** (junto con grupos, metadata, record-key, etc.). Cada `<record-save>` solo elige `format` y `path`: el mismo record puede volcarse a varios formatos en la misma corrida y los extras se **serializan donde el formato lo permita**; si un formato no tiene canal para eso, **no se escriben** (no hay error; el archivo de datos igual se genera).

**Tags canónicos** (bajo `<record-create>`)

| Tag | Rol |
|-----|-----|
| `<record-export-attr name="..." required="false" show-attribute="true">valor</record-export-attr>` | Clave/valor libre; `name` y el cuerpo se resuelven al **guardar** con `engine.resolve()` (incluye `${...}`). `required` (default `false`): si es `true` y el valor queda vacío al guardar, falla. `show-attribute` (default `true`): si es `false` y la corrida se considera **exitosa** para export, la clave no se emite; si la sesión **no** terminó en éxito, el valor real **sí** se emite (para diagnóstico). |
| `<record-export-root-attr name="..." …>valor</record-export-root-attr>` | Igual resolución que `record-export-attr`, pero pensado en **raíz** de export: va a `_export` en JSON/NDJSON y a atributos de `<Records>` en XML. |
| `<record-export-system name="session_id"/>` | Incluye `session_id` de la corrida (UUID). Equivalente extra a `xml-include-root-session-id="true"` en `<record-save>`. |
| `<record-export-system name="francis_suite_version"/>` | Constante de versión del framework. |
| `<record-export-system name="exported_at"/>` | Marca UTC ISO-8601 al momento de guardar. |
| `<record-export-system name="total_records"/>` | Número de filas al momento de guardar (string). |
| `<record-export-system name="status_process"/>` | Estado de la sesión (`completed`, `failed`, …). En el **último** hand de `<francis-workflow>`, el valor exportado puede ser `completed` aunque el estado interno aún sea `running` durante el `record-save`. |

**Alias legacy (misma semántica):** `<xml-root-attr>`, `<xml-root-system>` bajo `<record-create>`. El prefijo “xml” es histórico; **no** están limitados a `format="xml"`.

**Solo XML (no se mezclan con JSON/CSV/NDJSON):** bajo `<record-create>`,

- `<record-xml-root-attr name="..." required="false">valor</record-xml-root-attr>` — atributos en `<Records>` **solo** en XML (no entran en `_export` JSON). Equivalente “solo XML” frente a `record-export-root-attr` (multi-formato).
- `<record-xml-record-attr name="..." from-field="book.record_key" required="false"/>` — atributo en **cada** `<record>` con valor tomado del campo aplanado (misma notación que el schema). Alias canónico: `<record-export-row-attr>` (misma semántica). Sin `from-field`, el cuerpo del tag es un valor **estático** repetido en todas las filas. `required` por atributo: si se omite, equivale a `false`; si es `true` y el valor queda vacío al guardar, falla la sesión.

**Solo en `<record-save>` (serialización XML):** `<xml-record-attr>` — atributos estáticos extra en cada `<record>` (se fusionan al final; solo `format="xml"`).

Los flags booleanos en `record-save` (`xml-include-root-session-id`, etc.) **suman** a lo declarado en el record; si ya fijaste una clave en `record-export-attr`, **no** la sobrescribe el integrado.

**Compatibilidad por formato** (`_export` / metadata de export): los valores se **normalizan** para el destino (p. ej. saltos de línea en valores no se dejan crudos en CSV/comentarios/attrs XML). En **parquet**, si el JSON de export supera un umbral de tamaño, se **omite** el bloque `francis_export` en metadata **pero** las **columnas de datos** siguen igual. Los atributos **solo XML** (`record-xml-root-attr`, `record-xml-record-attr`) **no** se mezclan en JSON/CSV/NDJSON.

**JSON y envoltorio `_export`:** si **no** declaraste nada que rellene el bloque de export “flat” (custom + system + root multi-formato), el JSON puede ser **solo** el array de filas (comportamiento antiguo). Si declaraste export pero **todas** las claves quedan omitidas (p. ej. `show-attribute="false"` en éxito), el archivo puede ser `{ "_export": {}, "data": [ ... ] }` para mantener el contrato.

**Escritura atómica:** salidas de texto (json, ndjson, csv, html, txt, metadata) y XML usan archivo temporal en el mismo directorio y `replace`; excel y parquet escriben a `.tmp` y reemplazan.

**Dónde se escribe cada formato**

| `format` | Dónde van las claves de exportación |
|----------|--------------------------------------|
| `json` | Objeto `_export` en el mismo archivo (junto con `data` y, si aplica, `_metadata`). |
| `ndjson` | Primera línea: `{"_type":"export", ...}`. |
| `csv`, `txt` | Líneas `# clave: valor` antes de la cabecera de columnas. |
| `html` | Sección con `<h2>Export</h2>` y tabla nombre/valor. |
| `excel` / `xlsx` | Hoja **Export** (columnas `name`, `value`). |
| `parquet` | Metadata de tabla PyArrow: clave `francis_export` (JSON UTF-8). |
| `xml` | Atributos en el elemento raíz `<Records>` (junto con `workflow`, `total_records`, etc.). |

**Llamada API (Python):** `FRecord.save(..., export_augmentation={"client": "acme", ...})`. Con `format="xml"` y sin `export_augmentation`, los flags `xml-include-root-*` siguen rellenando `session_id` / `francis_suite_version` / `exported_at` en el dict interno.

---

## Ejemplo completo: `examples/books_all_pages.xml`

El ejemplo **books to scrape** (paginación + HTTP) además guarda cada libro en un **`FRecord`** (`booksRecords`). Opcionalmente puede declararse `<record-journal path="…"/>` para un NDJSON **incremental** durante el scrape. **Al terminar** el scrape, el mismo record se exporta con varios `<record-save>` — **ocho archivos** de salida final bajo `output/` (más el journal si está declarado):

| Archivo | `format` |
|---------|----------|
| `output/books.json` | `json` |
| `output/books.csv` | `csv` |
| `output/books.ndjson` | `ndjson` |
| `output/books.xml` | `xml` |
| `output/books.html` | `html` (`html-title="Books to Scrape"`) |
| `output/books.txt` | `txt` (TSV) |
| `output/books.xlsx` | `excel` (`sheet-name="Libros"`) |
| `output/books.parquet` | `parquet` |

**Cómo correrlo** (requiere red; puede tardar varios minutos):

```bash
francis-suite run examples/books_all_pages.xml
```

En el workflow: `<record-create name="booksRecords">` incluye los hijos `record-export-*` una vez; grupo `book` (`record_key`, `titulo`, `precio`); en el loop, `record_key` = `book-${contador}`; al final, ocho `<record-save>` mínimos (solo `format` y `path`) al mismo `from="booksRecords"`.

El ejemplo añade **`record-xml-root-attr`** / **`record-xml-record-attr`** (solo afectan a `output/books.xml`): p. ej. `dataset` en la raíz e `id` por fila desde `book.record_key`. **`examples/all_books_pages.xml`** declara además `url` en cada `<record>` desde `book.url_libro` (`required` omitido → `false`), **`record-journal`** hacia `output/all_books_pages.journal.ndjson` (vivo) y los **mismos** ocho `record-save` con prefijo `all_books_pages.*`.

El listado plano **`output/todos_los_libros.txt`** sigue generándose como antes (misma corrida, otro consumo).

---

## Muestras de salida (mismos datos, dos filas ficticias)

Ilustrativo: una fila real tiene `book.record_key`, `book.titulo`, `book.precio` aplanados donde aplique.

### `json`

```json
[
  {
    "book": {
      "record_key": "book-1",
      "titulo": "A Light in the ...",
      "precio": "£51.77"
    }
  },
  {
    "book": {
      "record_key": "book-2",
      "titulo": "Tipping the Velvet",
      "precio": "£53.74"
    }
  }
]
```

### `csv`

```csv
book.record_key,book.titulo,book.precio
book-1,A Light in the ...,£51.77
book-2,Tipping the Velvet,£53.74
```

### `ndjson`

```ndjson
{"book":{"record_key":"book-1","titulo":"A Light in the ...","precio":"£51.77"}}
{"book":{"record_key":"book-2","titulo":"Tipping the Velvet","precio":"£53.74"}}
```

### `xml`

Raíz `<Records>` y un `<record>` por fila. Atributos **integrados** (todos se pueden apagar con flags):

| Atributo | Dónde | Origen | Activar / omitir |
|----------|--------|--------|-------------------|
| `workflow` | `<Records>`, `<record>` | `session.workflow_name` (stem del XML al correr con CLI) | Flags `xml-include-root-workflow`, `xml-include-record-workflow` (default true) |
| `total_records` | `<Records>` | **Siempre** `len(rows)` — calculado en código, nunca manual | `xml-include-root-total-records` (default true) |
| `session_id` | `<Records>` | `session.id` (UUID de la corrida) | En **record-create:** `<record-export-system name="session_id"/>` (alias `<xml-root-system>`). En **record-save:** `xml-include-root-session-id="true"` |
| `francis_suite_version` | `<Records>` | Constante del framework en código | **record-create:** `<record-export-system name="francis_suite_version"/>`. **record-save:** `xml-include-root-francis-version` |
| `exported_at` | `<Records>` | Marca UTC ISO al guardar el archivo | **record-create:** `<record-export-system name="exported_at"/>`. **record-save:** `xml-include-root-exported-at` |
| `recordKey` | `<record>` | Si hay `<record-key>` — hash SHA-256 | `xml-include-record-key` en **record-save** (default true) |

**Custom (multi-formato):** `<record-export-attr>` bajo **record-create** (o alias `<xml-root-attr>`). Los atributos integrados de la tabla se aplican al serializar; si chocan el nombre con un `record-export-attr`, **no** sobrescribe el valor declarado en create.

**Solo XML:** `<record-xml-root-attr>` y `<record-xml-record-attr>` (ver sección «Metadatos de exportación» arriba) — atributos en la raíz y en cada `<record>` **independientes** del contenido anidado (`<book>`, etc.).

Ejemplo (mismos datos, dos filas ficticias; con `record-xml-*` como en `books_all_pages.xml`):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<Records dataset="books_catalog" workflow="books_all_pages" total_records="2">
  <record workflow="books_all_pages" recordKey="…" id="book-1">
    <book>
      <record_key>book-1</record_key>
      <titulo>A Light in the ...</titulo>
      <precio>£51.77</precio>
    </book>
  </record>
  <!-- … -->
</Records>
```

### `html`

Página con `<title>` / `<h1>` según `html-title`, tabla con columnas aplanadas; si hay `record-export-*`, sección **Export** encima de la tabla de datos.

### `txt`

Cabecera TSV + filas (separador tabulador, no espacios); líneas `#` opcionales para metadata pública y para claves de exportación.

### `excel`

Hoja principal con columnas aplanadas; hoja **Metadata** si `include-metadata` y schema público; hoja **Export** si hay `record-export-*`.

### `parquet`

Columnas aplanadas; metadata de exportación en el esquema de tabla (`francis_export`). Abrir con Pandas, Polars o pyarrow.

---

## Cuándo usar cada formato (orientativo)

| Formato | Suele servir para |
|---------|-------------------|
| `json` | APIs, apps, anidamiento legible |
| `csv` | Excel, Sheets, abrir en cualquier lado |
| `ndjson` | pipelines, BigQuery, una fila = un JSON |
| `xml` | integraciones legacy, SAP, B2B |
| `html` | reporte humano rápido en el navegador |
| `txt` | TSV para pegar en hojas de cálculo sin Excel |
| `excel` | entregar a personas no técnicas |
| `parquet` | análisis masivo, Pandas/Polars/Spark |

---

## Fragmento XML: varios formatos en el mismo workflow

```xml
<record-save from="booksRecords" format="json"     path="output/books.json"/>
<record-save from="booksRecords" format="csv"      path="output/books.csv"/>
<record-save from="booksRecords" format="ndjson"   path="output/books.ndjson"/>
<record-save from="booksRecords" format="xml"      path="output/books.xml"/>
<record-save from="booksRecords" format="html"      path="output/books.html" html-title="Books to Scrape"/>
<record-save from="booksRecords" format="txt"      path="output/books.txt"/>
<record-save from="booksRecords" format="excel"    path="output/books.xlsx" sheet-name="Libros"/>
<record-save from="booksRecords" format="parquet"  path="output/books.parquet"/>
```

`examples/books_all_pages.xml` declara `record-export-*` y `record-xml-*` dentro de `<record-create>`. `examples/all_books_pages.xml` añade `case_key` con `${case_key}` en `record-export-attr` y `record-xml-record-attr` para `id` / `url` (ver «Metadatos de exportación» arriba).

`path` puede usar `${variables}` si resolvés rutas por entorno o parámetros.

---

## Formatos

| `format` | Descripción breve |
|----------|-------------------|
| `json` | Lista de objetos o envoltorio con `data` / `_metadata` / `_export` según flags; ver sección «Metadatos de exportación» arriba. |
| `csv` | Filas aplanadas con claves por punto; metadata pública y claves de exportación como líneas `# name: value` al inicio si aplica. |
| `ndjson` | Primera línea opcional `export` o `metadata`, luego una línea JSON por fila. |
| `xml` | Raíz `<Records …>`, un `<record>` por fila; attrs declarativos con `record-xml-root-attr` / `record-xml-record-attr` (solo XML). Si hay `<record-key>`, atributo `recordKey` = hash SHA-256 completo. |
| `html` | Página HTML con tabla (columnas = filas aplanadas); secciones opcionales Export y metadata pública. |
| `txt` | Texto **TSV** (tab-separated): cabecera + filas; líneas `#` de metadata y/o exportación si aplica. |
| `excel` / `xlsx` | Libro Excel (openpyxl); hoja de datos; hojas opcionales Metadata y Export. |
| `parquet` | Tabla columnar (pyarrow), filas aplanadas; compresión snappy; metadata opcional `francis_export`. |

Los nombres de `format` son **insensibles a mayúsculas**. `excel` y `xlsx` son equivalentes.

---

## Atributos

| Atributo | Obligatorio | Notas |
|----------|-------------|-------|
| `from` | Sí | Nombre del record (shared-box). |
| `format` | Sí | Uno de la tabla anterior. |
| `path` | Sí | Ruta de salida; soporta `${variables}`. |
| `include-metadata` | No | `true` / `false` (default `false`). Metadata **pública** declarada en `<record-metadata>`. |
| `sheet-name` | No | Solo **excel**: nombre de la hoja de datos (default `Data`; máx. 31 caracteres en Excel). |
| `metadata-sheet-name` | No | Solo **excel**: hoja para metadata pública (default `Metadata`). |
| `html-title` | No | Solo **html**: título de página y `<h1>` (default: nombre del workflow). |

Atributos de texto pasan por `engine.resolve()` donde aplica.

---

## Comportamiento por formato (resumen)

### `json` / `ndjson` / `csv`

Array o líneas; CSV con cabecera y filas aplanadas. Con `record-export-*`, JSON incluye `_export`; NDJSON antepone línea `export`. Más detalle arriba y en [record-save-formats.md](record-save-formats.md).

### `xml`

- Declaración XML UTF-8, pretty-print.
- Bloque opcional `<public-metadata>` con `<field name="…">` si `include-metadata` y hay metadata pública.

### `html`

- Estilos mínimos inline en `<head>`; tabla en `<body>`.
- Metadata pública en `<section>` con tabla nombre/valor si aplica.
- Claves de exportación en `<section class="francis-export">` si aplica.

### `txt`

- Separador: tabulador (`\t`). Primera línea = nombres de columnas aplanadas (tras líneas `#` de metadata/export).

### `excel`

- Primera fila = cabeceras; datos debajo.
- Con metadata pública: hoja **Metadata** con columnas `name`, `value`.
- Con `record-export-*`: hoja **Export** con columnas `name`, `value`.

### `parquet`

- Metadata de tabla PyArrow: clave `francis_export` (JSON UTF-8) cuando hay exportación.
- Columnas inferidas desde la unión de claves aplanadas.

---

## Errores comunes

- Record inexistente o no es `FRecord` → error del hand.
- Formato desconocido → `[RECORD] unsupported format '…'`.
- Record vacío → no se escribe archivo (mismo criterio que csv).
