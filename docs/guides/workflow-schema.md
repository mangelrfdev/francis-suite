# Workflow schema (XSD + manifest) for the editor

Francis Suite can emit **machine-readable artifacts** from the same registry the runtime uses (`HandRegistry`). You regenerate them after adding or renaming hands.

## What gets generated

From the project root (with the dev env active), the command writes under `schema/` (or `--out`):

| File | Purpose |
|------|---------|
| `francis-workflow.xsd` | **XML Schema** — associate workflow XML files with this in VS Code / Cursor (Red Hat XML) for validation and **tag-name** awareness under `<francis-workflow>`. |
| `francis-workflow.schema.json` | **JSON manifest** — sorted list of registered `hand_tags`, version string, pointers to the XSD. Useful for tooling or quick inspection; not a full JSON Schema of every attribute per hand. |

The XSD uses a shared `HandMixedType`: mixed content, `xs:any` for nested elements, and `xs:anyAttribute` so **attributes are not enumerated** per tag (that would duplicate the hands’ Python APIs). The main win today is **known child tag names** and a valid root structure.

## Prerequisites

Same as running workflows: Python 3.11+, dependencies installed.

```bash
git clone https://github.com/mangelrfdev/francis-suite
cd francis-suite
uv sync
```

Optional dev tools: `uv sync --extra dev` for pytest.

## How to generate

From the repository root:

```bash
francis-suite schema --out schema
```

If the `francis-suite` launcher fails (see **Windows** below), use the module form:

```bash
uv run python -m francis_suite schema --out schema
```

Options:

- `--out DIR` — output directory (default: `schema`).
- `--version TEXT` — string stored in the JSON manifest (default: installed package version from metadata).

After changing hands, **regenerate and commit** the files under `schema/` so the repo stays the source of truth.

## Windows: “Control de aplicaciones bloqueó este archivo”

Some environments block the **console script** that `uv`/`pip` install for `francis-suite` (error **4551** or similar). The interpreter is usually allowed, so prefer:

```bash
uv run python -m francis_suite schema --out schema
```

or:

```bash
python -m francis_suite schema --out schema
```

(using the same venv you use for `pytest`).

## Using the XSD in VS Code / Cursor

1. Install an XML extension (commonly **XML** by Red Hat).
2. Map your workflow globs to the XSD, for example in **User** or **Workspace** `settings.json`:

```json
{
  "xml.fileAssociations": [
    {
      "pattern": "**/examples/*.xml",
      "systemId": "${workspaceFolder}/schema/francis-workflow.xsd"
    }
  ]
}
```

Adjust `pattern` to match where you keep workflows (e.g. `**/*.xml` only if you do not mix unrelated XML). Use forward slashes or `${workspaceFolder}`; avoid hardcoding another machine’s path.

3. Reload the window if the association does not apply immediately.

Validation is **structural** (root + allowed hand tags + flexible content/attributes), not a guarantee that every attribute value is valid for that hand.

## Tests

Generation is covered in `tests/test_schema_gen.py`. Full suite:

```bash
uv run pytest
```

## See also

- [docs/architecture.md](../architecture.md) — engine, hands, registry.
- [docs/roadmap.md](../roadmap.md) — future **plugin** and richer IDE contract.
