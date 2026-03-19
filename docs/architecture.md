# Francis Suite — Architecture Guide

Guía técnica completa del proyecto.

---

## ¿Qué es Francis Suite?

Framework universal de extracción y procesamiento de datos.
Low-code, declarativo, extensible, cloud-ready.

No es solo scraping — extrae data de cualquier fuente:
web, PDF, Excel, JSON, APIs, imágenes con IA, bases de datos.

---

## Filosofía central

```
Todo se guarda en boxes.
Una box es la unidad de datos del framework.
Todo resultado se guarda en una box.
Todo lo que se quiere usar después, vive en una box.
```

---

## Pipeline de ejecución

```
workflow.xml
    ↓
FParser         lee el XML y construye un árbol de FNodes
    ↓
FRuntime        camina el árbol y ejecuta cada hand
    ↓
Hand.execute()  corre la lógica, devuelve un FVariable
    ↓
FContext        guarda el resultado en variables (boxes)
    ↓
EventBus        notifica inicio, fin, o error
```

FNode es el puente universal. Todo lo que venga de afuera
se convierte a FNode. El engine nunca sabe el formato de origen.
Esto permite agregar YAML en el futuro sin cambiar nada del engine.

---

## Reglas de desarrollo de Hands

### REGLA 1 — engine.resolve() en atributos

Todo atributo que el usuario pueda escribir como ${variable}
DEBE pasar por engine.resolve() antes de usarse.

```python
engine = FrancisExpression(self.context)
url  = engine.resolve(self.require_attr("url"))
path = engine.resolve(self.attr("path", "output/"))
```

SÍ necesitan resolve: path, url, dest, expression, ms, timeout, name en function-call.
NO necesitan resolve: flags booleanos (append, mkdir), opciones fijas (level), nombres internos (name en box-def).

### REGLA 2 — Scoping: "si no se toca, no cambia"

Las variables del contexto solo cambian cuando algo las toca explícitamente.

- while y loop NO usan new_scope()
- function-call SÍ usa new_scope()

### REGLA 3 — Compatibilidad universal:

Todo el código debe funcionar igual en Windows, Linux y Mac.
- Rutas: siempre usar pathlib.Path — nunca strings con / o \ hardcodeados
- Rutas en tests: siempre usar .as_posix() al insertar en f-strings de XML
- Encoding: siempre especificar utf-8 explícitamente al leer o escribir archivos
- Saltos de línea: nunca asumir \n o \r\n — dejar que Python lo maneje
- Procesos externos: nunca llamar comandos del sistema que sean OS-específicos

---

## core/variables.py ✅

FVariable — clase base abstracta.
FNodeVariable — valor único (string, número, HTML, XML, bytes).
FListVariable — lista de FVariables.
FEmptyVariable — representa nada. Singleton.

---

## core/nodes.py ✅

FNode representa cada etiqueta XML como objeto Python.
Métodos: get_attr, require_attr, children_by_tag, first_child_by_tag.

---

## core/context.py ✅

FContext — almacén de variables con scopes anidados.
Métodos: set, get, set_global, get_global, set_shared_box, get_shared_box, new_scope.

---

## core/registry.py ✅

Mapa de tags a clases Hand. Los hands se registran con @hand(tag="nombre").
Métodos: get, require, all_tags, reset.

---

## core/parser.py ✅

Lee XML y construye árbol de FNodes.
Métodos: parse_file, parse_string, parse_bytes.
Validaciones: archivo existe, XML válido, tag raíz = francis-workflow.
Futuro: FYamlParser convierte YAML a FNode tree. El engine no cambia.

---

## core/session.py ✅

Contenedor de la ejecución.
Estados: CREATED, RUNNING, COMPLETED, FAILED, CANCELLED.
Contiene: id (UUID), status, context, timestamps, duration, error.

---

## core/events.py ✅

EventBus — canal de comunicación entre partes del sistema.
El Plugin VSCode usará estos eventos para el tree de ejecución en tiempo real.

Eventos de sesión: SessionStartedEvent, SessionCompletedEvent,
SessionFailedEvent, SessionCancelledEvent.

Eventos de hands: HandStartedEvent, HandCompletedEvent, HandFailedEvent.

---

## core/expressions.py ✅

Motor de expresiones.

engine.resolve("${base_url}/page-${pagina}.html")
engine.evaluate("${contador} + 1")
engine.evaluate("${precio} > 1000")

Métodos en variables: toBoolean(), isEmpty(), toUpperCase(), toLowerCase(), trim().

---

## core/runtime.py ✅

Ejecuta el árbol de FNodes.
Métodos: run(root, workflow_name), execute_node, _execute_children.

---

## hands/base.py ✅

AbstractHand — clase base de todos los hands.

```python
@hand(tag="mi-tag")
class MiHand(AbstractHand):
    def execute(self) -> FVariable:
        return FNodeVariable("resultado")
```

Disponible en cada hand: self.node, self.session, self.context,
self.attr, self.require_attr, self.resolve_body_text,
self.has_children, self.execute_children, self.execute_child.

---

## Hands implementados ✅

```
Variables:    box-def, box, shared-box-def (replace), shared-box, evaluate
HTTP:         httpx-call, httpx-header, httpx-param
Parsing:      convert-html-to-xml, xpath-extract
              convert-json-to-xml, convert-xml-to-json
Regex:        regex, regex-pattern, regex-input, regex-result
Text:         compose, text-split
Flow:         while (max-loops), loop (loop-list, loop-body, index, max-loops)
              if, else, case, try, catch, exit, sleep
Functions:    function-create (replace), function-call, function-param, function-return
Files:        file-read, file-write, file-download, file-upload, file-manage
Misc:         log, build-list, call-workflow
```

---

## Hands pendientes — Urgentes ⬜

- file-write — agregar newline="true"
- file-manage — agregar mkdir, exists, rename, size
- workflow-param — parámetros de entrada al workflow
- sensitive — atributo para box-def y shared-box-def

---

## Hands pendientes — Sistema de Records ⬜

Diseño acordado, pendiente codear.

Ciclo de vida:
```
1. DEFINIR   → record-create
2. AGREGAR   → record-add
3. VERIFICAR → record-last-added
4. GUARDAR   → record-save
```

```xml
<!-- 1. definir schema -->
<record-create name="productosRecords">
    <record-set-group name="productos" required="true">
        <record-set-field name="nombre_visible" type="string" required="true"/>
        <record-set-field name="precio" type="integer" required="true"/>
        <record-set-field name="marca" type="string" required="false"/>
    </record-set-group>
    <record-set-group name="empaques" required="false">
        <record-set-field name="cantidad" type="integer" required="false"/>
        <record-set-field name="unidad" type="string" required="false"/>
    </record-set-group>
</record-create>

<!-- 2. agregar dentro del loop -->
<record-add to="productosRecords">
    <record-add-group name="productos">
        <record-add-field name="nombre_visible">${nombre}</record-add-field>
        <record-add-field name="precio">${precio}</record-add-field>
    </record-add-group>
</record-add>

<!-- 3. verificar -->
<record-last-added from="productosRecords"/>

<!-- 4. guardar -->
<record-save from="productosRecords" format="json" path="output/productos.json"/>
<record-save from="productosRecords" format="csv" path="output/productos.csv"/>
<record-save from="productosRecords" format="ndjson" path="output/productos.ndjson"/>
```

Tipos de field: string, integer, decimal, boolean, date, datetime, otros relacionados a base de datos, se entiende?

Formatos: json, csv, ndjson, txt, html, xml, etc.

Modos actuales para no colapsar la memoria(son ideas,se necesita pensar seriamente en las ideas): mode="batch" (default), mode="stream" (sin límite RAM).

Otras etiquetas: record-store-all, record-view-content, record-count.

Nota de memoria: Con mode="stream" la box guarda solo referencia al archivo.
El Plugin VSCode navegará desde disco: record 1 de 1000. Nunca se carga todo en RAM.

---

## Hands pendientes pero que aun no son prioridad — Nuevas fuentes ⬜

```
use-ia          — análisis con IA (imágenes a JSON estructurado)
playwright-call — automatización de browser
scrapling-call  — scraping avanzado
```
---

## Futuro del proyecto ⬜

### Plugin VSCode
- Syntax highlighting para XML de Francis Suite
- Autocompletado de hands y atributos
- Tree de ejecución en tiempo real (usa EventBus)
- Navegador de records: por ejemplo si son 1000 records que se pueda navegar 1 a 1, botones anterior/siguiente
- ventana para visualizar data junto a switch JSON/HTML/TEXT/CSV/XML/PERSONALIZADO en el visualizador/ventana.
- Variables sensibles muestran *** en logs.

### Storage Provider — Cloud-ready - Elaborar cuando ya todo lo primordial este listo.
Usa fsspec. Configuración en francis-config.yaml (nunca en git).
Soporta: local, S3, GCS, Azure Blob.

### fs — Objeto de utilidades - Elaborar cuando ya todo lo primordial este listo.
${fs.uuid()}, ${fs.now()}, ${fs.env("KEY")}, ${fs.random(1,100)}, ${fs.urlEncode("")}.

### FastAPI REST - Elaborar cuando ya todo lo primordial este listo.
POST /run, GET /status/:id, GET /context/:id.

### YAML como formato alternativo - Pensar la elaboracion cuando ya todo lo primordial este listo.
FYamlParser convierte YAML a FNode tree. El engine no cambia nada.

---

## Gestión de contenido HTTP por formato

`httpx-call` tiene un atributo `response` que controla cómo se devuelve
el contenido de la respuesta HTTP.

### Valores de `response`

| Valor | Cuándo usarlo |
|---|---|
| `text` (default) | HTML, XML, JSON, CSV, texto plano |
| `binary` | PDF, Excel, Word, ZIP, imágenes |
| `stream` | Video, audio, archivos grandes (+50MB) |

### Regla general

```
Es texto                    → text (default)
Es binario pequeño/mediano  → binary
Es binario grande (+50MB)   → stream obligatorio
Requiere base64             → lo maneja la hand destino internamente
```

### Base64

Base64 NO es una opción de `response`. Si una API destino requiere
base64, la hand correspondiente (`use-ia`, etc.) maneja la conversión
internamente. El usuario nunca necesita convertir a base64 manualmente.

### Flujo completo por tipo de contenido

**HTML:**
```xml
<box-def name="html">
    <httpx-call url="https://ejemplo.com"/>
</box-def>
```

**JSON:**
```xml
<box-def name="data">
    <httpx-call url="https://api.ejemplo.com/productos"/>
</box-def>
```

**PDF o Excel:**
```xml
<box-def name="reporte">
    <httpx-call url="https://ejemplo.com/reporte.pdf" response="binary"/>
</box-def>
<file-write path="downloads/reporte.pdf" encoding="binary">
    <box name="reporte"/>
</file-write>
```

**Imagen para IA:**
```xml
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<box-def name="datos">
    <use-ia model="vision">
        <box name="foto"/>
    </use-ia>
</box-def>
```

**Video o audio — stream obligatorio:**
```xml
<httpx-call url="https://ejemplo.com/video.mp4" response="stream" path="downloads/video.mp4"/>
```

### `file-download` y `file-upload`

Estos hands fueron eliminados. `httpx-call` con `response="binary"` o
`response="stream"` + `file-write` cubre todos los casos. Cada cliente
futuro (playwright, scrapling) manejará sus propias descargas
internamente.

---

## Estado del proyecto

| Módulo | Responsabilidad | Estado |
|---|---|---|
| core/variables.py | Tipos de variables | ✅ |
| core/nodes.py | Nodo XML parseado | ✅ |
| core/context.py | Store de variables con scope | ✅ |
| core/registry.py | Registro de hands | ✅ |
| core/parser.py | XML a árbol de FNodes | ✅ |
| core/session.py | Sesión de ejecución | ✅ |
| core/events.py | Sistema de eventos | ✅ |
| core/expressions.py | Motor de expresiones | ✅ |
| hands/base.py | Clase base de hands | ✅ |
| core/runtime.py | Motor de ejecución | ✅ |
| hands/core/*.py | Todos los hands core | ✅ |
| compose | rename de text-format | ✅ |
| Sistema de records | record-create, record-add, etc. | ⬜ |
| workflow-param | parámetros de entrada | ⬜ |
| sensitive | variables sensibles | ⬜ |
| file-manage nuevo | mkdir, exists, rename, size | ⬜ |
| Plugin VSCode | syntax highlighting y debug | ⬜ |
| Nuevas fuentes | pdf, excel, json, api, ia | ⬜ |
| Storage cloud | fsspec | ⬜ |
| FastAPI REST | API de ejecución | ⬜ |
| YAML parser | formato alternativo | ⬜ |
