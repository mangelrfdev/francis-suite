# `<record-save>` — referencia (formatos implementados)

Hand que persiste un `FRecord` en disco.

**Diseño avanzado** (metadata-placement por formato, plantillas txt libres, etc.): [record-save-formats.md](record-save-formats.md).

---

## Ejemplo completo: `examples/books_all_pages.xml`

El ejemplo **books to scrape** (paginación + HTTP) además guarda cada libro en un **`FRecord`** (`booksRecords`) y, **al terminar el scrape**, escribe **los mismos datos** en **ocho archivos** bajo `output/`:

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

En el workflow: `<record-create name="booksRecords">` con grupo `book` (`record_key`, `titulo`, `precio`); en el loop, `record_key` = `book-${contador}`; al final, ocho `<record-save>` seguidos apuntando al mismo `from="booksRecords"`.

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
| `session_id` | `<Records>` | `session.id` (UUID de la corrida) | `xml-include-root-session-id="true"` o `<xml-root-system name="session_id"/>` |
| `francis_suite_version` | `<Records>` | Constante del framework en código | `xml-include-root-francis-version` o `<xml-root-system name="francis_suite_version"/>` |
| `exported_at` | `<Records>` | Marca UTC ISO al guardar el archivo | `xml-include-root-exported-at` o `<xml-root-system name="exported_at"/>` |
| `recordKey` | `<record>` | Si hay `<record-key>` — hash SHA-256 | `xml-include-record-key` (default true) |

**Custom (lo que quieras):** hijos `<xml-root-attr>` / `<xml-root-attr name="client">${cliente}</xml-root-attr>` — valores libres; los **integrados** de la tabla se aplican después y **pisan** el mismo nombre si ambos están activos (los de sistema tienen prioridad para `workflow`, `total_records`, etc.).

**Atributos integrados desde el XML del workflow:** también podés usar `<xml-root-system name="session_id"/>` (sin cuerpo) en lugar de flags booleanos.

Ejemplo (mismos datos, dos filas ficticias):

```xml
<?xml version='1.0' encoding='UTF-8'?>
<Records workflow="books_all_pages" total_records="2">
  <record workflow="books_all_pages" recordKey="…">
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

Página con `<title>` / `<h1>` según `html-title`, tabla con columnas aplanadas.

### `txt`

Cabecera TSV + filas (separador tabulador, no espacios).

### `excel`

Hoja principal con columnas `book.record_key`, `book.titulo`, `book.precio`, etc.

### `parquet`

Columnas aplanadas; abrir con Pandas, Polars o pyarrow.

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

`path` puede usar `${variables}` si resolvés rutas por entorno o parámetros.

---

## Formatos

| `format` | Descripción breve |
|----------|-------------------|
| `json` | Un archivo JSON: lista de objetos anidados (o `_metadata` + `data` si `include-metadata="true"`). |
| `csv` | Filas aplanadas con claves por punto; metadata pública como líneas `# name: value` al inicio si aplica. |
| `ndjson` | Una línea JSON por fila; opcionalmente primera línea de metadata. |
| `xml` | Raíz `<Records workflow="…" total_records="…">`, un `<record>` por fila; anidación según grupos del schema. Si hay `<record-key>`, atributo `recordKey` = hash SHA-256 completo. |
| `html` | Página HTML con tabla (columnas = filas aplanadas); sección opcional de metadata pública. |
| `txt` | Texto **TSV** (tab-separated): cabecera + filas; líneas `#` de metadata si `include-metadata` y schema público. |
| `excel` / `xlsx` | Libro Excel (openpyxl); hoja principal con columnas aplanadas; segunda hoja opcional para metadata pública. |
| `parquet` | Tabla columnar (pyarrow), filas aplanadas; compresión snappy. |

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

Array o líneas; CSV con cabecera y filas aplanadas. Más detalle en las muestras de arriba y en [record-save-formats.md](record-save-formats.md).

### `xml`

- Declaración XML UTF-8, pretty-print.
- Bloque opcional `<public-metadata>` con `<field name="…">` si `include-metadata` y hay metadata pública.

### `html`

- Estilos mínimos inline en `<head>`; tabla en `<body>`.
- Metadata pública en `<section>` con tabla nombre/valor si aplica.

### `txt`

- Separador: tabulador (`\t`). Primera línea = nombres de columnas aplanadas.

### `excel`

- Primera fila = cabeceras; datos debajo.
- Con metadata pública: segunda hoja con columnas `name`, `value`.

### `parquet`

- Sin metadata embebida en esta versión (usar `json`/`ndjson` o archivo aparte si hace falta).
- Columnas inferidas desde la unión de claves aplanadas.

---

## Errores comunes

- Record inexistente o no es `FRecord` → error del hand.
- Formato desconocido → `[RECORD] unsupported format '…'`.
- Record vacío → no se escribe archivo (mismo criterio que csv).
