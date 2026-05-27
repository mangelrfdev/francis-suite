# Francis Suite

> 🌐 **English** · [Español](README.md)

> Low-code XML framework for data extraction and processing, built in Python.

[![PYTHON 3.11+](https://img.shields.io/badge/PYTHON-3.11%2B-blue)](https://www.python.org/downloads/)
[![LICENSE MIT](https://img.shields.io/badge/LICENSE-MIT-yellow)](LICENSE)
[![TESTS 150+](https://img.shields.io/badge/TESTS-150%2B-brightgreen)](tests/)
[![STATUS Functional](https://img.shields.io/badge/STATUS-Functional%20%C2%B7%20Extensible-brightgreen)](docs/roadmap.md)

> Core is **functional** and ready for real pipelines. New capabilities are added as **hands**
> without rewriting the engine — see [`docs/roadmap.md`](docs/roadmap.md).

**Want to extend the framework?** → [**How to create a hand**](docs/guides/how-to-create-a-hand.md)
Step-by-step guide: Python + XML + tests + schema, with a ready-to-copy template.

---

## What is Francis Suite?

A **universal framework for data extraction, transformation, and persistence.** Each pipeline is
described in a single XML file: fetch information, process, validate, transform, and store — all
from the same declarative definition.

Covers the full lifecycle:

- **Acquisition** — HTTP requests, file reads from disk, remote download, endpoint upload.
- **Transformation** — format conversions (HTML, XML, JSON, CSV, Base64, binary), XPath, regex,
  splits, text composition.
- **Modeling** — typed boxes, schema-backed records, per-row validation, key-based deduplication.
- **Persistence** — export to JSON, CSV, NDJSON, XML, HTML, TXT/TSV, Excel, and Parquet — in any
  combination, with public and private per-run metadata.
- **Operations** — file management (move, copy, delete, list), proxies, append-only journals,
  reproducible sessions.

All data flows through a unified model called **`boxes`** — predictable, typed, scoped, ready to
compose. The same workflow can read an Excel file, call an API, merge results, deduplicate, and
persist to Parquet for analytics without writing Python.

---

## Tests & coverage

The project includes **150+ pytest tests**. Their purpose is to **ensure everything built into
Francis Suite behaves as documented**: the XML parser, the runtime that executes each hand, the
data flow between `box-def` and `box`, `${...}` expressions, the record system (schema,
validation, deduplication, export), HTTP calls, format conversions, and atomic disk writes.

Each suite runs **real XML workflows** — the same kind you would run with `francis-suite run` —
and checks the result at every layer: parser → runtime → hands → context → artifacts in `output/`.
Error paths are also covered (unknown tags, invalid records, timeouts, session and RAM limits) so
production isn't the first time the engine encounters them.

| Suite | What it validates |
|-------|-------------------|
| [`test_pipeline.py`](tests/test_pipeline.py) | Full pipeline: `httpx-call`, HTML/XML/JSON/CSV conversions, `xpath-extract`, `loop`/`while`, `if`/`else`/`case`, functions, `regex`, `compose`, `evaluate`, records, files, `try`/`catch`, `exit` |
| [`test_expression_chain.py`](tests/test_expression_chain.py) | Expression engine: arithmetic, comparisons, chainable methods (`toUpperCase`, `isEmpty`, `toInt`, …) |
| [`test_httpx_auto_cookies.py`](tests/test_httpx_auto_cookies.py) | Cookie jar shared across `<httpx-call auto-cookies="true">` |
| [`test_httpx_cookie_jar_close.py`](tests/test_httpx_cookie_jar_close.py) | HTTP session shutdown and lockout until `set-proxy` |
| [`test_httpx_introspect.py`](tests/test_httpx_introspect.py) | Last-response inspection (status, headers, cookies) |
| [`test_set_proxy.py`](tests/test_set_proxy.py) | Proxy configuration and rotation |
| [`test_schema_gen.py`](tests/test_schema_gen.py) | XSD generation and JSON manifest of the schema |
| [`test_liveness.py`](tests/test_liveness.py) | Session deadline, `session-pulse`, RAM limits |
| [`test_box_def_item.py`](tests/test_box_def_item.py) | Boxes inside `loop` contexts |

Run the full suite from the repo root:

```bash
uv sync --extra dev
uv run pytest
uv run pytest -x    # stop on first failure
```

The example workflows in [`workflows/`](workflows/) and [`examples/`](examples/) complement the
tests as runnable references; the source of truth for engine behavior lives in `tests/`.

---

## Philosophy

| Principle | What it means in practice |
|-----------|---------------------------|
| **Declarative, not imperative** | XML says *what* to do, not *how*. Logic lives in runtime hands. |
| **One data model** | Everything is a `box`. An `FVariable` goes in, an `FVariable` comes out. No stray objects. |
| **Parser is not the engine** | XML is converted to a neutral `FNode` tree. The runtime is format-agnostic. |
| **Convention over configuration** | Sensible defaults: undeclared = absent. Declared = wins. |
| **Reproducible** | Atomic writes, lockfiles, private metadata with version, session, and environment per run. |

---

## Why XML

Workflows are **decision trees**. XML is built for trees:

- **Schema:** structural validation before execution (XSD generated via `francis-suite schema`).
- **Editor autocomplete** (VS Code / Cursor) thanks to the schema.
- **Horizontal readability:** anyone on the team reads the flow without reading Python.
- **Clean composition:** nesting, attributes, and text are separated; no YAML implicit conventions.

A full annotated example (with HTTP request, headers, query params, HTML→XML conversion, XPath
extraction, and loop) lives in the Spanish README under [«Por qué XML»](README.md#por-qué-xml).
The XML syntax is universal — the comments are in Spanish but the tags are the framework's API.

---

## Quick Start

Requires [Python 3.11+](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/mangelrfdev/francis-suite
cd francis-suite
uv sync
uv run francis-suite run workflows/all_books_pages.xml
```

The workflow scrapes `books.toscrape.com`, paginates to the end, and exports results in
**eight different formats** under `output/`.

For a production-oriented pipeline see
[`workflows/properties_workflow_template.xml`](workflows/properties_workflow_template.xml):
a listings template with run manifest, validation, and structured output.

---

## Main capabilities

### HTTP requests (GET, POST, headers, query params, body)

`<httpx-call>` covers the full request lifecycle: method, headers, params, timeout, response
types (text / binary / disk stream), and an optional cookie-jar session shared across calls.

```xml
<box-def name="json_response">
    <httpx-call url="https://api.example.com/listings" method="GET" timeout="15000">
        <httpx-header name="Authorization">Bearer ${api_token}</httpx-header>
        <httpx-header name="Accept">application/json</httpx-header>
        <httpx-param name="city">santiago</httpx-param>
        <httpx-param name="limit">50</httpx-param>
    </httpx-call>
</box-def>
```

For `POST`/`PUT`/`PATCH`/`DELETE`, `<httpx-param>` becomes form-encoded body. Cookie persistence
via `auto-cookies="true"`. Full reference: [`docs/guides/httpx-call.md`](docs/guides/httpx-call.md)
(Spanish).

### Multi-format declarative output

```xml
<record-save from="data" format="json" path="output/data.json"/>
<record-save from="data" format="csv" path="output/data.csv" clean-data="true"/>
<record-save from="data" format="ndjson" path="output/data.ndjson"/>
<record-save from="data" format="excel" path="output/data.xlsx" sheet-name="Data"/>
<record-save from="data" format="parquet" path="output/data.parquet"/>
```

Same source, five formats, no glue code. Data-shape options:

- **`clean-data="true"`** — rows only, no embedded metadata.
- **`allow-nested="true"`** — JSON/NDJSON keep the group nesting.
- **`allow-prefix="true"`** — flat keys with group prefix (`group.field`).
- *Default:* short keys, sanitized strings (no line breaks that would break CSV).

### Built-in expression language

Variables, arithmetic, comparisons, logical operators, chainable string methods.

```xml
<if condition="${price.isNotEmpty()} and ${price} != '0'">
    <log>Valid price: ${price} ${currency.toUpperCase()}</log>
</if>
```

Methods on strings: `isEmpty`, `isNotEmpty`, `toUpperCase`, `toLowerCase`, `trim`, `length`,
`contains`, `startsWith`, `endsWith`, `replace`, `toInt`, `toFloat`, `toBoolean`.

Evaluation via `simpleeval` — no native `eval()`, no access to `__builtins__`.

### Structured records

Schema, validation, deduplication, and metadata declared in the same XML. Per-row validation
(`strict` or `collect-errors`), `record-key` deduplication with separate export of duplicates,
append-only NDJSON journal that survives crashes, private per-run metadata (totals, completion,
duration, RAM, errors, OS, version, session id), and public metadata embedded where the format
supports it (`_metadata` in JSON, sheet in Excel, node in XML).

### Reusable workflows

```xml
<function-create name="fetchPage">
    <box-def name="html">
        <httpx-call url="${target_url}"/>
    </box-def>
    <function-return>
        <convert-html-to-xml>
            <box name="html"/>
        </convert-html-to-xml>
    </function-return>
</function-create>
```

Functions have their own scope. Parameters travel via `<function-param>` inside `<function-call>`.

### Unify sources: local CSV + web in the same XML

Once a source ends up in a box containing XML — coming from a CSV, a JSON API, an HTML page,
an Excel file, anything — the rest of the workflow doesn't care about its origin. XPath works
for everything, records receive rows from any source, and the output is unified in whichever
format the use case requires.

Full annotated examples (HTTP + headers, full pipeline with pagination, CSV+web unified): see the
Spanish README — same XML syntax, comments in Spanish.

### Production-ready

- **Docker image** without workflows or secrets. `.xml` files are mounted from the host.
- **CLI params**: `--param city=santiago --param pages=10`.
- **Sensitive variables** auto-masked in logs (`api_key`, `token`, `password`, …).
- **XSD schema** generated for editor autocomplete.
- **Atomic writes** in all formats (no half-written files after a failure).
- **150+ tests** covering parser, runtime, hands, expressions, exports, and error cases.

---

## Available hands today

Catalog of integrated **hands**, grouped by function. Full reference of tags and attributes in
[`docs/architecture.md`](docs/architecture.md).

### Network & HTTP

| Hand | Purpose |
|------|---------|
| `<httpx-call>` | HTTP requests (GET/POST/…); headers, payloads, cookies, streaming, retries |
| `<httpx-cookie-jar>` | Cookie jar shared across calls |
| `<httpx-introspect>` | Inspect last response (status, headers, cookies) |
| `<set-proxy>` | Configure proxies (manual, file, API, rotation, probe) |

### Files on disk

| Hand | Purpose |
|------|---------|
| `<file-read>` | Read files as text or binary (UTF-8, latin-1, base64) |
| `<file-write>` | Write content to disk with atomic write |
| `<file-manage>` | Delete, move, copy, list files and folders (with `force-*` and filters) |
| `<file-download>` | Download a remote resource directly to disk |
| `<file-upload>` | Send a file to an HTTP endpoint |

### Format conversions

| Hand | Conversion |
|------|------------|
| `<convert-html-to-xml>` | "Dirty" HTML → clean XML ready for XPath |
| `<convert-html-entities-to-text>` | HTML entities (`&amp;`, `&#xE9;`) → text |
| `<convert-xml-to-json>` / `<convert-json-to-xml>` | Bidirectional XML ↔ JSON |
| `<convert-xml-to-csv>` | Tabular XML → CSV |
| `<convert-csv-to-json>` / `<convert-json-to-csv>` | CSV ↔ JSON |
| `<convert-text-to-base64>` / `<convert-base64-to-text>` | Text ↔ Base64 |
| `<convert-binary-to-base64>` / `<convert-base64-to-binary>` | Binary (images, PDFs, blobs) ↔ Base64 |
| `<convert-text-to-url>` / `<convert-url-to-text>` | URL-encoding both ways |

### Text extraction & manipulation

| Hand | Purpose |
|------|---------|
| `<xpath-extract>` | XPath selection on XML / converted HTML (attributes, text, subtrees) |
| `<regex>` (+ `<regex-pattern>`, `<regex-input>`, `<regex-result>`) | Match, capture groups, output template |
| `<text-split>` | Tokenize by separator, regex, or lines |
| `<compose>` | Variable interpolation to plain text |
| `<evaluate>` | Expression evaluation (`${price * qty}`, comparisons, string methods) |

### Variables & data composition

| Hand | Purpose |
|------|---------|
| `<box-def>` / `<box>` | Define and reuse variables with scope |
| `<shared-box-def>` / `<shared-box>` | Variables shared across scopes (`replace="true|false"`) |
| `<build-list>` | Explicitly build lists from children |

### Records (structured data)

| Hand | Purpose |
|------|---------|
| `<record-create>` | Define schema, keys, validation, journal, metadata |
| `<record-add>` | Insert a normalized row according to the schema |
| `<record-last-added>` / `<record-count>` | Inspection and count |
| `<record-save>` | Export to JSON/CSV/NDJSON/XML/HTML/TXT/Excel/Parquet (with `clean-data`, `allow-nested`, `allow-prefix`) |
| `<record-save-duplicates>` | Export rows dropped by duplicate key |
| `<record-save-validation-errors>` | Export rows rejected under `collect-errors` mode |
| `<record-save-metadata>` / `<record-private-metadata>` | Persist public and private metadata |

### Control flow & composition

| Hand | Purpose |
|------|---------|
| `<loop>` (+ `<loop-list>`, `<loop-body>`) | Iterate lists with `item`, `index`, `max-loops` |
| `<while>` | Loop by condition |
| `<if>` / `<else>` / `<case>` | Conditional branches and switch-case |
| `<try>` / `<catch>` | Local error handling |
| `<exit>` | Stop workflow execution |
| `<function-create>` / `<function-call>` (+ `<function-param>`, `<function-return>`) | Reusable functions with their own scope |
| `<call-workflow>` | Run another external XML workflow |

### Ops, timing, observability

| Hand | Purpose |
|------|---------|
| `<log>` | Print messages with interpolation |
| `<sleep>` / `<sleep-min>` / `<sleep-max>` / `<sleep-avg>` | Fixed and randomized pauses |
| `<pause-task>` | Pause execution waiting for input/condition |
| `<session-pulse>` | Session heartbeat for long processes |

---

## In development & upcoming

Full roadmap (with acceptance criteria and design decisions) in
[`docs/roadmap.md`](docs/roadmap.md). Expectation-oriented summary:

**Upcoming data sources**

- `pdf-read` — read and extract structured data from PDFs. Today you can already load the binary
  with `file-read` and convert with `convert-binary-to-base64` for an external endpoint; the
  native hand will unify the parsing side.
- `excel-read` — direct read of `.xlsx` / `.xls` and `.csv` from XML (Excel is already available
  for **writing** via `record-save format="excel"`).
- `json-read` — load external JSON files as a `box` ready to iterate.
- `use-ia` — invoke models (image OCR, semantic text/PDF extraction, classification) with
  timeout, retry, and error contract.

**Advanced clients**

- `playwright-call` — full browser control (clicks, scroll, waits, network interception) with a
  declarative XML contract.
- `scrapling-call` — layout-change-resistant scraping integrated into the pipeline.
- Extended `set-proxy` — DB-stored credentials, Playwright/Scrapling integration.

**Infrastructure & delivery**

- **Storage providers** (fsspec) — save/load from S3, Google Cloud Storage, Azure Blob from the
  same `record-save` or `file-write`.
- **`fs` expression helpers** — `${fs.uuid()}`, `${fs.now()}`, `${fs.env("KEY")}`, `${fs.random(1,100)}`.
- **REST API (FastAPI)** — `POST /run`, `GET /status/:id`, `WS /ws/:id` to orchestrate workflows
  from other applications.
- **VS Code / Cursor plugin** — full autocomplete, step-by-step execution, live event tree,
  variable inspector, cascading record viewer.
- **External plugin system** (`hands/ext/`) — add custom hands without modifying core.

**Out of scope** (to be explicit)

- `database-call` — not planned: standard output is files via `record-save` or object storage.
- `send-mail`, `ftp-call`, `zip` — no priority until a concrete use case appears.
- YAML workflows — discarded: the declarative format is and will remain XML.

---

## Architecture

```
workflow.xml
   │
   ▼
FParser ──► FNode tree (universal AST, input-format-agnostic)
   │
   ▼
FRuntime ──► executes each Hand
                  │
                  ▼
                Hand.execute() ──► FVariable
                                       │
                                       ▼
                                  FContext (boxes, scopes)
                                       │
                                       ▼
                                  EventBus (start, end, error)
```

The execution engine doesn't depend on XML. The parser builds a tree of neutral `FNode` objects;
everything else — runtime, hands, expressions, events — operates on that tree. If another
definition form (visual editor, graphical builder) is ever added, only a new parser producing
the same tree is needed; the engine stays intact. The declarative human-written format remains
XML by design.

Full design in [`docs/architecture.md`](docs/architecture.md). Design decisions in
[`docs/decisions/`](docs/decisions/).

---

## Tech stack

| Component | Library | Role |
|-----------|---------|------|
| Language | Python 3.11+ | Core |
| XML | lxml | Parsing and XPath |
| HTTP | httpx | Modern HTTP client |
| Browser | Playwright | JavaScript-heavy pages |
| Resilient scraping | Scrapling | Layout-change resistance |
| Expressions | simpleeval | Safe evaluation |
| Excel / Parquet | openpyxl, pyarrow | Native export |
| Metrics | psutil | RAM and environment for private metadata |
| Packaging | uv | Install + lockfile |
| Tests | pytest, respx | Full pipeline coverage |
| Linting | ruff | Linter and formatter |

Full list in [`pyproject.toml`](pyproject.toml).

---

## CLI

```bash
francis-suite run workflow.xml
francis-suite run workflow.xml --param url=https://example.com --param token=SECRET
francis-suite schema --out schema
francis-suite --help
francis-suite --version
```

---

## Docker

```bash
docker build -t francis-suite:local .
docker compose run --rm francis
```

Workflows are mounted from the host (not bundled in the image). Output in `./docker-output/`.
Details in [`workflows/README.md`](workflows/README.md).

---

## Documentation

| Document | Contents |
|----------|----------|
| [`docs/README.md`](docs/README.md) | General index (Spanish) |
| [`docs/guides/how-to-create-a-hand.md`](docs/guides/how-to-create-a-hand.md) | Create and integrate a new hand (English) |
| [`docs/guides/como-crear-un-hand.md`](docs/guides/como-crear-un-hand.md) | Crear e integrar un hand (Spanish) |
| [`docs/architecture.md`](docs/architecture.md) | Layers, FNode, hands, scoping, mental model (Spanish) |
| [`docs/roadmap.md`](docs/roadmap.md) | Status, next steps, out of scope (Spanish) |
| [`docs/guides/record-save.md`](docs/guides/record-save.md) | Export: formats, metadata, `clean-data`, `allow-nested`, `allow-prefix` (Spanish) |
| [`docs/guides/httpx-call.md`](docs/guides/httpx-call.md) | HTTP: cookies, retries, sensitive headers (Spanish) |
| [`docs/guides/workflow-schema.md`](docs/guides/workflow-schema.md) | Editor setup, XSD generation (Spanish/English mixed) |
| [`docs/decisions/`](docs/decisions/) | Architecture Decision Records (mostly Spanish) |

Most deep-dive guides are written in Spanish but are technical enough to follow with translation
tools. New guides may be added in English as the project grows.

---

## Status

**Functional and ready to use.** The core is implemented and tested: parser, runtime, record
system, expressions, integrated hands for network, files, conversions, control flow, and
multi-format export. You can build real pipelines today with the workflows in
[`workflows/`](workflows/) and [`examples/`](examples/).

The framework remains **open to grow**: new capabilities are added as hands (registered in the
runtime) without rewriting the engine. Planned features (native PDF, Excel/JSON reading, AI,
full browser, cloud storage, editor plugin, REST API) are listed under
[**In development & upcoming**](#in-development--upcoming) and in
[`docs/roadmap.md`](docs/roadmap.md).

---

## Development

```bash
uv sync --extra dev
uv run pytest          # 150+ tests
uv run pytest -x       # stop on first failure
uv run ruff check .    # lint
```

---

## License

[MIT](LICENSE).
