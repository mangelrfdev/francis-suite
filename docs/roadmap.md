# Francis Suite — Roadmap

Ideas y features pendientes de implementar, ordenadas por prioridad.

---

## 🔥 Prioridad Alta

### Ejemplos funcionales
- [ ] `examples/books_all_pages.xml` — paginación completa con 50 páginas y 1000 libros
- [ ] Más ejemplos reales de scraping

### CLI — `--param` support
Permitir pasar parámetros al workflow desde la terminal:
```powershell
francis-suite run scraper.xml --param nombre=Juan --param modo=debug
```
Los parámetros se inyectan al contexto como variables normales.

### `file-manage` — actions pendientes
Agregar nuevas actions a `file-manage`:
```xml
<file-manage action="mkdir" path="output/scraping-${id}/"/>
<file-manage action="exists" path="output/config.txt"/>
<file-manage action="rename" path="old.txt" dest="new.txt"/>
<file-manage action="size" path="output/resultado.txt"/>
```

### `file-manage` — validaciones automáticas
Todo lo que se pueda resolver automáticamente se resuelve.
Todo lo que no se pueda resolver da un error claro y controlado.

Validaciones automáticas:
- Caracteres inválidos en rutas: `? * : " < > |`
- Ruta vacía o demasiado larga
- Carpeta padre no existe → crearla automáticamente
- Sin permisos de escritura → error claro
- Archivo no encontrado → error claro
- Disco lleno → error claro

Aplica a todos los hands de file: `file-read`, `file-write`,
`file-download`, `file-upload`, `file-manage`.

Mismo comportamiento en local y en nube.

---

## 🚧 Prioridad Media

### `workflow-param` — Parámetros de entrada al workflow
Declarar qué parámetros espera un workflow y de dónde vienen:
```xml
<francis-workflow>
    <workflow-param name="searchTerm" default=""/>
    <workflow-param name="page" default="1"/>
    <workflow-param name="api_key" from-env="API_KEY"/>
</francis-workflow>
```

- `default` — valor por defecto si no se recibe nada
- `from-env` — leer desde variable de entorno del sistema operativo
- Siempre opcional — nunca falla si no se recibe el parámetro
- Los parámetros extra que vengan de afuera se ignoran silenciosamente
- Se guardan como `shared-box-def` internamente
- Actualizables desde adentro del workflow con `box-def` o `shared-box-def`
- Visibles en el panel de contexto del IDE

### `sensitive` — Variables sensibles
Marcar variables como sensibles para que no aparezcan en logs ni en el IDE:
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

En logs y en el IDE siempre muestra `***` para variables sensibles.

Aplica a `box-def`, `shared-box-def` y `workflow-param`.

### Storage Provider — Cloud-ready file system
Francis Suite usa un storage provider abstracto — el XML nunca cambia,
solo la configuración de dónde vive el storage.
```xml
<!-- mismo XML en local y en nube -->
<file-write path="output/resultado.txt">contenido</file-write>
```

Configuración en `francis-config.yaml` (nunca en git):
```yaml
# local — default
storage:
  provider: local
  base_path: output/

# S3
storage:
  provider: s3
  bucket: mi-bucket
  region: us-east-1
  credentials:
    access_key: ${env:AWS_ACCESS_KEY}
    secret_key: ${env:AWS_SECRET_KEY}

# Google Cloud Storage
storage:
  provider: gcs
  bucket: mi-bucket
  credentials:
    key_file: ${env:GCS_KEY_FILE}

# Azure Blob
storage:
  provider: azure
  container: mi-container
  credentials:
    connection_string: ${env:AZURE_CONNECTION_STRING}
```

Usa `fsspec` como librería base — estándar de la industria,
usado por Pandas, Dask, DuckDB, Prefect, etc.

Las credenciales viven en variables de entorno — nunca en el XML.
El XML es siempre seguro para commitear a git.

### Hands externos pendientes
- [ ] `scrapling-call` — scraping con Scrapling
- [ ] `playwright-call` — scraping con Playwright
- [ ] `send-mail` — envío de correos
- [ ] `ftp-call`, `ftp-get`, `ftp-put`, `ftp-list` — operaciones FTP
- [ ] `zip`, `zip-entry` — compresión de archivos
- [ ] `database-call` — consultas a base de datos

---

## 💡 Prioridad Baja / Futuro

### IDE — Editor visual
Editor web con:
- Panel de contexto — muestra variables activas en tiempo real
  - Variables sensibles muestran `***`
- Árbol de ejecución — visualiza el flujo del workflow
- Editor XML con syntax highlighting
- Ejecución paso a paso con breakpoints
- Inspector de variables

### Breakpoint
Pausar la ejecución para inspeccionar el contexto:
```xml
<breakpoint/>
```

### Heartbeat
Detectar si el workflow está vivo durante ejecuciones largas:
```xml
<francis-workflow heartbeat="30000" max-idle="5">
```
- Cada 30 segundos emite `[HEARTBEAT] proceso vivo — iteración 23`
- Si hay más de 5 heartbeats sin actividad → cierra limpiamente

### Proxy management
- Pool de proxies con rotación automática
- Verificación con `match-string` o `match-xpath`

### `fs` — Objeto de utilidades del sistema
Disponible en todas las expresiones:
```xml
${fs.now()}                    <!-- fecha/hora actual -->
${fs.uuid()}                   <!-- generar UUID -->
${fs.env("API_KEY")}           <!-- leer variable de entorno -->
${fs.random(1, 100)}           <!-- número aleatorio -->
${fs.urlEncode("hola mundo")}  <!-- encodear URL -->
```

### FastAPI — REST API
Exponer Francis Suite como API REST:
```
POST /run         — ejecutar workflow
GET  /status/:id  — estado de una ejecución
GET  /context/:id — variables del contexto en tiempo real
```

---

## ✅ Completado

- [x] Core: variables, nodes, context, registry, parser, session, events, runtime
- [x] Expression engine con `${variable}`, arithmetic, comparisons, `toBoolean()`, `isEmpty()`, etc.
- [x] Hands core: log, box-def, box, sleep, empty, httpx-call, convert-html-to-xml
- [x] xpath-extract, loop, while, if, else, case, try, catch, exit
- [x] function-create, function-call, function-param, function-return
- [x] regex, text-format, text-split, evaluate, build-list, call-workflow
- [x] convert-json-to-xml, convert-xml-to-json
- [x] file-read, file-write, file-download, file-upload, file-manage
- [x] shared-box-def, shared-box con `replace` attribute
- [x] `replace` attribute en function-create
- [x] Scoping: "si no se toca, no cambia" — while y loop sin new_scope()
- [x] engine.resolve() en todos los atributos que soportan variables
- [x] 54 tests pasando