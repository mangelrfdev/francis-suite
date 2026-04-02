# Francis Suite

Modern web scraping framework, built in Python.

## Overview

Francis Suite is a low-code web scraping framework configured via XML,
built on a modern Python stack. Define your scrapers in XML and run them from the terminal.

## Quick Start
```bash
# Install
git clone https://github.com/mangelrfdev/francis-suite
cd francis-suite
uv sync

# Run a workflow
francis-suite run examples/books_scraper.xml
```

## Docker

- **Image** — `francis_suite` + dependencies only. **No** `examples/` and **no** workflow XML inside the image; XML always comes from a **mounted host folder** at `/app/workflows`.
- **Container** — one execution: `docker run` or `docker compose run`.

```bash
docker build -t francis-suite:local .
# Compose: default mount ./workflows; or set WORKFLOWS_HOST_PATH in `.env` to a folder outside this repo (see `.env.example`).
docker compose run --rm francis
```

Outputs appear under `./docker-output/` on the host.

**Image from OCIR / registry (no local build):** set `FRANCIS_IMAGE` and `WORKFLOWS_HOST_PATH` in `.env`, then `docker compose -f docker-compose.ocir.yml --env-file .env pull` and `docker compose -f docker-compose.ocir.yml --env-file .env run --rm francis francis-suite run workflows/...`. See comments in `docker-compose.ocir.yml`.

**Workflows outside the repo:** copy `.env.example` → `.env`, set `WORKFLOWS_HOST_PATH=C:/your/path`, put `.xml` there, then `docker compose run --rm francis francis-suite run workflows/your.xml`. See **`workflows/README.md`**.

Official demos stay under **`examples/`** for local `uv run` only.

## Examples

| File | What it shows |
|------|----------------|
| `examples/books_scraper.xml` | Single page, loop + `<log>` (minimal; see comments for full record pipeline) |
| `examples/books_all_pages.xml` | Paginated scrape + `record-create` (`record-export-*`, optional `record-journal`, `record-xml-*` for XML) + **eight** `<record-save>` → `output/books.*` |
| `examples/all_books_pages.xml` | Run folder `output/{SOURCE}_{UTC}_{SHORT}/` (CAPS via `toUpperCase`; params from shell; default folder `BOOKS_TOSCRAPE_NODATE_LOCAL`). NDJSON: `LISTINGS_{SHORT}.NDJSON`. Private metadata: `BOOKSRECORDS_PRIVATE_METADATA_{SHORT}.JSON`. See `workflows/README.md`. |
| `examples/test_boolean.xml`, `examples/test_sensitive.xml` | Tiny workflows for conditions / sensitive masking |
| `examples/record_pipeline_minimal.xml` | Same record patterns as `all_books_pages` (metadata, journal, xml attrs, multi-format `record-save`) + duplicates + private metadata; sample property rows |

Full **record-save** reference (formats, attributes, samples): [docs/guides/record-save.md](docs/guides/record-save.md).

**Índice de toda la documentación:** [docs/README.md](docs/README.md).

**Plantillas Cursor (reglas reutilizables en otros proyectos):** [templates/cursor-reusable-rules/README.md](templates/cursor-reusable-rules/README.md).

**Plantillas Claude (instrucciones + contexto para chat nuevo):** [templates/claude/README.md](templates/claude/README.md).

**Ejemplo de User Rules globales (Cursor):** [templates/user-rules-cursor-example.md](templates/user-rules-cursor-example.md).

**Integración con un producto web (ej. Estación Inmobiliaria):** toda la spec y handoff están en **[`integrations/web/README.md`](integrations/web/README.md)** (copiar esa carpeta al otro repo o usar con `@`). No forma parte del núcleo del framework.

## Example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<francis-workflow>

    <box-def name="html">
        <httpx-call url="http://books.toscrape.com"/>
    </box-def>

    <box-def name="xml">
        <convert-html-to-xml>${html}</convert-html-to-xml>
    </box-def>

    <box-def name="libros">
        <xpath-extract expression="//article[@class='product_pod']">${xml}</xpath-extract>
    </box-def>

    <loop item="libro" index="i">
        <loop-list>
            <box name="libros"/>
        </loop-list>
        <loop-body>
            <box-def name="titulo">
                <xpath-extract expression=".//h3/a/@title">${libro}</xpath-extract>
            </box-def>
            <box-def name="precio">
                <xpath-extract expression=".//p[@class='price_color']/text()">${libro}</xpath-extract>
            </box-def>
            <log>Libro ${i}: ${titulo} — ${precio}</log>
        </loop-body>
    </loop>

    <log>Scraping completado</log>

</francis-workflow>
```

## CLI
```bash
# Run a workflow
francis-suite run workflow.xml

# Pass variables (shared-box)
francis-suite run workflow.xml --param url=https://ejemplo.com --param token=SECRET

# Regenerate editor schema (XSD + JSON manifest) under schema/
francis-suite schema --out schema
# If the launcher is blocked on Windows, use: uv run python -m francis_suite schema --out schema

# Help
francis-suite --help
francis-suite --version
```

**Editor / validation:** [docs/guides/workflow-schema.md](docs/guides/workflow-schema.md) — generate `schema/francis-workflow.xsd`, associate it in VS Code/Cursor, and work around Windows app control if needed.

**Paths:** Relative paths in workflows (e.g. `output/file.csv`) are resolved against the **process working directory** (where you run the command), not a built-in project root. For production jobs, use absolute paths or inject a base path via `--param` / environment and `${variable}` in XML. Ideas such as CLI `--workspace`, write sandboxing, or split export files are **out of scope for now** — see [docs/roadmap.md — “Analizar en el futuro (no prioritario)”](docs/roadmap.md#analizar-futuro-no-prioridad).

## Stack

- **Python 3.11+** — core language
- **lxml** — XML parsing and XPath
- **httpx** — HTTP client
- **Scrapling** — smart element extraction
- **Playwright** — browser automation
- **FastAPI** — REST API / IDE backend
- **simpleeval** — safe expression evaluation engine
- **uv** — packaging and environment management
- **openpyxl** / **pyarrow** — Excel and Parquet export (`record-save`)
- **psutil** — RAM / metrics for record metadata

See `pyproject.toml` for the full dependency list.

## Dev Stack

- **pytest** — testing framework
- **respx** — HTTP mocking for tests
- **ruff** — linter and formatter

## Status

🚧 Early development — core hands complete, external hands pending.

## Project Structure
```
francis_suite/
├── cli.py          # CLI entry point
├── core/           # execution engine
│   ├── parser.py       # XML → FNode tree
│   ├── runtime.py      # FNode tree → execution
│   ├── context.py      # variable scoping
│   ├── variables.py    # FVariable types
│   ├── nodes.py        # FNode definition
│   ├── registry.py     # HandRegistry + @hand decorator
│   ├── session.py      # FrancisSession
│   ├── events.py       # EventBus
│   └── expressions.py  # FrancisExpression engine
├── hands/
│   └── core/       # built-in hands (ext/ planned for plugins)
tests/
docs/
schema/           # generated: francis-workflow.xsd, francis-workflow.schema.json (run: francis-suite schema)
integrations/web/ # optional: specs for a consumer product (e.g. web app); not core framework
templates/        # reusable Cursor/Claude rule snippets for any project
examples/
├── books_scraper.xml
├── books_all_pages.xml
├── test_boolean.xml
└── test_sensitive.xml
```

## Core Hands (partial list)

For the full set of built-in tags, see [docs/architecture.md](docs/architecture.md) (`Hands implementados`).

| Tag | Description |
|---|---|
| `<log>` | Print a message to console |
| `<box-def>` | Execute children and store result in a variable |
| `<box>` | Retrieve a variable from context |
| `<sleep>` | Pause execution for N seconds |
| `<empty>` | Return an empty variable |
| `<httpx-call>` | Make HTTP requests via httpx |
| `<convert-html-to-xml>` | Convert HTML to clean XML |
| `<xpath-extract>` | Apply XPath expressions to XML |
| `<loop>` | Iterate over a list — requires `<loop-list>` and `<loop-body>` |
| `<if>` | Conditional execution |
| `<else>` | Else branch for if |
| `<case>` | Switch-case pattern |
| `<while>` | Loop while condition is true |
| `<try>` / `<catch>` | Error handling |
| `<exit>` | Stop workflow execution |
| `<function-create>` | Define a reusable function |
| `<function-call>` | Call a defined function |
| `<function-param>` | Pass parameters to a function |
| `<function-return>` | Return a value from a function |
| `<regex>` | Apply regular expressions |
| `<compose>` | Interpolate variables into text |
| `<text-split>` | Split text into a list of tokens |
| `<evaluate>` | Evaluate expressions |
| `<build-list>` | Build a list from children |
| `<call-workflow>` | Execute an external workflow file |
| `<convert-json-to-xml>` | Convert JSON to XML |
| `<convert-xml-to-json>` | Convert XML to JSON |
| `<file-read>` | Read a file from disk |
| `<file-write>` | Write content to a file |
| `<file-manage>` | Delete, move, copy, or list files |

## Expression Engine

Francis Suite has a built-in expression engine (`FrancisExpression`) that supports:

- Variable resolution: `${nombre}`
- Arithmetic: `${precio} * ${cantidad}`
- Comparisons: `${edad} > 18`
- Logical operators: `${activo} and !${vacio}`
- Method calls: `${nombre.isEmpty()}`, `${texto.toUpperCase()}`
- Boolean conditions: `${flag.toBoolean()}`

Available string methods: `isEmpty()`, `isNotEmpty()`, `toUpperCase()`, `toLowerCase()`,
`trim()`, `length()`, `contains(x)`, `startsWith(x)`, `endsWith(x)`, `replace(x, y)`,
`toInt()`, `toFloat()`, `toBoolean()`

## Loop
```xml
<loop item="producto" index="i" max-loops="50">
    <loop-list>
        <box name="productos"/>
    </loop-list>
    <loop-body>
        <log>Producto ${i}: ${producto}</log>
    </loop-body>
</loop>
```

- `item` — required — variable name for current item
- `index` — optional — counter starting at 1
- `max-loops` — optional — maximum iterations
- `loop-list` — required — defines the list to iterate
- `loop-body` — required — defines the logic per iteration

## Regex
```xml
<box-def name="anio">
    <regex>
        <regex-pattern>(\d{4})-(\d{2})-(\d{2})</regex-pattern>
        <regex-input>${fecha}</regex-input>
        <regex-result>${_1}</regex-result>
    </regex>
</box-def>
```

- `${_0}` — full match
- `${_1}`, `${_2}`, `${_3}` — capture groups

## Nomenclature

Tag and attribute naming is documented in [docs/architecture.md](docs/architecture.md)
(rules for hands, `engine.resolve`, shared-box, records, etc.).

## Development
```bash
uv sync --extra dev
uv run pytest
```