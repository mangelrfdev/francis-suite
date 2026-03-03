# ADR-001: Execution Engine Architecture

**Date:** 2026-03-02  
**Status:** Accepted

## Context

Francis Suite needs a core execution engine that reads an XML configuration
file and runs plugins sequentially. This is the heart of the framework.

The reference implementation (Java) uses this pipeline:

1. XML file → SAX parser → XmlNode tree
2. XmlNode tree → tag name lookup → Plugin class resolution
3. Plugin instantiation → attribute injection
4. Session creation (UUID + metrics)
5. Scraper.execute() → recursive plugin execution
6. Event broadcasting (started, completed, failed)
7. Results extraction + cleanup

## Decision

Francis Suite will implement the same pipeline in Python with these mappings:

| Reference concept     | Francis Suite equivalent              |
|-----------------------|---------------------------------------|
| SAXConfigParser       | `core/parser.py` — lxml SAX/etree     |
| XmlNode               | `core/nodes.py` — Python dataclass    |
| PluginRegistry        | `core/registry.py` — dict tag→class   |
| @CorePlugin           | `@plugin(tag="...")` decorator        |
| DynamicScopeContext   | `core/context.py` — scoped variable store |
| ScraperSession        | `core/session.py` — UUID + metrics    |
| Scraper.execute()     | `core/runtime.py` — recursive executor|
| Variable / NodeVariable | `core/variables.py` — typed wrappers|
| EventBus              | `core/events.py` — simple pub/sub     |

## Pipeline (Francis Suite)
```
workflow.xml
    ↓
Parser (lxml)         → builds FNode tree
    ↓
Registry lookup       → resolves tag → Plugin class
    ↓
Session creation      → UUID + FrancisSession
    ↓
Runtime.execute()     → walks FNode tree recursively
    ↓  
Plugin.execute()      → runs logic, returns FVariable
    ↓
Context.set()         → stores result in scoped variables
    ↓
Events                → on_start, on_complete, on_error
    ↓
Results + cleanup
```

## Core files to create (in order)

1. `core/variables.py` — FVariable, FNodeVariable, FListVariable, FEmptyVariable
2. `core/nodes.py` — FNode (parsed XML node with tag, attrs, children)
3. `core/context.py` — FContext (scoped variable store)
4. `core/registry.py` — PluginRegistry + @plugin decorator
5. `core/parser.py` — XML parser → FNode tree
6. `core/session.py` — FrancisSession (UUID, metrics, status)
7. `core/runtime.py` — Runtime executor (walks tree, calls plugins)
8. `core/events.py` — simple event system
9. `plugins/base.py` — AbstractPlugin base class

## Consequences

- All plugins extend `AbstractPlugin` and implement `execute(context)`
- Tag-to-plugin mapping is automatic via `@plugin` decorator
- Context is passed through the entire execution tree
- Sessions are isolated — parallel execution is safe by design