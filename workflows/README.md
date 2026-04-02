# Workflows (your XML)

The **Docker image does not include any workflows**. XML always comes from a **host folder mounted at** `/app/workflows` (see `docker-compose.yml` and `Dockerfile`).

## Folder inside this repo (default)

`docker-compose.yml` defaults to `./workflows` (this directory). Copy `examples/record_pipeline_minimal.xml` here as `record_pipeline_minimal.xml` if you want the default `CMD` to work without changing anything.

## Folder **outside** francis-suite (recommended for you)

1. Create a directory anywhere, e.g. `C:\FrancisWorkflows` or `~/francis-workflows`.
2. Put your `.xml` there (“brutal” copy, `scp`, download from OCI Object Storage, etc.).
3. Point Compose at it — **create `.env` in the francis-suite repo root** (gitignored) from `.env.example`:

   ```env
   WORKFLOWS_HOST_PATH=C:/FrancisWorkflows
   ```

   Docker Compose reads `.env` for variable substitution. Use **forward slashes** on Windows with Docker Desktop.

4. Run:

   ```bash
   docker compose run --rm francis francis-suite run workflows/my_job.xml
   ```

   Paths are always `workflows/...` **inside the container**; that maps to whatever you mounted.

**Plain `docker run`** (no Compose):

```bash
docker run --rm \
  -v "${PWD}/docker-output:/app/output" \
  -v "C:/FrancisWorkflows:/app/workflows" \
  francis-suite:local \
  francis-suite run workflows/my_job.xml
```

## Git or Oracle for workflows only

- **Separate git repo:** clone it next to francis-suite (or on the OCI VM) and set `WORKFLOWS_HOST_PATH` to that clone path — `git pull` updates XML without touching the engine image.
- **OCI Object Storage:** on the VM, a cron/script can `oci os object get` your XML into a folder, then `docker compose run` — still the same mount idea.

## Local run without Docker (host)

From the francis-suite repo root (so paths resolve):

```bash
uv run francis-suite run C:/FrancisWorkflows/my_job.xml
```

Or `cd` into your external folder and use absolute paths in `francis-suite run` if the workflow references relative `output/` — simplest is run from repo root with a path to the XML.

## Universal run artifact layout (identify everything in one place)

Today the engine does two things:

1. **Paths you declare** in XML (`<record-save path="..."/>`, `<record-journal path="..."/>`, `<record-save-metadata path="..."/>`) — usually under `output/...`.
2. **Automatic private metadata** after each run: `sessions/<session_id>/<recordName>_private_metadata.json` (see `FRuntime._persist_private_record_metadata`). That is **by design** so traces exist even if the workflow crashes before `record-save`.

To keep **exports + metadata identifiable and bucket-friendly**, use one **run root** per execution and stable **file names**.

### Recommended convention

1. **Define a run id** (UUID from your orchestrator or CLI) and pass it in:
   ```bash
   francis-suite run workflows/job.xml --param ingestion_run_id=a1b2c3d4-...
   ```
2. In the XML, build a **run folder name** and reuse it everywhere. Example in `all_books_pages.xml`:
   - `run_utc` — compact UTC time, no colons (e.g. `20260329T184512Z`)
   - `run_short_id` — short hex (e.g. 8 chars) for audit-friendly filenames
   - `source` — slug (letters, digits, underscore)
   - `run_dir` = `${source.toUpperCase()}_${run_utc.toUpperCase()}_${run_short_id.toUpperCase()}` → **`output/${run_dir}/`** (no `runs/` segment; folder name is CAPS for readability)

3. **Inside that folder (example `all_books_pages`):**

   ```text
   output/{run_dir}/
     RUN_MANIFEST.JSON                          # index: ids + which file is primary_ndjson
     LISTINGS_{SHORT}.NDJSON                    # canonical NDJSON for ingest (full rows, not URLs-only)
     ALL_BOOKS_PAGES_{SHORT}.JOURNAL.NDJSON
     BOOKSRECORDS_PRIVATE_METADATA_{SHORT}.JSON # written after session completes
     ALL_BOOKS_PAGES_{SHORT}.*                  # other exports (CSV, JSON, …)
   ```

   `<record-save-metadata>` registers the path; the engine writes that JSON **after** the session ends (same timing as `sessions/<id>/` auto metadata), so `status`, `fin`, and duration are final.

4. **Bucket:** mirror the same folder name under your prefix. The ingest job must know the NDJSON basename pattern (or use a manifest).

5. **`ingestion_run_id`:** full UUID for DB lineaje in `ingestion_runs` / metadata; can differ from `run_short_id`.

### What about `sessions/`?

- Those files are **tied to `session_id`** (Francis session UUID), not necessarily `ingestion_run_id`. For admin/debug you can:
  - **Option A:** Set `FRANCIS_AUTO_RECORD_METADATA=0` in the container and rely only on **explicit** `<record-save-metadata path="output/${run_dir}/..."/>` so **everything** is under the run root (no split).
  - **Option B:** Keep auto `sessions/` and, in your upload script, copy `sessions/<session_id>/` next to the run folder or register both paths in a manifest for the admin UI.

### Docker

Compose mounts `./docker-output` → `/app/output`, so the tree above appears under **`docker-output/<RUN_DIR>/`** on the host.

### Example: `all_books_pages.xml` with UTC stamp + short id (PowerShell)

From the francis-suite repo root:

```powershell
$ingestionId = [guid]::NewGuid().ToString()
$runUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$short = ([guid]::NewGuid().ToString().Replace("-", "")).Substring(0, 8)
docker compose run --rm francis francis-suite run workflows/all_books_pages.xml `
  --param "ingestion_run_id=$ingestionId" `
  --param "run_utc=$runUtc" `
  --param "run_short_id=$short" `
  --param source=books_toscrape
```

Artifacts: `docker-output/BOOKS_TOSCRAPE_${runUtc}_${short}/` including `LISTINGS_${short}.NDJSON`.

Defaults without params: `output/BOOKS_TOSCRAPE_NODATE_LOCAL/` (dev only).

### Image rebuild

Rebuild the image only when the **engine** changes; changing paths in XML does not require a rebuild.

## Pipeline context

| Phase | Where |
|-------|--------|
| XML | Your host folder → mount `/app/workflows` |
| Exports | `docker-output/` → `/app/output` |
| Product | Bucket + ingest job → Supabase (`integrations/web/08-GCP-PIPELINE-Y-JOB-INGESTA.md` §8) |

## Git workflow (later)

Branch → commit XML in **your** workflows repo (or this `workflows/` folder) → MR → merge. Never commit secrets in XML; use env / Secret Manager.
