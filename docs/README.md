# Documentación — Francis Suite

> 🌐 **Español** (este índice) · README en inglés: [`../README.en.md`](../README.en.md) · Guía de hands en inglés: [`guides/how-to-create-a-hand.md`](guides/how-to-create-a-hand.md)

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
| [**como-crear-un-hand.md**](guides/como-crear-un-hand.md) | **Cómo crear e integrar un hand nuevo** — plantilla Python, registro, tests, schema, checklist · 🇬🇧 [English](guides/how-to-create-a-hand.md) |
| [record-save.md](guides/record-save.md) | `<record-save>`, `<record-save-duplicates>`, `<record-save-validation-errors>`, `record-validation` (strict / collect-errors), `record-journal`, `record-export-*`, `clean-data`, `allow-nested` / `allow-prefix` (alias `allow-sufix`), ejemplos `books_all_pages.xml` / `all_books_pages.xml` |
| [record-save-formats.md](guides/record-save-formats.md) | Diseño evolutivo (metadata-placement, plantillas, etc.) |
| [sensitive.md](guides/sensitive.md) | Variables sensibles, masking, `--param` |
| [httpx-call.md](guides/httpx-call.md) | HTTP: text, binary, stream |
| [file_manage.md](guides/file_manage.md) | `file-manage` |
| [converts.md](guides/converts.md) | Hands de conversión |
| [workflow-schema.md](guides/workflow-schema.md) | Generar `schema/francis-workflow.xsd` y manifest JSON; uso en el editor; Windows |
| [portfolio-scraping-communication.md](guides/portfolio-scraping-communication.md) | Portafolio (Estación + Francis): decisiones de datos, marco del scraping, guion para reclutadores, enlaces a specs |
| [run-output-and-integration.md](guides/run-output-and-integration.md) | Qué hace el motor vs el XML: sesión, records, journal, `sessions/`, `record-save`, convención de carpetas, integración con jobs / inyector |

## Integraciones (producto que consume Francis)

| Recurso | Contenido |
|---------|-----------|
| [integrations/web/README.md](../integrations/web/README.md) | Specs y handoff para **un** sitio/producto (ej. Estación); no es núcleo del framework |

## Plantillas (cualquier proyecto)

| Recurso | Contenido |
|---------|-----------|
| [templates/cursor-reusable-rules/](../templates/cursor-reusable-rules/README.md) | Reglas `.mdc` genéricas para copiar a `.cursor/rules/` en repos nuevos |
| [templates/claude/](../templates/claude/README.md) | Instrucciones personalizadas + plantilla de contexto inicial para chats en Claude |
| [templates/user-rules-cursor-example.md](../templates/user-rules-cursor-example.md) | Ejemplo para pegar en User Rules globales de Cursor (tono cálido + criterios generales) |

## Feedback / notas personales (`feedback/`)

| Archivo | Contenido |
|---------|-----------|
| [feedback/work-style-self-notes.md](feedback/work-style-self-notes.md) | Fortalezas y áreas a vigilar (estilo de trabajo); derivado de reflexión en proyecto; opcional mover a `docs/private/` si no va al remoto |

## Documentación privada (`docs/private/`)

La carpeta **`docs/private/`** está en **`.gitignore`**: sirve para tutoriales operativos (Docker, OCIR, runbooks) que **no** deben subirse al remoto. Crea ahí tus `.md` en local; un `git clone` **no** trae esos archivos.

En tu copia de trabajo puedes tener p. ej. `docs/private/docker-oracle-ocir.md` (tutorial Docker + OCIR); al hacer `git push` esa ruta no se incluye.

## Ejemplos en el repo

Ver `examples/README.md` y la tabla en el [README principal](../README.md#examples) (`examples/demos/`, `examples/corredoras/`).
