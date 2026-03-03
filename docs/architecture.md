# Francis Suite — Architecture Guide

Guía técnica del proyecto. Explica qué hace cada parte del código,
por qué existe, y cómo se relaciona con el resto.

---

## El problema que resuelve Francis Suite

Quieres hacer web scraping pero no quieres escribir código Python
cada vez. En vez de eso, escribes un archivo XML que describe
qué hacer, y Francis Suite lo ejecuta.
```xml
<francis-workflow>
    <box-def var="pagina">
        <http-call url="https://ejemplo.com"/>
    </box-def>
    <log>${pagina}</log>
</francis-workflow>
```

Francis Suite lee ese XML, lo convierte en un árbol de objetos,
y ejecuta cada etiqueta como un plugin.

---

## Pipeline de ejecución
```
workflow.xml
    ↓
Parser (lxml)       lee el XML y construye un árbol de FNodes
    ↓
Registry            resuelve cada tag a su clase Plugin
    ↓
Session             crea una sesión con UUID y métricas
    ↓
Runtime             camina el árbol y ejecuta cada plugin
    ↓
Plugin.execute()    corre la lógica, devuelve un FVariable
    ↓
Context             guarda el resultado en variables con scope
    ↓
Events              notifica inicio, fin, o error
```

---

## core/variables.py

### ¿Qué problema resuelve?

Cada plugin hace algo y devuelve un resultado. Ese resultado
necesita un tipo común para que cualquier plugin pueda recibirlo
sin importar qué haya adentro.

### Clases

**`FVariable`** — clase base abstracta. Define que toda variable
debe saber hacer tres cosas: convertirse a string, convertirse a
lista, y decir si está vacía. Nunca se usa directamente.

**`FNodeVariable`** — la más común. Guarda un solo valor:
string, número, HTML, XML, o bytes. La mayoría de plugins
devuelven esto.
```python
var = FNodeVariable("<html>...</html>")
var.to_string()  # "<html>...</html>"
var.is_empty()   # False
```

**`FListVariable`** — guarda una lista de FVariables. La devuelve
por ejemplo `xpath-extract` cuando encuentra múltiples nodos.
```python
lista = FListVariable([FNodeVariable("uno"), FNodeVariable("dos")])
lista.to_string()  # "unodos"
len(lista)         # 2
```

**`FEmptyVariable`** — representa nada. Singleton: solo existe
una instancia en toda la ejecución. La devuelven plugins como
`<empty>` o cuando no hay resultado.

### ¿Por qué no usar strings y listas de Python directamente?

Porque necesitamos polimorfismo. Un plugin que recibe una variable
no necesita saber qué hay adentro — llama `.to_string()` y listo.
Esto hace el código más limpio y extensible.

---

## core/nodes.py

### ¿Qué problema resuelve?

Cuando el parser lee el XML, necesita una estructura Python para
representar cada etiqueta. `FNode` es esa estructura.

### Clase FNode

Cada etiqueta XML se convierte en un FNode:
```xml
<http-call url="https://ejemplo.com" method="GET"/>
```
```python
FNode(tag="http-call", attrs={"url": "https://ejemplo.com", "method": "GET"})
```

El XML completo se convierte en un árbol de FNodes:
```
FNode(tag="francis-workflow")
└── FNode(tag="box-def", attrs={"var": "pagina"})
    └── FNode(tag="http-call", attrs={"url": "https://ejemplo.com"})
```

El runtime después camina ese árbol de arriba a abajo y ejecuta
cada nodo.

### Métodos importantes

- `get_attr(name, default)` — obtiene un atributo, con valor por defecto
- `require_attr(name)` — obtiene un atributo requerido, lanza error si falta
- `children_by_tag(tag)` — filtra hijos por nombre de tag
- `first_child_by_tag(tag)` — primer hijo con ese tag

---


## core/context.py

### ¿Qué problema resuelve?

Durante la ejecución, los plugins necesitan guardar y leer variables.
`FContext` es ese almacén. Soporta scopes anidados — las variables
definidas dentro de un loop o función no existen fuera.

### Cómo funciona el scope
```
FContext
├── scope global: { pagina, baseUrl }
└── scope loop:   { item, index }
    ← al salir del loop, item e index desaparecen
```

### Métodos importantes

- `set(name, value)` — guarda variable en el scope actual
- `get(name)` — busca de adentro hacia afuera, devuelve FEmptyVariable si no existe
- `set_global(name, value)` — guarda directo en el scope global
- `new_scope()` — context manager que crea y destruye un scope automáticamente

### Ejemplo
```python
ctx = FContext()
ctx.set("url", FNodeVariable("https://ejemplo.com"))

with ctx.new_scope():
    ctx.set("item", FNodeVariable("temporal"))
    ctx.get("item")  # existe

ctx.get("item")  # FEmptyVariable — ya no existe
```

## core/registry.py

### ¿Qué problema resuelve?

Cuando el runtime encuentra un nodo con tag `http-call`, necesita
saber qué clase Python ejecutar. El Registry es ese mapa.

### Cómo funciona
```
"http-call"      →  HttpCallHand
"xpath-extract"  →  XPathExtractHand
"loop"           →  LoopHand
```

Los hands se registran solos usando el decorador `@hand`:
```python
@hand(tag="http-call")
class HttpCallHand(AbstractHand):
    ...
```

Cuando Python importa ese módulo, el decorador se ejecuta
automáticamente y registra la clase en el Registry.

### Métodos importantes

- `register(tag, class)` — registra un hand (lo llama el decorador)
- `get(tag)` — devuelve la clase o None si no existe
- `require(tag)` — devuelve la clase o lanza error si no existe
- `all_tags()` — lista todos los tags registrados
- `reset()` — solo para tests, nunca en producción

### El decorador @hand
```python
# En vez de registrar manualmente:
HandRegistry.instance().register("http-call", HttpCallHand)

# Usamos el decorador:
@hand(tag="http-call")
class HttpCallHand(AbstractHand):
    ...
```

## core/parser.py

### ¿Qué problema resuelve?

Es el primer paso del pipeline. Lee el archivo XML del workflow
y lo convierte en un árbol de FNodes que el runtime puede ejecutar.

### Cómo funciona
```
workflow.xml
    ↓
lxml etree.fromstring()
    ↓
_element_to_fnode() recursivo
    ↓
FNode tree
```

### Métodos principales

- `parse_file(path)` — lee un archivo XML del disco
- `parse_string(xml)` — parsea desde un string (útil para tests)
- `parse_bytes(xml)` — método central, los otros dos llaman este

### Validaciones

- El archivo debe existir
- El XML debe ser válido
- El tag raíz debe ser `<francis-workflow>`

### Ejemplo
```python
parser = FParser()
root = parser.parse_file("workflow.xml")
# root = FNode(tag="francis-workflow", children=[...])

# O desde string (útil en tests):
root = parser.parse_string("""
    <francis-workflow>
        <log>Hola mundo</log>
    </francis-workflow>
""")
```

## core/session.py

### ¿Qué problema resuelve?

Cada vez que ejecutas un workflow, Francis Suite necesita un
contenedor que agrupe todo lo que pasa durante esa ejecución:
su identidad, su estado, sus métricas y sus variables.

### Estados posibles
```
CREATED → RUNNING → COMPLETED
                  → FAILED
                  → CANCELLED
```

### Qué contiene una sesión

- `id` — UUID único, identifica esta ejecución
- `status` — estado actual (SessionStatus)
- `context` — el FContext con todas las variables
- `created_at / started_at / finished_at` — timestamps
- `duration` — segundos que tardó la ejecución
- `error` — la excepción si la sesión falló

### Ejemplo
```python
session = FrancisSession(workflow_name="mi-workflow")
session.start()
# ... ejecución ...
session.complete()

print(session.id)        # "abc-123-..."
print(session.status)    # SessionStatus.COMPLETED
print(session.duration)  # 2.34 (segundos)
```

## core/events.py

### ¿Qué problema resuelve?

Durante la ejecución, distintas partes del sistema necesitan
saber qué está pasando sin estar directamente conectadas entre sí.
El EventBus es el canal de comunicación entre ellas.

### Patrón publish/subscribe
```
Runtime                    Listeners
  │                            │
  ├─ emit(SessionStarted)  ──► Logger
  ├─ emit(HandStarted)     ──► IDE
  ├─ emit(HandCompleted)   ──► IDE
  └─ emit(SessionFailed)   ──► Logger, IDE
```

### Eventos disponibles

**Sesión:**
- `SessionStartedEvent` — la sesión empezó
- `SessionCompletedEvent` — la sesión terminó bien
- `SessionFailedEvent` — la sesión falló
- `SessionCancelledEvent` — la sesión fue cancelada

**Hands:**
- `HandStartedEvent` — un hand empezó a ejecutarse
- `HandCompletedEvent` — un hand terminó bien
- `HandFailedEvent` — un hand lanzó un error

### Ejemplo
```python
bus = EventBus()

@bus.on(SessionStartedEvent)
def on_start(event):
    print(f"Session {event.session_id} started")

bus.emit(SessionStartedEvent(session_id="abc-123"))
```

### Agregar un logger en el futuro

Solo hay que suscribirse a los eventos que interesan:
```python
@bus.on(HandFailedEvent)
def log_error(event):
    logger.error(f"Hand <{event.tag}> failed: {event.error}")
```

El runtime no cambia nada — sigue emitiendo eventos igual.

## hands/base.py

### ¿Qué problema resuelve?

Todo hand necesita acceso al nodo XML, a la sesión, y al contexto
de variables. `AbstractHand` provee todo eso — los hands concretos
solo tienen que implementar `execute()`.

### Contrato
```python
@hand(tag="mi-tag")
class MiHand(AbstractHand):
    def execute(self) -> FVariable:
        # tu lógica aquí
        return FNodeVariable("resultado")
```

### Lo que hereda cada hand

- `self.node` — el FNode con tag, atributos e hijos
- `self.session` — la sesión actual
- `self.context` — atajo a session.context
- `self.attr(name)` — obtiene un atributo XML
- `self.require_attr(name)` — atributo requerido, error si falta
- `self.get_body_text()` — texto entre las etiquetas
- `self.has_children()` — si tiene nodos hijos

### Ejemplo
```python
@hand(tag="log")
class LogHand(AbstractHand):
    def execute(self) -> FVariable:
        text = self.get_body_text()
        print(text)
        return FNodeVariable(text)
```

## core/runtime.py

### ¿Qué problema resuelve?

Es el corazón del framework. Toma el árbol de FNodes que produjo
el parser y lo ejecuta nodo por nodo, gestionando la sesión
y emitiendo eventos en cada paso.

### Cómo funciona
```
FRuntime.run(root)
    ↓
Crea FrancisSession
    ↓
Emite SessionStartedEvent
    ↓
_execute_children(root)
    ↓
Por cada hijo:
    execute_node(child)
        ↓
    HandRegistry.require(tag) → HandClass
        ↓
    HandClass(node, session).execute()
        ↓
    Devuelve FVariable
    ↓
Emite SessionCompletedEvent (o SessionFailedEvent)
    ↓
Devuelve FrancisSession con status y métricas
```

### Métodos principales

- `run(root, workflow_name)` — ejecuta el workflow completo,
  siempre devuelve una sesión, nunca lanza excepciones
- `execute_node(node, session)` — ejecuta un nodo individual
- `_execute_children(node, session)` — ejecuta todos los hijos
  de un nodo en orden

### Ejemplo
```python
parser = FParser()
runtime = FRuntime()

root = parser.parse_file("workflow.xml")
session = runtime.run(root, workflow_name="mi-workflow")

print(session.status)    # SessionStatus.COMPLETED
print(session.duration)  # 1.23
```

## Próximos archivos

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `core/variables.py` | Tipos de variables | ✅ Creado |
| `core/nodes.py` | Nodo XML parseado | ✅ Creado |
| `core/context.py` | Store de variables con scope | ✅ Creado |
| `core/registry.py` | Registro de plugins | ✅ Creado |
| `core/parser.py` | XML → árbol de FNodes | ✅ Creado |
| `core/session.py` | Sesión de ejecución | ✅ Creado |
| `core/events.py` | Sistema de eventos | ✅ Creado |
| `hands/base.py` | Clase base de plugins | ✅ Creado |
| `core/runtime.py` | Motor de ejecución | ✅ Creado |
