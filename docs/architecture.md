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

## Próximos archivos

| Archivo | Responsabilidad | Estado |
|---|---|---|
| `core/variables.py` | Tipos de variables | ✅ Creado |
| `core/nodes.py` | Nodo XML parseado | ✅ Creado |
| `core/context.py` | Store de variables con scope | 🔲 Pendiente |
| `core/registry.py` | Registro de plugins | 🔲 Pendiente |
| `core/parser.py` | XML → árbol de FNodes | 🔲 Pendiente |
| `core/session.py` | Sesión de ejecución | 🔲 Pendiente |
| `core/runtime.py` | Motor de ejecución | 🔲 Pendiente |
| `core/events.py` | Sistema de eventos | 🔲 Pendiente |
| `plugins/base.py` | Clase base de plugins | 🔲 Pendiente |