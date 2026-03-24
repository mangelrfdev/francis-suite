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

SÍ necesitan resolve: path, url, to, expression, ms, timeout, name en function-call.
NO necesitan resolve: flags booleanos, opciones fijas (level), nombres internos (name en box-def).

### REGLA 2 — Scoping: "si no se toca, no cambia"

Las variables del contexto solo cambian cuando algo las toca explícitamente.

- while y loop NO usan new_scope()
- function-call SÍ usa new_scope()

### REGLA 3 — Compatibilidad universal

Todo el código debe funcionar igual en Windows, Linux y Mac.
- Rutas: siempre usar pathlib.Path — nunca strings con / o \ hardcodeados
- Rutas en tests: siempre usar .as_posix() al insertar en f-strings de XML
- Encoding: siempre especificar utf-8 explícitamente al leer o escribir archivos
- Saltos de línea: nunca asumir \n o \r\n — dejar que Python lo maneje
- Procesos externos: nunca llamar comandos del sistema que sean OS-específicos

### REGLA 4 — Nombres de atributos autodescriptivos

Los nombres de atributos deben ser autodescriptivos.
El usuario debe entender qué hace un atributo solo con leerlo,
sin necesitar documentación.

Ejemplos aplicados:
- search-in-subfolders en vez de recursive
- force-delete, force-move, force-copy en vez de force u overwrite
- size-format en vez de unit
- to en vez de dest
- include-metadata en vez de meta o with-meta

### REGLA 5 — Sensitive variables

- Nunca usar resolve_body_text() en contextos de display
- Usar resolve_body_text_display() o engine.resolve_display() para logs y UI
- to_string() → valor real para el engine
- to_display() → valor maskeado si sensitive, para logs y UI
- Auto-sensitive: api_key, token, password, secret, credential, auth, private_key

### REGLA 6 — FRecord en el contexto

- FRecord hereda de FVariable (importada de base.py)
- Se guarda como shared-box en el contexto global
- Verificar con isinstance(record, FRecord) — nunca con hasattr
- to_string() retorna "[RECORD:nombre:count]" — nunca data real
- Los hands de record pasan self.session a save() y save_meta()

---

## core/base.py ✅ NUEVO

FVariable — clase base abstracta única del sistema.
Vive aquí para evitar circular imports entre variables.py y records.py.
Ambos módulos importan FVariable desde base.py.

```python
from francis_suite.core.base import FVariable
```

NUNCA mover FVariable de base.py.

---

## core/variables.py ✅

Importa FVariable de base.py.
FNodeVariable — valor único (string, bytes, número) con soporte sensitive.
FListVariable — lista de FVariables.
FEmptyVariable — representa nada. Singleton.

Funciones: is_sensitive_name(), mask_sensitive()

---

## core/records.py ✅ NUEVO

Sistema de records estructurados con schema, metadata y persistencia.
Importa FVariable de base.py.

Clases:
- FRecordField — un campo con tipo, validación y normalización
- FRecordGroup — grupo de campos
- FRecordSchema — schema completo con grupos y metadata pública
- FRecord(FVariable) — colección de rows + schema + metadata + save()

FRecord hereda de FVariable — vive en el contexto como shared-box.

### Tipos de field:
```
string, integer, decimal (Decimal exacto), boolean
date (→YYYY-MM-DD), datetime (→YYYY-MM-DDTHH:MM:SS)
url, email, uuid, null-if-empty
```

### Metadata privada automática (siempre disponible):
```
session_id, workflow_path, francis_suite_version, hostname
sistema_operativo, python_version, status, error, inicio, fin
duracion_segundos, ram_peak_mb (psutil), ram_promedio_mb, rows_por_segundo
total_rows, rows_completados, rows_con_campos_vacios
rows_fallidos, campos_nulos_total, porcentaje_completitud
+ campos agregados via <record-private-metadata>
```

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

Motor de expresiones con soporte sensitive.

engine.resolve()         → valor real, para el engine
engine.resolve_display() → valor maskeado si sensitive, para logs y UI
engine.evaluate()        → evaluación aritmética y lógica

Métodos en variables: toBoolean(), isEmpty(), toUpperCase(), toLowerCase(), trim().

---

## core/runtime.py ✅

Ejecuta el árbol de FNodes.
Métodos:
- run(root, workflow_name) — crea sesión internamente
- run_session(root, session) — acepta sesión pre-construida con variables inyectadas

---

## hands/base.py ✅

AbstractHand — clase base de todos los hands.

```python
@hand(tag="mi-tag")
class MiHand(AbstractHand):
    def execute(self) -> FVariable:
        return FNodeVariable("resultado")
```

Disponible en cada hand:
- self.node, self.session, self.context, self.runtime
- self.attr, self.require_attr
- self.resolve_body_text() — valor real
- self.resolve_body_text_display() — valor maskeado para logs
- self.has_children, self.execute_children, self.execute_child

---

## Hands implementados ✅

```
Variables:    box-def (sensitive), box
              shared-box-def (replace, sensitive), shared-box
              evaluate

HTTP:         httpx-call (response: text, binary, stream)
              httpx-header, httpx-param

Parsing:      convert-html-to-xml, xpath-extract
              convert-json-to-xml, convert-xml-to-json

Converts:     convert-binary-to-base64, convert-base64-to-binary
              convert-text-to-base64, convert-base64-to-text
              convert-json-to-csv, convert-csv-to-json, convert-xml-to-csv
              convert-text-to-url, convert-url-to-text
              convert-html-entities-to-text

Regex:        regex, regex-pattern, regex-input, regex-result

Text:         compose, text-split

Flow:         while (max-loops), loop (loop-list, loop-body, index, max-loops)
              if, else, case, try, catch, exit, sleep
              pause-task (FRANCIS_ENV=dev pausa, prod warning)

Functions:    function-create (replace), function-call, function-param, function-return

Files:        file-read, file-write (encoding: utf-8, binary, newline)
              file-manage (8 actions)

Records:      record-create, record-add, record-last-added, record-count
              record-save (json, csv, ndjson)
              record-save-metadata (solo metadata privada, sin rows)
              record-private-metadata (agrega metadata en cualquier parte)

Misc:         log (sensitive auto-masked), build-list, call-workflow
```

---

## Gestión de contenido HTTP

| response | Cuándo usarlo |
|---|---|
| text (default) | HTML, XML, JSON, CSV, texto |
| binary | PDF, Excel, imágenes, ZIP |
| stream | Video, audio, archivos +50MB |

file-download y file-upload fueron eliminados.
httpx-call + file-write los reemplaza completamente.

---

## Sistema de records — flujo completo

```xml
<!-- 1. definir schema con metadata opcional -->
<record-create name="propiedadesRecords">
    <record-metadata>
        <metadata-field name="fuente">Portal Inmobiliario</metadata-field>
        <metadata-field name="rows_completados"/>
    </record-metadata>
    <record-set-group name="propiedad" required="true">
        <record-set-field name="titulo" type="string"  required="true"/>
        <record-set-field name="precio" type="integer" required="true"/>
    </record-set-group>
</record-create>

<!-- 2. loop de scraping -->
<loop item="item" index="i">
    <loop-body>
        <record-add to="propiedadesRecords">
            <record-add-group name="propiedad">
                <record-add-field name="titulo">${titulo}</record-add-field>
                <record-add-field name="precio">${precio}</record-add-field>
            </record-add-group>
        </record-add>

        <!-- metadata privada en cualquier parte del workflow -->
        <record-private-metadata to="propiedadesRecords">
            <private-metadata-add-field name="paginas_procesadas">${i}</private-metadata-add-field>
        </record-private-metadata>
    </loop-body>
</loop>

<!-- 3. guardar data — metadata pública se incluye si fue declarada -->
<record-save from="propiedadesRecords" format="ndjson" path="output/propiedades.ndjson"/>

<!-- 4. guardar solo metadata privada — para vos, sin duplicar los rows -->
<record-save-metadata from="propiedadesRecords" path="output/internal/meta.json"/>
```

---

## CLI

```bash
francis-suite run workflow.xml
francis-suite run workflow.xml --param ciudad=santiago --param paginas=10
```

Variables inyectadas con --param se guardan como shared-box antes de ejecutar.
Valores sensibles nunca aparecen en logs — solo "[PARAMS] Context variables loaded."

---

## Futuro del proyecto

### RecordKey — próximo a implementar
Sistema de deduplicación por hash de campos inmutables.
record-key dentro de record-create define los campos del key.
Si el key ya existe al hacer record-add → skip silencioso con log.

### Formatos adicionales de record-save
xml, excel (con hoja de metadata), parquet, html, txt con template.

**Guía de diseño (metadata por formato, atributos, ejemplos):** [guides/record-save-formats.md](guides/record-save-formats.md).

### Plugin VSCode
Syntax highlighting, autocompletado, tree de ejecución, inspector de variables,
navegador de records, controles run/pause/step/resume/stop.
Ver ADR-003 para diseño completo.

### Storage Provider
fsspec, S3, GCS, Azure Blob. Configurado en francis-config.yaml (nunca en git).

### FastAPI REST
POST /run, GET /status/:id, GET /context/:id, WS /ws/:id.

### YAML parser
FYamlParser convierte YAML → FNode tree. El engine no cambia.

---

## Estado del proyecto

| Módulo | Responsabilidad | Estado |
|---|---|---|
| core/base.py | FVariable base única | ✅ |
| core/variables.py | FNodeVariable, FListVariable, FEmptyVariable | ✅ |
| core/records.py | FRecord, FRecordSchema, metadata | ✅ |
| core/nodes.py | Nodo XML parseado | ✅ |
| core/context.py | Store de variables con scope | ✅ |
| core/registry.py | Registro de hands | ✅ |
| core/parser.py | XML a árbol de FNodes | ✅ |
| core/session.py | Sesión de ejecución | ✅ |
| core/events.py | Sistema de eventos | ✅ |
| core/expressions.py | Motor de expresiones con resolve_display | ✅ |
| hands/base.py | Clase base con resolve_body_text_display | ✅ |
| core/runtime.py | Motor con run() y run_session() | ✅ |
| Todos los hands core | Ver lista completa arriba | ✅ |
| Sistema de records base | record-create hasta record-save-metadata | ✅ |
| Sistema de metadata | psutil, calidad de datos, trazabilidad | ✅ |
| pause-task | pausa en dev, warning en prod | ✅ |
| CLI --param | inyección segura de variables | ✅ |
| Compatibilidad universal | pathlib, as_posix(), utf-8 | ✅ |
| Auto metadata privada por sesión | `sessions/<session_id>/*_private_metadata.json` sin XML; `FRANCIS_AUTO_RECORD_METADATA=0` desactiva | ✅ |
| Tests | todos compatibles Windows/Linux/Mac | ✅ |
| RecordKey | deduplicación por hash | ⬜ |
| Formatos xml, excel, parquet | record-save adicional | ⬜ |
| record-filter, record-sort | filtrado y ordenamiento | ⬜ |
| workflow-param como hand XML | --param ya funciona en CLI | ⬜ |
| Plugin VSCode | syntax highlighting y debug | ⬜ |
| Nuevas fuentes | pdf, excel, ia, playwright | ⬜ |
| Storage cloud | fsspec | ⬜ |
| FastAPI REST | API de ejecución | ⬜ |
| YAML parser | formato alternativo | ⬜ |
