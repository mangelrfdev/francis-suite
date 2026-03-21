# Francis Suite — Roadmap

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible, cloud-ready.

---

## ⬜ Ahora — Urgente

- [ ] `httpx-call` — agregar `response="binary"` y `response="stream"`
- [ ] `file-write` — corregir manejo de binarios con `open("wb")`
- [ ] `file-manage` — agregar actions: `mkdir`, `exists`, `rename`, `size`
- [ ] `file-manage` — agregar `overwrite="true/false"` en move y copy
- [ ] `file-manage` — agregar `safe="true"` en delete para directorios
- [ ] Eliminar `file-download` y `file-upload` del codebase
- [ ] Verificar que `evaluate` persiste bien entre iteraciones del loop
- [ ] `sensitive` — atributo para box-def y shared-box-def
- [ ] `workflow-param` — parámetros de entrada al workflow
- [ ] CLI — `--param` support

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

**`record-create`** — define el schema, sin path, sin mode por ahora:
```xml
<record-create name="productosRecords">
    <record-set-group name="productos" required="true">
        <record-set-field name="nombre_visible" type="string"  required="true"/>
        <record-set-field name="precio"         type="integer" required="true"/>
        <record-set-field name="marca"          type="string"  required="false"/>
    </record-set-group>
    <record-set-group name="empaques" required="false">
        <record-set-field name="cantidad" type="integer" required="false"/>
        <record-set-field name="unidad"   type="string"  required="false"/>
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

**`record-last-added`** — ver último record agregado (debug):
```xml
<record-last-added from="productosRecords"/>
```

**`record-store-all`** — guarda todos los records en una box:
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
string        — texto, default
integer       — número entero ($3.990 → 3990 automático)
decimal       — número decimal
boolean       — true/false
date          — fecha (2024-01-15)
datetime      — fecha y hora
url           — valida URL
email         — valida email
uuid          — genera UUID si está vacío
null-if-empty — si vacío → null, no ""
```

### Formatos de output:
```
json    — array de objetos, soporta grupos anidados
csv     — plano, grupos se aplanan automáticamente (grupo.campo)
ndjson  — una línea por record — ideal para BigQuery y streaming
txt     — libre con template
html    — libre con template
```

### Modos:
```
mode="batch"   — acumula en memoria, guarda al final (default)
mode="stream"  — escribe a disco en cada record (sin límite RAM)
```

### Nota de memoria:
Con `mode="stream"` la box guarda solo una referencia al archivo.
El Plugin VSCode navegará record por record desde disco (1 de 1000).
Nunca se carga todo en RAM.

---

## ⬜ Trabajando en ello — Variables y control

### `sensitive` — Variables sensibles
```xml
<!-- automático por nombre -->
<shared-box-def name="api_key">secreto</shared-box-def>

<!-- explícito -->
<shared-box-def name="codigo_cliente" sensitive="true">abc123</shared-box-def>

<!-- forzar no-sensible -->
<shared-box-def name="token_count" sensitive="false">100</shared-box-def>
```
Palabras que activan `sensitive` automáticamente:
`api_key`, `apikey`, `token`, `password`, `passwd`, `secret`,
`credential`, `auth`, `private_key`, `access_key`

En logs y Plugin VSCode muestra `***` para variables sensibles.
Aplica a `box-def`, `shared-box-def` y `workflow-param`.

### `workflow-param` — Parámetros de entrada
```xml
<francis-workflow>
    <workflow-param name="searchTerm" default=""/>
    <workflow-param name="page"       default="1"/>
    <workflow-param name="api_key"    from-env="API_KEY"/>
</francis-workflow>
```
- `default` — valor si no se recibe nada
- `from-env` — lee desde variable de entorno del sistema
- Siempre opcional — nunca falla si falta el parámetro
- Se guarda internamente como `shared-box-def`

### CLI — `--param` support
```powershell
francis-suite run scraper.xml --param nombre=Juan --param modo=debug
```

---

## ⬜ Pendiente — Observabilidad y control de ejecución

Sistema de control y monitoreo de workflows en ejecución.
Inspirado en sistemas de producción reales.

### Hands a implementar:
- `<breakpoint/>` — pausa la ejecución en un punto específico para inspección
- `<freeze message="..."/>` — congela la tarea con mensaje e ID inspectable

### Estados de ejecución:
```
running    — ejecutándose
completed  — terminó correctamente
failed     — falló con error
frozen     — congelado manualmente para inspección — diferente a failed
```

### Entorno de observabilidad:
- Cola de tareas — corriendo, en espera, fallidas, frozen
- Historial de fallos por tarea — cuántas veces falló
- Logs por tarea con ID inspectable
- IDs por entorno — prod, dev, test
- Replicar ejecución local con ID de prod o dev

### Nota:
Conecta con `EventBus` y `FrancisSession` que ya existen — son la base
natural para construir esto encima. Implementar cuando FastAPI esté listo.

---

## ⬜ Pendiente — Nuevas fuentes de datos

Francis Suite extrae data de cualquier fuente:

- [ ] `pdf-read` — leer y parsear PDFs
- [ ] `excel-read` — leer Excel y CSV
- [ ] `json-read` — leer JSON externo
- [ ] `use-ia` — análisis con IA (imágenes, texto) — retorna JSON estructurado
- [ ] `playwright-call` — automatización de browser con su propio manejo de descargas
- [ ] `scrapling-call` — scraping avanzado con su propio manejo de descargas
- [ ] `database-call` — consultas a bases de datos
- [ ] `send-mail` — envío de correos
- [ ] `ftp-call` — operaciones FTP
- [ ] `zip` — compresión de archivos

### Nota sobre clientes HTTP:
Cada cliente maneja sus propias descargas internamente.
`httpx-call` con `response="binary"` o `response="stream"` cubre todos
los casos de descarga HTTP. `file-download` fue eliminado.

---

## ⬜ Futuro

### Plugin VSCode
- Syntax highlighting para XML de Francis Suite
- Autocompletado de hands y atributos
- Snippets para patrones comunes
- Tree de ejecución en tiempo real (usa EventBus)
- Visualización de boxes y sus valores
- Navegador de records (1 de 1000, botones < >)
- Switch de formato: JSON / BEAUTY / TEXT / CSV
- Variables sensibles muestran `***`
- Modo preview: corre solo N iteraciones
- Integración con sistema de observabilidad — ver tareas frozen, fallos, cola

### Sistema de proxy — Alta prioridad cuando implementemos clientes
- El primer hit de cualquier cliente debe pasar por configuración de proxy
- Soporta: sin proxy, proxy fijo, rotación automática
- Pendiente de diseño — no implementar antes de tener clientes listos

### Storage Provider — Cloud-ready
```yaml
# francis-config.yaml (nunca en git)
storage:
  provider: s3
  bucket: mi-bucket
  credentials:
    access_key: ${env:AWS_ACCESS_KEY}
```
Usa `fsspec` — estándar de la industria (Pandas, Dask, DuckDB, Prefect).

### `fs` — Objeto de utilidades
```xml
${fs.uuid()}
${fs.now()}
${fs.env("API_KEY")}
${fs.random(1, 100)}
${fs.urlEncode("hola mundo")}
```

### FastAPI — REST API
```
POST /run         — ejecutar workflow
GET  /status/:id  — estado de ejecución
GET  /context/:id — variables del contexto en tiempo real
```

### Heartbeat
```xml
<francis-workflow heartbeat="30000" max-idle="5"/>
```

### YAML como formato alternativo
`FYamlParser` convierte YAML → FNode tree.
El engine no cambia nada — solo el parser cambia.
XML sigue siendo válido y soportado.

---

## ✅ Completado

- [x] Core: variables, nodes, context, registry, parser, session, events, runtime
- [x] Expression engine: `${variable}`, arithmetic, comparisons, `toBoolean()`, `isEmpty()`
- [x] Arquitectura por capas — FNode como puente universal
- [x] Hands: log, box-def, box, sleep, httpx-call, convert-html-to-xml
- [x] xpath-extract, loop, while, if, else, case, try, catch, exit
- [x] function-create (replace), function-call, function-param, function-return
- [x] regex, compose, text-split, evaluate, build-list, call-workflow
- [x] convert-json-to-xml, convert-xml-to-json
- [x] file-read, file-write, file-manage
- [x] shared-box-def, shared-box con `replace`
- [x] Scoping: "si no se toca, no cambia"
- [x] engine.resolve() en todos los atributos
- [x] Compatibilidad universal — pathlib, as_posix(), utf-8 explícito
- [x] file-write — newline="true"
- [x] file-manage — fix _list filtra directorios, fix _move/_copy sin str()
- [x] file-write — context manager con with
- [x] text-format renombrado a compose
- [x] ADR-002 — decisión de formatos HTTP documentada
- [x] 55 tests pasando
- [x] Ejemplo books_all_pages.xml — 1000 libros extraídos
