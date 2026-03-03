# Francis Suite

Modern web scraping framework inspired by WebHarvest, built in Python.

## Overview

Francis Suite is a low-code web scraping framework configured via XML (with YAML planned).
It reimagines WebHarvest's plugin architecture using a modern Python stack.

## Stack

- **Python 3.11+** — core language
- **lxml** — XML parsing and XPath
- **httpx** — async HTTP client
- **Scrapling** — smart element extraction
- **Playwright** — browser automation
- **FastAPI** — REST API / IDE backend
- **uv** — packaging and environment management
- **simpleeval** — safe expression evaluation engine

## Dev Stack

- **pytest** — testing framework
- **respx** — HTTP mocking for tests
- **ruff** — linter and formatter

## Status

🚧 Early development — foundation phase.

## Project Structure
```
francis_suite/
├── core/          # execution engine (parser, runtime, context, variables)
├── plugins/
│   ├── core/      # built-in plugins (http-call, xpath-extract, loop, etc.)
│   └── ext/       # external plugins (ftp, mail, zip, browser)
└── xml/           # XML schema and config loading
tests/
docs/
  └── decisions/   # Architecture Decision Records
examples/
```

## Nomenclature

Francis Suite hands tags for clarity.
See [docs/nomenclatures.yaml](docs/nomenclatures.yaml) for the full mapping.

## Development
```bash
uv sync --extra dev
uv run pytest
```