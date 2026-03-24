# ADR-003 — Debug, Observability, and Plugin VSCode

## Contexto

Francis Suite necesita un sistema de debug, observabilidad y control de
ejecución que permita al desarrollador inspeccionar, pausar, reanudar y
navegar workflows en tiempo real — tanto desde el CLI ahora, como desde
un Plugin VSCode en el futuro.

Este ADR documenta todas las decisiones de diseño relacionadas con:
- Control de ejecución (pause-task, CLI flags)
- Validación de sintaxis
- Plugin VSCode — árbol de ejecución, inspector, visualizador de datos

---

## Decisiones

---

## 1. `<pause-task/>` — Punto de pausa en el workflow

Tag XML que marca un punto de pausa intencional en el código.
No es un error — es una herramienta de debug.

### Comportamiento en dev:
```
[PAUSE-TASK] Workflow paused.
```
El workflow se detiene. No hay forma de reanudarlo hasta que el
Plugin VSCode esté implementado — por ahora es solo una señal de
"aquí hay algo que quiero inspeccionar".

### Comportamiento en prod:
```
WARNING: workflow contains <pause-task/> tags. Remove them before deploying to production.
```
El workflow no corre — falla inmediatamente antes de ejecutar nada.

### Uso correcto:
Usar `<log>` antes de `<pause-task/>` para dar contexto:
```xml
<log>Verificando precio — valor actual: ${precio}</log>
<pause-task/>
```

`<pause-task/>` no tiene atributo `message` — el `<log>` cumple ese rol
de forma consistente con la filosofía del framework.

### Regla:
- `<pause-task/>` nunca debe subirse a producción
- El framework lo detecta y advierte — o falla según el entorno
- En dev no advierte — es el ambiente correcto para usarlo

---

## 2. Entornos — dev vs prod

El framework necesita saber en qué entorno está corriendo para
comportarse correctamente con `<pause-task/>` y otros controles.

### Decisión:
Variable de entorno del sistema `FRANCIS_ENV`:
```bash
FRANCIS_ENV=prod francis-suite run workflow.xml
FRANCIS_ENV=dev  francis-suite run workflow.xml
```
(Equivalente: `python -m francis_suite.cli run …` si ejecutás el módulo sin entrypoint instalado.)

Default: `dev` si no se especifica.

Valores válidos: `dev`, `staging`, `prod`.

---

## 3. CLI — Flags de debug

Antes del Plugin VSCode, el CLI es la interfaz de debug.

```bash
# correr normal
francis-suite run workflow.xml

# modo debug — pausa en cada <pause-task/> y espera Enter para continuar
francis-suite run workflow.xml --debug

# modo step — avanza hand por hand, espera Enter en cada una
francis-suite run workflow.xml --step
```

> **Nota:** `--debug` y `--step` son parte del diseño de este ADR; el CLI actual puede no implementarlos todavía — ver `francis_suite/cli.py`.

### `--debug`:
- El workflow corre normal
- Se detiene en cada `<pause-task/>` y espera Enter para continuar
- Muestra `[PAUSE-TASK] Workflow paused.` en cada pausa
- Al presionar Enter reanuda hasta el próximo `<pause-task/>` o fin

### `--step`:
- Avanza una hand a la vez
- Espera Enter después de cada hand
- No necesita `<pause-task/>` en el XML
- Útil para inspeccionar el estado del contexto hand por hand

### Regla:
- `--debug` y `--step` nunca se usan en producción
- Son la base sobre la que el Plugin VSCode construirá su interfaz visual
- Funcionan en cualquier sistema sin GUI

---

## 4. Validador de sintaxis

Antes de ejecutar cualquier workflow, el framework valida la sintaxis
y reporta errores con número de línea exacto.

### Errores que detecta:
```
ERROR: <loop> at line 45 is missing required <loop-body> child.
ERROR: <loop> at line 45 is missing required <loop-list> child.
ERROR: <function-call name="extraer"> at line 78 — function "extraer" is not defined.
ERROR: Unknown tag <mi-tag> at line 92.
ERROR: <box-def> at line 12 is missing required attribute "name".
ERROR: XML syntax error at line 34 — unclosed tag.
WARNING: <pause-task/> found at line 103. Remove before deploying to production.
```

### Cuándo se ejecuta:
- **Diseño:** antes de cada ejecución y como comando `validate` dedicado.
- **Hoy:** el validador inline y `francis-suite validate` pueden no estar implementados — el `run` parsea el XML y falla si el XML es inválido o hay tags desconocidos.

```bash
# previsto cuando exista el subcomando
francis-suite validate workflow.xml
```

### Relación con el Plugin VSCode:
El validador es la base del syntax highlighting y los errores inline
del plugin — el plugin consume los mismos errores que reporta el CLI.

---

## 5. Plugin VSCode — Visión general

El Plugin VSCode es una extensión que se instala desde el marketplace
de VSCode. Se comunica con Francis Suite via FastAPI — que expone
endpoints REST y WebSocket para control en tiempo real.

### Arquitectura:
```
Plugin VSCode → HTTP/WebSocket → FastAPI → FRuntime → EventBus → Plugin
```

### Funcionalidades:

**Syntax highlighting:**
- Colores para cada tipo de tag — hands, atributos, variables
- Errores inline del validador de sintaxis
- Autocompletado de tags y atributos

**Árbol de ejecución en tiempo real:**
- Muestra cada hand ejecutándose con su estado
- Estados: running, completed, failed, paused
- Al hacer click en una fila del árbol — salta a la línea en el XML
- Muestra en qué punto del árbol va la ejecución actualmente

**Controles de ejecución:**
- ▶ Run — ejecutar workflow
- ⏸ Pause — pausar en cualquier momento
- ⏭ Step — avanzar una hand y pausar
- ▶ Resume — reanudar hasta el próximo pause-task o fin
- ⏹ Stop — detener completamente

**Step granular:**
- Entra dentro de loops, funciones, box-def — cualquier nivel
- Cada iteración de loop cuenta como un paso
- Cada hand dentro de un box-def cuenta como un paso

---

## 6. Inspector de variables

Panel inferior del Plugin VSCode. Al hacer click en cualquier línea
del XML muestra información de esa hand.

### Formato del inspector:

Para `<box-def>`:
```
Hand:   box-def                     [Ver]
Name:   html                        [Ver]
Value:  <!DOCTYPE html><html>...    [Ver]
```

Para `<xpath-extract>`:
```
Hand:   xpath-extract               [Ver]
Expr:   //article...                [Ver]
Value:  (20 results)                [Ver]
```

Para `<convert-html-to-xml>`:
```
Hand:   convert-html-to-xml         [Ver]
Value:  <html><body>...             [Ver]
```

### Regla:
- El valor se trunca en el inspector — no se muestra todo
- Al final de cada fila hay un botón `[Ver]` que abre el Visualizador de Datos
- Si no hay valor todavía (no se ejecutó) — muestra vacío

---

## 7. Visualizador de Datos Universal

Ventana que se abre al hacer click en `[Ver]` en el Inspector.
Es un visualizador universal que soporta múltiples formatos.

### Formato inicial:
Siempre abre en formato `TEXT` — el valor crudo sin procesar.

### Selector de formato (cascada):
```
TEXT → HTML → XML → JSON → CSV
```

Cada formato renderiza el contenido de manera diferente:
- `TEXT` — texto plano, el valor crudo
- `HTML` — renderiza el HTML visualmente como un browser
- `XML` — árbol colapsable de nodos XML con colores
- `JSON` — árbol colapsable de objetos JSON con colores
- `CSV` — tabla con filas y columnas

### Buscador integrado por formato:

**En TEXT:**
- Búsqueda por texto simple — resalta coincidencias

**En HTML:**
- Búsqueda por texto simple
- Búsqueda por XPath — muestra coincidencias resaltadas en el HTML

**En XML:**
- Búsqueda por XPath
- Si hay más de una coincidencia — muestra lista 1 por 1 con navegación anterior/siguiente

**En JSON:**
- Búsqueda por clave o valor
- Búsqueda por JSONPath

**En CSV:**
- Búsqueda por texto en cualquier columna
- Filtro por columna específica

### Navegación de resultados múltiples:
Cuando una búsqueda devuelve más de un resultado:
```
← 1 / 20 →
```
Botones anterior/siguiente para navegar resultado por resultado.

### Relación con records:
El Visualizador de Datos es también el navegador de records —
la misma ventana se usa para navegar `record-view-content`
con los botones anterior/siguiente (1 de 1000).

---

## 8. Sistema de observabilidad — Futuro

A implementar cuando FastAPI esté listo.

### Estados de ejecución:
```
running    — ejecutándose
completed  — terminó correctamente
failed     — falló con error
paused     — pausado — por <pause-task/> o por el usuario
```

### Panel de observabilidad:
- Cola de tareas — corriendo, en espera, completadas, fallidas, pausadas
- Historial de fallos por tarea — cuántas veces falló
- Logs por tarea con ID inspectable
- IDs por entorno — prod, dev, test

### IDs de sesión por entorno:
Cada ejecución tiene un UUID único — ya existe en `FrancisSession`.
El desarrollador puede tomar un ID de prod y replicarlo en dev
para debuggear exactamente lo que pasó en producción.

---

## Consecuencias

### Implementar ahora:
- `<pause-task/>` hand simple
- Detección de `FRANCIS_ENV` en el CLI
- Warning de `<pause-task/>` en prod
- CLI flags `--debug` y `--step`
- Validador de sintaxis básico con `validate` command

### Implementar después (requiere FastAPI y Plugin VSCode):
- Árbol de ejecución en tiempo real
- Inspector de variables
- Visualizador de Datos Universal
- Controles de ejecución desde el IDE
- Sistema de observabilidad completo
- Step granular dentro de loops y funciones

### Base ya existe:
- `EventBus` — canal de comunicación entre partes del sistema
- `FrancisSession` con UUID — base para IDs de sesión
- `HandStartedEvent`, `HandCompletedEvent`, `HandFailedEvent` — eventos ya emitidos
