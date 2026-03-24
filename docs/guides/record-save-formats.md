# record-save — Formatos, metadata y atributos (diseño)

Documento de **diseño** para extender `record-save` más allá de json / csv / ndjson.
Se va a ir **ajustando** cuando exista implementación; la intención es que la idea no se pierda.

**Implementado hoy:** [record-save.md](record-save.md) (atributos y comportamiento real de json / csv / ndjson).

**Relacionado:** `record-save-metadata` (metadata **privada** sin rows), metadata pública en `record-create` (`<record-metadata>`), roadmap (formatos pendientes), tests golden / comparación de contenido (pendiente, ver sección al final).

---

## Tres capas (mental model)

| Capa | Qué es | Dónde suele ir |
|------|--------|----------------|
| **Datos de negocio** | Rows / grupos del schema (`record-add`) | Siempre en el archivo principal de datos |
| **Metadata pública** | La que el usuario declara en `<record-metadata>` si quiere exponerla | Opcional; según formato: embebida, otra hoja, otro archivo, primera línea, etc. |
| **Metadata privada / operativa** | Mucha más data (sesión, tiempos, RAM, errores, etc.) | **No** mezclar con el entregable “cliente” por defecto. El **runtime** guarda un JSON por cada `FRecord` al terminar la sesión en `sessions/<session_id>/` (sin depender del XML). El hand **`<record-save-metadata>`** sigue sirviendo para **otra ruta** si la necesitás. Variable de entorno `FRANCIS_AUTO_RECORD_METADATA=0` desactiva el guardado automático (p. ej. tests). |

---

## Atributos transversales (idea)

Nombres **orientativos** (estilo Francis: autodescriptivos). No todos aplican a todos los formatos; el hand validaría combinaciones.

| Atributo (idea) | Rol |
|-----------------|-----|
| `metadata-placement` | Dónde va la **metadata pública** (valores permitidos dependen del `format`) |
| `metadata-path` | Ruta del archivo **sidecar** cuando la metadata no va en el mismo archivo |
| `include-workflow-column` | Si el export incluye columna / campo `workflow` (trazabilidad) |
| `include-record-key-column` | Si incluye columna / campo del identificador de record (`recordKey`) cuando exista RecordKey |

**Valores de `metadata-placement` (por formato):** ver tabla por formato abajo. No todos los formatos soportan todos los valores.

---

## Por formato

### JSON

**Uso:** Universal, APIs, anidado.

**Observaciones:** Un archivo; fácil de envolver en `{ "metadata": ..., "records": ... }`.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `embedded` | Objeto top-level con `metadata` + `records` (o equivalente) |
| `none` | Solo el array de records (o el objeto mínimo acordado) |
| `sidecar` | Solo datos en `path`; metadata en `metadata-path` |

**Atributos extra (idea):** `encoding` (utf-8), indentación / pretty-print si se expone.

---

### CSV

**Uso:** Excel, Google Sheets, Pandas.

**Observaciones:** Tabla plana; **meter metadata en las mismas filas** suele ensuciar. Muy habitual **metadata aparte** o solo columnas de datos.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `none` | Solo header + filas de datos |
| `sidecar` | Metadata en otro archivo (json, csv pequeño, etc.) |
| `embedded` | Poco recomendado (filas especiales rompen parsers) |

**Atributos extra (idea):** `delimiter`, `include-header`, más `include-workflow-column` / `include-record-key-column`.

---

### NDJSON

**Uso:** BigQuery, Spark, Polars, streaming.

**Observaciones:** Una línea = un record.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `first-line` | Línea 1 = un JSON con metadata; líneas siguientes = records |
| `none` | Solo líneas de records |
| `sidecar` | Solo data lines; metadata en `metadata-path` |

**Atributos extra (idea):** `encoding`.

---

### XML

**Uso:** Legacy, SAP, integraciones B2B.

**Observaciones:** Buen lugar para atributos en el root y en cada `<record>` (`workflow`, `recordKey`, `total_records`).

**Ejemplo de forma (diseño):**

```xml
<Records workflow="PORTAL-INMOBILIARIO" total_records="1000">
    <record workflow="PORTAL-INMOBILIARIO" recordKey="IdPortalInmobiliario1111">
        <propiedad>
            <otro-id>...</otro-id>
            <titulo>Casa</titulo>
        </propiedad>
    </record>
    <record workflow="PORTAL-INMOBILIARIO" recordKey="IdPortalInmobiliario2222">
        <propiedad>
            <otro-id>...</otro-id>
            <titulo>Departamento</titulo>
        </propiedad>
    </record>
</Records>
```

- Repetir `workflow` en cada `<record>` es redundante pero **mejora trazabilidad** si se corta un fragmento.
- `total_records` debe ser **consistente** con la cantidad real de `<record>` al generar (útil para validación y futuros tests golden).
- `recordKey` = ID estable del ítem en el pipeline; **otro** campo (ej. `canonical-listing-id` / nombre final a definir en schema) puede servir para **emparejar entre sitios**.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `embedded` | Bloque de metadata pública bajo el root (ej. hermano de los records) |
| `none` | Solo `<Records>` + `<record>` |
| `sidecar` | XML “limpio” de negocio; metadata en otro archivo |

**Atributos extra (idea):** nombres de elementos root/record, encoding, pretty-print.

---

### Parquet

**Uso:** Análisis masivo, columnar.

**Observaciones:** Esquema fuerte; metadata **voluminosa** en columnas mezcladas con negocio suele ser mala idea.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `none` | Solo tabla de datos |
| `sidecar` | Archivo json con metadata del job (muy habitual) |
| `embedded` | Solo key-value pequeño en metadata de Parquet (limitado) |

**Atributos extra (idea):** `compression`, `row-group-size` (si aplica).

---

### Excel

**Uso:** Clientes no técnicos.

**Observaciones:** La metadata densa en la **misma hoja** suele confundir; opciones típicas: **sin metadata en el libro**, **hoja 2**, o **archivo aparte**.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `none` | Solo hoja de datos |
| `second-sheet` | Hoja 2 solo para metadata pública |
| `sidecar` | Metadata en otro archivo (no necesariamente xlsx) |

**Atributos extra (idea):** `sheet-name` (datos), `metadata-sheet-name`, `metadata-path`, `include-workflow-column`, `include-record-key-column`, `header-row`, formatos de fecha/número.

**Ejemplo XML (idea, ya en roadmap):**

```xml
<record-save from="propiedadesRecords"
             format="excel"
             path="output/propiedades.xlsx"
             sheet-name="Propiedades"
             include-metadata-sheet="true"/>
```

(Al implementar, alinear nombres con `metadata-placement` unificado.)

---

### TXT (plantilla)

**Uso:** Salida libre con template.

**Observaciones:** La metadata pública casi nunca va “dentro” del texto salvo que el template lo permita.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `none` | Solo render del template |
| `sidecar` | Metadata en archivo separado |

**Atributos extra (idea):** template inline o ruta, encoding.

---

### HTML

**Uso:** Reportes visuales.

**Observaciones:** Metadata puede ir en pie de página o sección aparte; para cliente final a menudo **no**.

| `metadata-placement` (idea) | Comportamiento |
|-----------------------------|----------------|
| `none` | Solo reporte |
| `embedded` | Sección opcional (ej. detalles) |
| `sidecar` | HTML limpio + metadata en json |

**Atributos extra (idea):** `title`, stylesheet, encoding.

---

## Audiencias y preferencias (referencia)

| Audiencia | Datos | Metadata pública |
|-----------|--------|------------------|
| Data engineers | Limpia | Separada (`sidecar`, o `first-line` en NDJSON) |
| Analistas | A veces todo junto | `embedded` o segunda hoja (Excel) |
| Sistemas legacy | XML con atributos | `embedded` en root / bloque |
| BigQuery | NDJSON | `first-line` o metadata aparte |
| Usuarios Excel | Columnas claras | `none` o hoja 2; no mezclar con data si confunde |

---

## RecordKey vs otros identificadores

- **RecordKey** (diseño en roadmap): clave para **deduplicar** en el scrape según campos estables (hash).
- **workflow** (u otro identificador de caso): indica **de qué flujo / portal** sale el record; puede repetirse en cada fila para control.
- **Campo adicional** (ej. id canónico cross-site): vive en el **schema de datos** (`record-set-field`), no tiene por qué ser el mismo string que `recordKey`.

---

## Pendientes relacionados

- **RecordKey** — implementado; ver `docs/roadmap.md`.
- **Filtrado / orden de filas** — no planeado como hands dedicados; usar pipeline externo o librerías cuando haga falta.
- **Tests automatizados** — archivos expected + comparación de contenido; `total_records` como señal rápida + diff completo (no solo conteo).

---

## Historial de cambios (manual)

| Fecha | Nota |
|-------|------|
| 2026-03-24 | Primera versión de guía (diseño acordado en conversación) |
