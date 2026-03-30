# Francis Suite — Roadmap

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible, cloud-ready.

---

## ✅ Ahora — al día (últimos hitos)

- [x] RecordKey — identificador único por record para evitar duplicados
- [x] Formatos adicionales de record-save — xml, html, txt (TSV), excel/xlsx, parquet — ver [guides/record-save.md](guides/record-save.md)
- [x] Documentación + ejemplos `books_all_pages.xml` / `all_books_pages.xml` (export + attrs XML-only `record-xml-*`)
- [x] Liveness en motor — `session-deadline-ms`, `silence-limit-ms`, `session-max-rss-mb`, `session-rss-warn-mb` (opcional), `<session-pulse/>`, pulso automático por hand — ver [Liveness, límites y operación](#liveness-operacion)
- [x] `set-proxy` (httpx) — `local`, `manual`, `file`, `api`; sesión con proxy + última respuesta; `httpx-last-status` / `httpx-get-headers` / `httpx-get-cookies`; `item` en `box-def` y `shared-box-def` — ver [ADR-004](decisions/ADR-004-set-proxy-design.md) (`type="db"` pendiente)

**Siguiente foco (orden de producto):** cerrar **core estable** → **contrato XML / schema para IDE** (base del plugin) → **plugin VSCode** (ADR-003) para debugear bien → en paralelo diseño fuerte de **proxy** y **storage cloud** para prod (GCP u otros). Guías `docs/guides/*` por hand y `liveness.md` cuando haga falta, sin bloquear el core.

---

<a id="prioridad-producto-2026"></a>

## 🎯 Prioridad de producto (decisión 2026)

- **Entregable típico del pipeline:** archivos finales (`record-save`, múltiples formatos) — **no** hay plan de `database-call`; la salida es artefactos en disco o en bucket vía storage.
- **Patrón operativo (ej. trabajo previo):** shared-box tipo “sitio disponible” — `false` al inicio, `true` solo si todo el proceso terminó bien; convención de workflow, no obligatorio en el motor.
- **Plugin VSCode (ADR-003):** prioridad alta **después** de dejar el core lo más cerrado posible; antes de `playwright-call` para poder debugear bien.
- **Contrato / schema XML:** muy prioritario como insumo del plugin (autocompletado, tipos, documentación en IDE).
- **Proxy:** muy prioritario — configuración **manual** (p. ej. local vs remoto), credenciales desde **path** o **respuesta de API** (diseñar antes de implementar en clientes).
- **Storage cloud (fsspec + config):** muy prioritario — subir a prod simple (ej. GCP: jobs programados que corren workflows, generan data final y la guardan para consumo posterior u otro proceso).
- **`excel-read` / `json-read`:** encajan con el **visualizador universal** del plugin (selector en cascada de formato; visor de Excel **solo lectura**, no editor).
- **`pdf-read`:** evolutivo / lo más sólido posible con el tiempo; ir refinando según librería y casos.
- **`playwright-call`:** importante; **después** del plugin para depuración.
- **`use-ia`:** diseño tipo llamada con **timeout, retry**, fallos controlados con **mensaje en la respuesta**; **prompt** desde **path** o **box**; respuesta en **box**; acotar qué se envía al proveedor (investigar proveedor y límites).
- **`zip`:** **sin decidir** — puede ser empaquetar salidas o leer/extraer `.zip`; revisar necesidad real antes de priorizar.
- **`send-mail`, `ftp-call`:** sin prioridad.
- **`database-call`:** **fuera de alcance** (no planificado).
- **YAML como sintaxis de workflow:** **descartado** — el lenguaje declarativo del workflow es **XML** (ver nota abajo).
- **FastAPI** y **`fs` en expresiones:** útiles sobre todo si el plugin o integraciones **online** lo necesitan; para **plugin offline** la prioridad es menor — decidir cuando el plugin tenga recorte claro.
- **Capa producción** (cron, límites OS, alertas): **documentación / ops** — hay que **pensarlo y hablarlo**; checklist en [Liveness — capa externa](#liveness-operacion).
- **Guías** (`docs/guides/liveness.md`, guías por hand): **no** bloquean el core; completar según necesidad, no “todas ya”.
- **Temas pospuestos / sin prioridad ahora** (cwd vs “raíz Francis”, `--workspace`, sandbox de escritura, salidas separadas en record-save, recetas Docker): tabla en [Analizar en el futuro (no prioritario)](#analizar-futuro-no-prioridad).

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

## ✅ Formatos extra de record-save — implementado (base)

**Referencia de atributos y comportamiento:** [guides/record-save.md](guides/record-save.md).

Incluye: `xml`, `html`, `txt` (tab-separated), `excel` / `xlsx`, `parquet` (además de json, csv, ndjson).

**Metadatos de exportación unificados:** declarados en `<record-create>` (`<record-export-attr>` / `<record-export-system>`, alias `<xml-root-*>`); **attrs solo XML:** `<record-xml-root-attr>` / `<record-xml-record-attr>`; cada `<record-save>` solo elige formato; [guides/record-save.md](guides/record-save.md).

**Evolutivo / diseño avanzado** (`metadata-placement`, plantillas txt libres, etc.): [guides/record-save-formats.md](guides/record-save-formats.md).

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
record-store-all    → guarda todos en una box
record-view-content → navega record por record (Plugin VSCode)
mejoras record-save → metadata-placement, txt con plantilla, etc. (guides/record-save-formats.md)
```
Filtrado u orden de filas: fuera del engine por ahora (script externo, Pandas, etc.).

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

<a id="liveness-operacion"></a>

## Liveness, límites y operación

*Contexto (2026): evitar workflows **pegados eternos** y **pérdida de criterio técnico**. La base está en código; refinamientos y capa externa siguen en roadmap.*

### Estado en código (2026)

| Pieza | Estado |
|-------|--------|
| **`<francis-workflow session-deadline-ms="…">`** | Implementado: wall clock desde `session.start()`; comprobación antes de cada hand y en hilo de fondo. **Limitación:** durante un bloqueo largo dentro de un solo hand (p. ej. `time.sleep` sin hand intermedio), el deadline no se evalúa hasta que el hand devuelve. |
| **`silence-limit-ms`** | Implementado: si pasan más de X ms sin “progreso”, el hilo marca `LivenessError` (silence). **Progreso** = pulso al **inicio** de cada hand (`FRuntime.execute_node`), al **terminar** un hand con éxito, y `<session-pulse/>` manual. **Limitación:** el aborto se observa al desbloquear el main (p. ej. tras `time.sleep` o al terminar la petición HTTP); no interrumpe código C ni operaciones sin cooperación. |
| **`session-max-rss-mb`** | Implementado: tope software de RSS del proceso (MB). Comprobación en hilo de liveness (~250 ms) y antes de cada hand. Superarlo → `SessionRssLimitError` (subclase de `LivenessError`). **Limitación:** no sustituye al OOM del kernel; si `psutil` falla, se avisa una vez y el límite no se aplica. |
| **`session-rss-warn-mb`** | Opcional; solo con `session-max-rss-mb` y debe ser **menor** que el máximo (si no, se ignora con un `[SESSION]` log). Un solo aviso por sesión cuando RSS ≥ umbral y aún no se superó el máximo. |
| **`<session-pulse/>`** | Pulso extra entre hands o dentro de tramos largos (mismo reloj que `silence-limit-ms`). |
| **Timeouts de hands** (`httpx-call`, etc.) | Siguen siendo el contrato de la operación; el silencio no los acorta: mientras el hand bloquea dentro de su timeout, el reloj de silencio sigue; si el hand dura más que `silence-limit-ms` sin nuevos pulsos, puede fallar por silencio antes que por timeout HTTP (ajustar límites o trocear en más hands / usar `session-pulse`). |

### A) Dentro de Francis (motor / sesión) — prioridad conceptual

| Idea | Rol |
|------|-----|
| **Deadline global de sesión** (opcional, p. ej. env o atributo raíz) | Corta la corrida tras N minutos aunque el XML siga; última defensa contra zombies. Trade-off: puede matar jobs lentos pero válidos si N es bajo. |
| **Watchdog de “sin señales”** | Si durante demasiado tiempo no hay **progreso relevante**, abortar con error claro (equivalente moderno a “N updating task y cerrar”). |
| **Qué cuenta como progreso relevante (por defecto)** | **Cualquier hand que termina con éxito** — así cada hand nuevo entra sin registrar a mano. Opcional: opt-out en hands raros. |
| **`<heartbeat/>` o equivalente** | Reinicia el contador / reloj de silencio en **huecos largos** (HTTP lento aceptable, sleep grande, batch interno) donde no hay cierre de hand todavía. |
| **Trabajos enormes (p. ej. data lake)** | No basta con “un solo hand largo”: **trocear** en etapas (varios hands / loops) o **señales de progreso** (fase, partición, filas) para que el motor vea avance; si no, solo ayudan timeout HTTP + deadline global. |

**Nota:** Hoy ya existen piezas parciales: `timeout` en `httpx-call`, `max-loops` en `<while>` (default 10 000), `<loop>` con `max-loops` opcional (sin tope = recorre **toda** la lista).

**Regla al implementar (prioridad):** Los **timeouts que el usuario configure** en hands (`httpx-call` y análogos) son el tiempo **acordado** de espera en esa operación. La liveness / `session-pulse` / watchdog **debe respetarlos**: no declarar “pegado” ni cortar **dentro** de ese presupuesto por culpa del pulso. El pulso o el contador de silencio conviven (p. ej. evaluar **entre** hands, o usar `<session-pulse/>` antes/después de tramos largos). Si el timeout HTTP vence, la operación falla por **timeout**, no por el watchdog “ganándole” por poco tiempo.

### B) Capa externa (opcional; sana en producción)

No reemplaza lo anterior; es **red de seguridad** cuando el proceso deja de responder a Python:

- **Tiempo máximo del proceso** (cron `timeout`, systemd, job scheduler).
- **Límite de RAM** (ulimit, cgroups, Kubernetes `memory`).
- **Reintentos con backoff** (no infinitos) para fallos transitorios.
- **Una sola corrida a la vez** por recurso (lock / archivo / flag en DB).
- **Secretos fuera del repo**, rotación de logs, cuidado con PII en logs.
- **Rate limiting / respeto robots.txt y TOS** donde aplique.
- **Alertas** simples (webhook, mail) si el job termina con exit code ≠ 0.

### C) Documentación futura

- Mini **ADR** o sección en `architecture.md`: refinamientos (p. ej. opt-out de pulso automático por hand si algún día hace falta).

---

## ⬜ Pendiente — Nuevas fuentes y hands

**Alta / media prioridad (ver [Prioridad de producto](#prioridad-producto-2026))**

- [ ] `excel-read` — leer Excel/CSV; complementa el **visualizador** del plugin (formato en cascada).
- [ ] `json-read` — leer JSON externo; mismo eje de visualización en plugin.
- [ ] `pdf-read` — parseo PDF; enfoque evolutivo (“vanguardista” a medida que madure el ecosistema).
- [ ] `use-ia` — ver diseño en prioridad de producto (timeout, retry, prompt path/box, errores controlados).
- [ ] `playwright-call` — **después** del plugin VSCode para poder debugear.
- [ ] `scrapling-call` — scraping avanzado (cuando toque).

**Sin prioridad / fuera de alcance**

- ~~`database-call`~~ — no planificado; la salida típica son archivos (`record-save`) u object storage.
- `send-mail`, `ftp-call` — sin prioridad.
- `zip` — **decidir** si hace falta **crear** `.zip` de salidas, **leer** contenido, o ambos; no priorizado hasta definir caso de uso.

---

## ⬜ Futuro

### Contrato / schema XML para IDE (prioridad alta para el plugin)

Definir un **contrato de metadatos** — schema o gramática — consumible por el plugin y por reglas del editor:

- Tab / autocompletado de tags y atributos
- Qué devuelve cada hand y valores permitidos por atributo
- Cursor rules, extensión VSCode o snippets comparten el mismo contrato

**Orden sugerido:** cerrar el core “suficientemente estable” → **schema** → **plugin** (ADR-003).

### `workflow-param` — opcional (sin prioridad ahora)

Hand XML para declarar defaults o `from-env` en el archivo. **No está planeado implementarlo pronto:** la inyección vía CLI `--param`, código con `run_session` / shared-box, y perfiles del plugin cubren el caso. Si más adelante se necesita, se diseña y se agrega.

```xml
<!-- idea — solo referencia, no implementado -->
<workflow-param name="ciudad"   default="santiago"/>
<workflow-param name="api_key"  from-env="PORTAL_API_KEY"/>
```

- Hoy: `--param` y `set_shared_box` antes de ejecutar — ver [guides/sensitive.md](guides/sensitive.md).

### Plugin VSCode (prioridad alta tras el core)
Ver ADR-003 para diseño completo. Objetivo: **debugear workflows** antes de hands pesados (p. ej. Playwright).

- Syntax highlighting, autocompletado (alimentado por el **schema XML**), snippets
- Tree de ejecución en tiempo real (usa EventBus)
- Inspector de variables — al hacer click muestra el valor real
- Visualizador de datos universal — TEXT, HTML, XML, JSON, CSV con buscador; **selector en cascada de formato**; visor de Excel (solo lectura) cuando exista `excel-read` / datos tabulares
- Navegador de records — 1 de N, botones anterior/siguiente
- Controles de ejecución — run, pause, step, resume, stop
- Variables sensibles muestran valor maskeado

### Sistema de proxy (muy prioritario)
**Hand `set-proxy` + sesión httpx:** [ADR-004](decisions/ADR-004-set-proxy-design.md). **Implementado:** `client="httpx"`, tipos `local`, `manual`, `file`, `api`; rotación y probe; `httpx-call` + stream registran última respuesta; **`httpx-last-status`**, **`httpx-get-headers`**, **`httpx-get-cookies`**; **`item`** en **`box-def`** / **`shared-box-def`** para indexar `FListVariable`. **Pendiente:** `type="db"`, Playwright/Scrapling.

Antes de tocar clientes HTTP en serio:

- Uso **manual** (p. ej. elegir proxy local vs otro)
- Credenciales / config desde **archivo (path)** o desde **respuesta de una API**
- Aplicar de forma coherente al primer request y siguientes (httpx y futuros clientes)

### Storage Provider — Cloud-ready (muy prioritario)
fsspec. Configuración en `francis-config.yaml` (nunca en git). Soporta: local, S3, GCS, Azure Blob.

**Caso de uso:** prod simple — ej. **GCP** (u otro): jobs que ejecutan workflows Francis en schedule, generan **data final** (`record-save` u uploads), almacenan en bucket para descarga o para que **otro proceso** consuma después.

### fs — Objeto de utilidades
```xml
${fs.uuid()}, ${fs.now()}, ${fs.env("KEY")}, ${fs.random(1,100)}
```

### FastAPI — REST API
```
POST /run, GET /status/:id, GET /context/:id, WS /ws/:id
```
Prioridad **condicional**: más relevante si el plugin u otras integraciones **online** lo necesitan; para un recorte **offline** del plugin puede esperar.

### ~~YAML como formato de workflow~~ — descartado
El workflow declarativo de Francis Suite es **solo XML**. No hay plan de `FYamlParser` ni de sintaxis YAML equivalente al `<francis-workflow>`. (Los ficheros `*.yaml` de **configuración** del producto, p. ej. `francis-config.yaml`, son otro asunto.)

---

<a id="analizar-futuro-no-prioridad"></a>

## Analizar en el futuro (no prioritario)

Temas **aclarados en diseño** pero **sin compromiso de implementación** hasta que el producto lo pida. Sirven para no mezclar “idea de roadmap” con comportamiento actual del motor.

| Tema | Estado hoy | Nota |
|------|------------|------|
| **Rutas relativas / cwd** | Las rutas en XML (`path`, `to`, etc.) son relativas al **directorio de trabajo del proceso** (cwd), no a una “raíz Francis” fija. Los ejemplos usan `output/` por convención. | En prod: rutas absolutas o `${param}` / env resueltos por `engine.resolve`. |
| **CLI `--workspace` / env tipo `FRANCIS_ROOT`** | No implementado. | Si se prioriza: definir semántica (solo rutas del workflow vs también cwd) y documentar. |
| **Validación unificada de paths** | Cada hand que escribe valida como toca. | Mejora de UX de errores; no bloquea el core. |
| **Sandbox / allowlist de escritura** (p. ej. solo bajo `output/`) | No hay. | Seguridad hoy por convención y workflows confiables; dry-run sería otro sub-tema. |
| **Salidas separadas en `record-save`** (duplicados vs fallidos en ficheros distintos) | No implementado. | Patrón de producto a decidir antes de código. |
| **Composición de rutas en cloud** (`BASE` + `session_id` en `path`) | Coherente con variables y `engine.resolve`. | Recetas en guías cuando haya un ejemplo oficial; no requiere cambio de motor por sí solo. |
| **Paridad Docker / contenedores** (volúmenes, cwd, usuario) | Documentación de ops cuando haga falta. | Relacionado con [Liveness — capa externa](#liveness-operacion), no con una feature del engine. |

Si algo de esta lista **sube de prioridad**, moverlo a [Prioridad de producto (decisión 2026)](#prioridad-producto-2026) o a un ADR concreto.

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
- [x] record-count, record-save (json, csv, ndjson, xml, html, txt, excel, parquet)
- [x] record-save-metadata — solo metadata privada, sin rows
- [x] record-private-metadata — agrega metadata en cualquier parte del workflow
- [x] Sistema de metadata automática — psutil para RAM, calidad de datos
- [x] Compatibilidad universal — pathlib, as_posix(), utf-8
- [x] ADR-002 — formatos HTTP
- [x] ADR-003 — debug, observabilidad, plugin VSCode
- [x] ADR-004 — diseño `set-proxy` (documentado; código pendiente)
- [x] Suite `pytest tests/test_pipeline.py` — ver CI / local
- [x] Ejemplos `books_all_pages.xml` / `all_books_pages.xml` — books.toscrape.com + ocho formatos + `record-xml-*` en XML
