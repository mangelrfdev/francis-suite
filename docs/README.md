# Documentación — Francis Suite

Índice rápido (la fuente de verdad sigue siendo el código y los tests).

| Documento | Contenido |
|-----------|-----------|
| [architecture.md](architecture.md) | Arquitectura, reglas de hands, FContext, records, CLI, estado del proyecto |
| [roadmap.md](roadmap.md) | Hitos, pendientes, futuro; **[Liveness y operación](roadmap.md#liveness-operacion)**; **[Analizar en el futuro (no prioritario)](roadmap.md#analizar-futuro-no-prioridad)** (cwd, workspace CLI, sandbox, prod) |
| **Guías** (`guides/`) | Uso práctico por tema |
| **Decisiones** (`decisions/ADR-*.md`) | ADRs; proxy: [ADR-004](decisions/ADR-004-set-proxy-design.md) |

## Guías (`guides/`)

| Guía | Tema |
|------|------|
| [record-save.md](guides/record-save.md) | `<record-save>`, `<record-save-duplicates>` (duplicados por `record-key`), `record-journal`, `record-export-*`, ejemplos `books_all_pages.xml` / `all_books_pages.xml` |
| [record-save-formats.md](guides/record-save-formats.md) | Diseño evolutivo (metadata-placement, plantillas, etc.) |
| [sensitive.md](guides/sensitive.md) | Variables sensibles, masking, `--param` |
| [httpx-call.md](guides/httpx-call.md) | HTTP: text, binary, stream |
| [file_manage.md](guides/file_manage.md) | `file-manage` |
| [converts.md](guides/converts.md) | Hands de conversión |

## Ejemplos en el repo

Ver `examples/` en la raíz del proyecto y la tabla en el [README principal](../README.md#examples).
