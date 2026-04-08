# Run output, artifacts, and integration

How a Francis Suite run works end-to-end: what the **engine** always does, what only happens if the **workflow** declares it, and how to design outputs so **jobs, injectors, and future you** can recognize them.

Language: English for headings where it matches code; body can be Spanish or English (this file uses Spanish for Miguel’s notes).

---

## 1. Mental model: engine vs workflow

| Layer | Role |
|-------|------|
| **Engine** (`FRuntime`, `FrancisSession`, `FContext`) | Walks the XML tree in order, runs each hand, stores results in **boxes** (variables). One **session** per run (UUID, status, duration). |
| **Workflow XML** | Declares *what* to execute: `httpx-call`, `record-create`, `file-write`, `record-save`, etc. If a tag is missing, that behavior does not run. |

There is **no** single global “product output folder” enforced by the core. Paths like `output/${run_dir}/` are a **project convention** in examples, not a framework guarantee.

---

## 2. What always exists during a run (in memory)

- **`FrancisSession`**: `session.id` (UUID), `workflow_name`, status (`running` → `completed` / `failed`), timestamps, duration after finish.
- **`FContext`**: scoped variables; **shared boxes** (e.g. records) live in the global scope.
- **EventBus** (for tooling): session / hand events; not a file artifact by itself.

Nothing here is automatically written as a “run package” unless hands do so.

---

## 3. Boxes and execution order

- Children of `<francis-workflow>` run **top to bottom**.
- Each hand returns an `FVariable`; results are stored under the names you set (`<box-def name="...">`, `<record-create name="...">`, etc.).
- **Rule of thumb**: “If you don’t touch it, it doesn’t change” (scoping rules: `while` / `loop` do not open a new scope; `function-call` does).

---

## 4. Records: what the engine guarantees on disk

### 4.1 `record-create` (no export by itself)

- Defines an **`FRecord`** in memory: schema, key, public metadata, optional XML export attrs, optional **journal** path.
- **`record-add`** appends **rows** in memory and validates/normalizes fields.
- **`record-save`** (later in the XML) is what **exports** rows to NDJSON, JSON, CSV, etc. **If you never call `record-save`, there is no dataset file** from that record—only what follows below.

### 4.2 Optional: `record-journal`

- If `<record-journal path="..."/>` is set on `record-create`, each successful **`record-add`** can append one **NDJSON line** to that path (incremental, crash-friendly).
- At **end of run**, the runtime **finalizes** the journal (footer / process line). See [record-save.md](record-save.md) for details.

**Journal = audit trail of row adds**, not a substitute for “per-slice job status” unless you design it that way.

### 4.3 Automatic: private metadata under `sessions/` (unless disabled)

After **every** run (success or failure), for each `FRecord` in the shared context, the runtime writes:

`sessions/<session_id>/<record_name>_private_metadata.json`

unless `FRANCIS_AUTO_RECORD_METADATA` is `0` / `false` / `no` (used in tests).

This file contains **technical metadata** (session id, workflow path, francis version, timing, RAM metrics, row counts, etc.)—see `docs/architecture.md` (FRecord / metadata section). It does **not** replace your **business** NDJSON for ingestion.

---

## 5. Explicit user outputs

These run **only** if the workflow declares them:

| Hand | Typical use |
|------|-------------|
| `<record-save>` | Export `FRecord` rows to `path` (ndjson, json, csv, …). |
| `<record-save-metadata>` | Public metadata JSON to a chosen path. |
| `<file-write>` | Arbitrary text/binary to a path (logs, manifests, slice reports). |

So: **yes**, you can run a workflow with **`record-create` + `record-add` + `log`** and **no** `record-save` / `file-write`—you still get **journal** (if configured) and **`sessions/..._private_metadata.json`**, but no “listing file” for your app unless you add it.

---

## 6. Why outputs can feel “messy”

- Examples use **different** naming: `LISTINGS_*.NDJSON`, `RUN_MANIFEST.JSON`, scrape logs, Docker `docker-output/`, etc.
- **`sessions/`** is engine-side; **`output/`** is user-defined in XML.
- **Journal** path is user-defined; it is not the same as **`record-save`** output.

**Order is a product convention**: the framework stays flexible; **you** (or the repo’s examples) choose one layout and document it.

### 6.1 `SLICE_OUTCOMES` — idea vs reality (read this if confused)

**`SLICE_OUTCOMES` is not a Francis feature.** There is no `<slice-outcomes>` hand and no automatic file with that name. It is a **name we use in docs** for a **recommended pattern**: *you* append one line per search slice (e.g. with `<file-write append="true">` and a `<compose>` JSON) so an external job knows “this slice ran and had N listings (N can be 0).”

| Artifact | Who creates it | Built into engine? |
|----------|----------------|-------------------|
| `sessions/<session_id>/<record>_private_metadata.json` | Runtime at end of run | **Yes** (per FRecord; can disable with `FRANCIS_AUTO_RECORD_METADATA`) |
| NDJSON from `<record-save>` | Your workflow | **Only if** you declare `record-save` |
| Lines from `<record-journal>` | Your workflow + runtime finalize | **Only if** you set `record-journal` on `record-create` |
| `RUN_MANIFEST.JSON`, scrape logs under `output/` | Examples / your workflow | **Only if** you use `file-write` or similar |
| **`SLICE_OUTCOMES` or any “per-slice report”** | **Nobody** until **you** write it | **No** — optional convention for orchestrators |

So: **existing** = session metadata + whatever your XML exports. **Slice outcomes** = **future / optional layer** you add when you need the injector to reconcile “scheduled slice” vs “completed with 0 rows.”

---

## 7. Integration patterns (jobs, injectors, downstream)

### 7.1 Primary data

- **`record-save`** → e.g. `LISTINGS_<SHORT>.NDJSON`: **rows to ingest** (one JSON object per line in NDJSON body, after any header line depending on format—see [record-save.md](record-save.md)).

### 7.2 Lineage and ops

- **`RUN_MANIFEST.JSON`** (or equivalent): small JSON with `ingestion_run_id`, `run_dir`, `source`, pointer to primary NDJSON—**examples already do this**; extend with `francis_suite_version`, `session_id` if your orchestrator needs them.

### 7.3 “No results” / per-slice reconciliation

- **Empty listing NDJSON** (or no new rows) is **ambiguous**: no scrape vs failed run vs zero results for a slice.
- **Recommended**: append a **structured slice report** (NDJSON lines or CSV) with at least: `slice_id`, `url_requested`, `listing_count` (0 allowed), `status`. Emit **one line per slice** your job expected—then the injector can match **input job list** ↔ **report lines**.
- This is **not** built into the core today; it belongs in **workflow XML** (`<file-write>` / `<compose>`) or a future convention hand.

### 7.4 Portfolio / product narrative

- [portfolio-scraping-communication.md](portfolio-scraping-communication.md) — product and communication notes (separate from this technical artifact guide).

---

## 8. Suggested folder convention (optional, not enforced)

For a single run folder `output/<RUN_DIR>/`:

| Subpath / file | Role |
|----------------|------|
| `data/` or root | `LISTINGS*.NDJSON` (or your primary export) |
| `RUN_MANIFEST.JSON` | Index: workflow, ids, paths to artifacts |
| `SLICE_OUTCOMES.NDJSON` | One JSON line per slice (if you implement it) |
| `logs/` | Scrape / debug text logs |

Version the manifest: `"schema_version": "1"` so future tools can evolve.

---

## 9. Where to read more

| Topic | Doc |
|-------|-----|
| Architecture, FContext, FRecord types | [architecture.md](../architecture.md) |
| `record-save`, formats, journal | [record-save.md](record-save.md), [record-save-formats.md](record-save-formats.md) |
| Roadmap / future CLI / workspace | [roadmap.md](../roadmap.md) |
| Web product integration (not core) | [integrations/web/README.md](../../integrations/web/README.md) |

---

## 10. Summary one-liner

**The engine orders execution and keeps session + in-memory state; it always writes `sessions/<id>/*_private_metadata.json` for each FRecord unless disabled. Everything your product “ships” (NDJSON, manifests, slice reports) is declared in XML—design one convention and stick to it.**
