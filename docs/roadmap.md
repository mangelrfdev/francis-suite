# Francis Suite — Roadmap

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible, cloud-ready.

---

## ⬜ Ahora — Urgente

- [x] RecordKey — identificador único por record para evitar duplicados
- [ ] Formatos adicionales de record-save — xml, excel, parquet, html, txt
- [ ] record-filter — filtrar rows antes de guardar
- [ ] record-sort — ordenar por campo
- [ ] workflow-param — como hand XML (CLI --param ya implementado)

---

## ✅ RecordKey — Implementado

Sistema para evitar duplicados en el scraping.
Cada record tiene un key único generado a partir de campos que nunca cambian.

### Concepto:

```
CaseKey  → identificador característico del scraper (nombre del workflow)
RecordKey → hash de campos que nunca cambian del item extraído
```

### En XML:

```xml
<record-create name="propiedadesRecords">

    <!-- define qué campos forman el key único -->
    <record-key>
        <key-field name="portal"/>
        <key-field name="codigo_propiedad"/>
    </record-key>

    <record-set-group name="propiedad" required="true">
        <record-set-field name="portal"           type="string"  required="true"/>
        <record-set-field name="codigo_propiedad" type="string"  required="true"/>
        <record-set-field name="titulo"           type="string"  required="true"/>
        <record-set-field name="precio"           type="integer" required="true"/>
    </record-set-group>

</record-create>
```

### Comportamiento:

```
record-add con key nuevo     → agrega el record normalmente
record-add con key duplicado → skip con log:
[RECORD] duplicate key — skipping (key: abc123def456)
```

### ¿Qué campos usar para el key?

```
✅ URL de la propiedad     — nunca cambia
✅ Código interno del portal — nunca cambia
✅ Dirección exacta        — rara vez cambia
❌ Precio                  — cambia constantemente
❌ Título                  — puede editarse
❌ Fecha                   — siempre cambia
```

---

## ⬜ Formatos adicionales de record-save

**Guía de diseño (no perder contexto):** [guides/record-save-formats.md](guides/record-save-formats.md) — metadata pública vs privada, `metadata-placement`, atributos por formato, XML de ejemplo, audiencias.

### Formatos a implementar:

```
xml     — para sistemas legacy, SAP, integraciones B2B
          <Records workflow="PORTAL-INMOBILIARIO" total_records="1000">
              <record workflow="PORTAL-INMOBILIARIO" recordKey="IdPortal1111">
                  <propiedad>
                      <titulo>Casa</titulo>
                  </propiedad>
              </record>
          </Records>

excel   — para clientes no técnicos
          columnas: workflow, recordKey, propiedad.titulo, propiedad.precio
          metadata en hoja separada (Sheet2) si se declara <record-metadata>
          atributos: sheet-name, include-metadata-sheet="true/false"

parquet — para análisis de datos masivos, columnar, muy eficiente
          ideal para BigQuery y Spark

html    — para reportes visuales
          tabla HTML con los rows

txt     — libre con template
          el usuario define el formato con ${variables}
```

### Atributos para excel:

```xml
<record-save from="propiedadesRecords"
             format="excel"
             path="output/propiedades.xlsx"
             sheet-name="Propiedades"
             include-metadata-sheet="true"/>
```

---

## ⬜ Trabajando en ello — Sistema de Records (COMPLETADO base)

Sistema de output estructurado para guardar data limpia y lista para DB.
Base implementada y funcionando.

### Ciclo de vida implementado:
```
1. DEFINIR   → record-create ✅
2. AGREGAR   → record-add ✅
3. VERIFICAR → record-last-added ✅
4. CONTAR    → record-count ✅
5. GUARDAR   → record-save ✅
6. METADATA  → record-save-metadata ✅
7. PRIVADO   → record-private-metadata ✅
```

### Pendiente del sistema de records:
```
record-key          → deduplicación
record-filter       → filtrar rows
record-sort         → ordenar rows
record-store-all    → guarda todos en una box
record-view-content → navega record por record (Plugin VSCode)
xml, excel, parquet, html, txt como formatos de record-save
```

### Tipos de field implementados:
```
string, integer, decimal (con Decimal exacto), boolean
date (→YYYY-MM-DD), datetime (→YYYY-MM-DDTHH:MM:SS)
url, email, uuid, null-if-empty
```

### Sistema de metadata implementado:

**Metadata privada — siempre generada automáticamente:**
```
Trazabilidad:  session_id, workflow_path, francis_suite_version,
               hostname, sistema_operativo, python_version, status, error, inicio, fin
Rendimiento:   duracion_segundos, ram_peak_mb, ram_promedio_mb, rows_por_segundo
               requests_http_total (futuro), requests_http_fallidas (futuro)
Calidad:       total_rows, rows_completados, rows_con_campos_vacios,
               rows_fallidos, campos_nulos_total, porcentaje_completitud
Scraping:      paginas_procesadas, paginas_fallidas, urls_visitadas
               (via <record-private-metadata>)
               proxies_usados (futuro), captchas_encontrados (futuro)
```

**Metadata pública — opcional, solo si se declara `<record-metadata>`:**
```xml
<record-metadata>
    <metadata-field name="fuente">Portal Inmobiliario</metadata-field>
    <metadata-field name="rows_completados"/>       <!-- auto-computado -->
    <metadata-add-field name="ciudad">${ciudad}</metadata-add-field>
</record-metadata>
```
Solo se escribe si status=completed.

---

## ⬜ Trabajando en ello — Variables y control

### `workflow-param` — Parámetros de entrada (CLI ya implementado)
```xml
<francis-workflow>
    <workflow-param name="ciudad"   default="santiago"/>
    <workflow-param name="api_key"  from-env="PORTAL_API_KEY"/>
</francis-workflow>
```
- CLI `--param KEY=VALUE` ya funciona — inyecta variables como shared-box
- El hand XML `workflow-param` está pendiente de implementar

---

## ⬜ Pendiente — Observabilidad y control de ejecución

Ver ADR-003 para diseño completo.

### Manos:
- `<pause-task/>` — IMPLEMENTADO — pausa en dev, falla con WARNING en prod
- CLI `--debug` — pausa en cada `<pause-task/>`
- CLI `--step` — avanza hand por hand

### Estados:
```
running, completed, failed, paused
```

---

## ⬜ Pendiente — Nuevas fuentes de datos

- [ ] `pdf-read` — leer y parsear PDFs
- [ ] `excel-read` — leer Excel y CSV
- [ ] `json-read` — leer JSON externo
- [ ] `use-ia` — análisis con IA (imágenes, texto)
- [ ] `playwright-call` — automatización de browser
- [ ] `scrapling-call` — scraping avanzado
- [ ] `database-call` — consultas a bases de datos
- [ ] `send-mail` — envío de correos
- [ ] `ftp-call` — operaciones FTP
- [ ] `zip` — compresión de archivos

---

## ⬜ Futuro

### Plugin VSCode
Ver ADR-003 para diseño completo.
- Syntax highlighting, autocompletado, snippets
- Tree de ejecución en tiempo real (usa EventBus)
- Inspector de variables — al hacer click muestra el valor real
- Visualizador de datos universal — TEXT, HTML, XML, JSON, CSV con buscador
- Navegador de records — 1 de N, botones anterior/siguiente
- Controles de ejecución — run, pause, step, resume, stop
- Variables sensibles muestran valor maskeado

### Sistema de proxy
El primer hit de cualquier cliente debe pasar por configuración de proxy.
Pendiente de diseño — no implementar antes de tener clientes listos.

### Storage Provider — Cloud-ready
Usa fsspec. Configuración en francis-config.yaml (nunca en git).
Soporta: local, S3, GCS, Azure Blob.

### fs — Objeto de utilidades
```xml
${fs.uuid()}, ${fs.now()}, ${fs.env("KEY")}, ${fs.random(1,100)}
```

### FastAPI — REST API
```
POST /run, GET /status/:id, GET /context/:id, WS /ws/:id
```

### YAML como formato alternativo
FYamlParser convierte YAML → FNode tree. El engine no cambia.

---

## ✅ Completado

- [x] Core completo — base, variables, nodes, context, registry, parser, session, events, runtime
- [x] base.py — FVariable única, evita circular imports entre variables.py y records.py
- [x] Expression engine — ${variable}, arithmetic, comparisons, methods
- [x] Arquitectura por capas — FNode como puente universal
- [x] Todos los hands core implementados
- [x] httpx-call — response: text, binary, stream
- [x] file-write — encoding binary, newline, context manager
- [x] file-manage — 8 actions completas con mensajes de error claros
- [x] sensitive — auto-detección por nombre, masking, to_display()
- [x] compose — renombrado desde text-format
- [x] file-download y file-upload eliminados
- [x] CLI --param — inyección segura de variables
- [x] FRuntime.run_session() — inyección antes de ejecutar
- [x] convert-binary-to-base64, convert-base64-to-binary
- [x] convert-text-to-base64, convert-base64-to-text
- [x] convert-json-to-csv, convert-csv-to-json, convert-xml-to-csv
- [x] convert-text-to-url, convert-url-to-text
- [x] convert-html-entities-to-text
- [x] pause-task — pausa en dev, warning en prod, FRANCIS_ENV
- [x] Sistema de records base — record-create, record-add, record-last-added
- [x] record-count, record-save (json, csv, ndjson)
- [x] record-save-metadata — solo metadata privada, sin rows
- [x] record-private-metadata — agrega metadata en cualquier parte del workflow
- [x] Sistema de metadata automática — psutil para RAM, calidad de datos
- [x] Compatibilidad universal — pathlib, as_posix(), utf-8
- [x] ADR-002 — formatos HTTP
- [x] ADR-003 — debug, observabilidad, plugin VSCode
- [x] 116 tests pasando
- [x] Ejemplo books_all_pages.xml — 1000 libros extraídos
