# Francis Suite

Modern web scraping framework, built in Python.

## Overview

Francis Suite is a low-code web scraping framework configured via XML (with YAML planned),
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

    <box-def name="titulos">
        <xpath-extract expression="//h3/a/@title">${xml}</xpath-extract>
    </box-def>

    <file-write path="output/libros.txt">${titulos}</file-write>

    <log>Scraping completado</log>

</francis-workflow>
```

## CLI
```bash
# Run a workflow
francis-suite run workflow.xml

# Pass variables
francis-suite run workflow.xml --var url=https://ejemplo.com --var token=SECRET

# Help
francis-suite --help
francis-suite --version
```

## Stack

- **Python 3.11+** — core language
- **lxml** — XML parsing and XPath
- **httpx** — HTTP client
- **Scrapling** — smart element extraction
- **Playwright** — browser automation
- **FastAPI** — REST API / IDE backend
- **simpleeval** — safe expression evaluation engine
- **uv** — packaging and environment management

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
│   ├── core/       # built-in hands
│   └── ext/        # external hands (ftp, mail, zip, browser)
tests/
docs/
examples/
└── books_scraper.xml
```

## Core Hands

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
| `<loop>` | Iterate over a list |
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
| `<text-format>` | Interpolate variables into text |
| `<text-split>` | Split text into a list of tokens |
| `<evaluate>` | Evaluate expressions |
| `<build-list>` | Build a list from children |
| `<call-workflow>` | Execute an external workflow file |
| `<convert-json-to-xml>` | Convert JSON to XML |
| `<convert-xml-to-json>` | Convert XML to JSON |
| `<file-read>` | Read a file from disk |
| `<file-write>` | Write content to a file |
| `<file-download>` | Download a file from a URL |
| `<file-upload>` | Upload a file to a URL |
| `<file-manage>` | Delete, move, copy, or list files |

## Expression Engine

Francis Suite has a built-in expression engine (`FrancisExpression`) that supports:

- Variable resolution: `${nombre}`
- Arithmetic: `${precio} * ${cantidad}`
- Comparisons: `${edad} > 18`
- Logical operators: `${activo} and !${vacio}`
- Method calls: `${nombre.isEmpty()}`, `${texto.toUpperCase()}`

Available string methods: `isEmpty()`, `isNotEmpty()`, `toUpperCase()`, `toLowerCase()`,
`trim()`, `length()`, `contains(x)`, `startsWith(x)`, `endsWith(x)`, `replace(x, y)`,
`toInt()`, `toFloat()`

## Nomenclature

Francis Suite uses its own tag naming convention.
See [nomenclatures.yaml](nomenclatures.yaml) for the full mapping.

## Development
```bash
uv sync --extra dev
uv run pytest
```