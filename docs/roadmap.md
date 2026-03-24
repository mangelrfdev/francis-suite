# Francis Suite — Roadmap

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible, cloud-ready.

---

## ⬜ Ahora — Urgente

- [ ] `pause-task` — pausa en dev, falla con warning en prod
- [ ] Sistema de records
- [ ] `workflow-param` como hand XML

---

## ⬜ Trabajando en ello — Sistema de Records

Sistema de output estructurado para guardar data limpia y lista para DB.
Diseño acordado — pendiente implementar.

### Ciclo de vida de un record:
```
1. DEFINIR   → record-create
2. AGREGAR   → record-add
3. VERIFICAR → record-last-added
4. GUARDAR   → record-save
```

### Hands a implementar:

**`record-create`** — define el schema:
```xml
<record-create name="productosRecords">
    <record-set-group name="productos" required="true">
        <record-set-field name="nombre_visible" type="string"  required="true"/>
        <record-set-field name="precio"         type="integer" required="true"/>
        <record-set-field name="marca"          type="string"  required="false"/>
    </record-set-group>
</record-create>
```

**`record-add`** — agrega un record:
```xml
<record-add to="productosRecords">
    <record-add-group name="productos">
        <record-add-field name="nombre_visible">${nombre}</record-add-field>
        <record-add-field name="precio">${precio}</record-add-field>
    </record-add-group>
</record-add>
```

**`record-last-added`** — ver último record (debug):
```xml
<record-last-added from="productosRecords"/>
```

**`record-store-all`** — guarda todos en una box:
```xml
<record-store-all from="productosRecords" to="productosBox"/>
```

**`record-view-content`** — navega record por record (Plugin VSCode):
```xml
<record-view-content from="productosRecords" preview-limit="20"/>
```

**`record-save`** — persiste en archivo:
```xml
<record-save from="productosRecords" format="json"   path="output/productos.json"/>
<record-save from="productosRecords" format="csv"    path="output/productos.csv"/>
<record-save from="productosRecords" format="ndjson" path="output/productos.ndjson"/>
```

**`record-count`** — cuenta records totales:
```xml
<record-count from="productosRecords"/>
```

### Tipos de field:
```
string, integer, decimal, boolean, date, datetime, url, email, uuid, null-if-empty
integer limpia automáticamente: $3.990 → 3990
```

### Formatos de output:
```
json    — array de objetos, soporta grupos anidados
csv     — plano, grupos se aplanan (grupo.campo)
ndjson  — una línea por record — ideal para BigQuery y streaming
txt, html — libres con template
```

### Modos:
```
mode="batch"  — acumula en memoria, guarda al final (default)
mode="stream" — escribe a disco en cada record (sin límite RAM)
```

---

## ⬜ Trabajando en ello — Variables y control

### `workflow-param` — Parámetros de entrada
```xml
<francis-workflow>
    <workflow-param name="ciudad"   default="santiago"/>
    <workflow-param name="api_key"  from-env="PORTAL_API_KEY"/>
</francis-workflow>
```
- `default` — valor si no se recibe nada
- `from-env` — lee desde variable de entorno del sistema
- Se guarda internamente como `shared-box-def`
- CLI `--param` ya implementado — inyecta variables como shared-box

---

## ⬜ Pendiente — Observabilidad y control de ejecución

Ver ADR-003 para diseño completo.

### Hands:
- `<pause-task/>` — pausa en dev, falla con WARNING en prod
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
- Tree de ejecución en tiempo real
- Inspector de variables
- Visualizador de datos universal
- Navegador de records
- Controles de ejecución — run, pause, step, resume, stop

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

- [x] Core completo — variables, nodes, context, registry, parser, session, events, runtime
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
- [x] Compatibilidad universal — pathlib, as_posix(), utf-8
- [x] ADR-002 — formatos HTTP
- [x] ADR-003 — debug, observabilidad, plugin VSCode
- [x] 99 tests pasando
- [x] Ejemplo books_all_pages.xml — 1000 libros extraídos
