# Francis Suite ↔ estacion-inmobiliaria — sync status

Single-page mirror so this repo stays aligned with the web repo. **Canonical handoff** (updated by both sides): `docs/FRANCIS_SUITE_HANDOFF.md` in **estacion-inmobiliaria**.

## Agreed split

| Piece | Owner |
|-------|--------|
| Extract + NDJSON (e.g. `record_pipeline_minimal` → `listings.ndjson`: `_type` export line + `listing` rows) | francis-suite |
| Job, Supabase, public site, `/buscar` | estacion-inmobiliaria |

## NDJSON sample (contract for mapping)

- Run: `uv run francis-suite run examples/demos/record_pipeline_minimal.xml`
- Output: `output/record_pipeline_minimal/listings.ndjson`
- **Template for new property scrapers** (same `listing` contract + `LISTINGS_{SHORT}.NDJSON` + `RUN_MANIFEST.JSON` under `output/${run_dir}/`): `examples/demos/properties_workflow_template.xml` (twin `workflows/properties_workflow_template.xml`). Copy into your `francis-workflows` mount for the VM.

## OCI Object Storage — fill when infra is ready (names only, no secrets)

**Note:** Creating the bucket is **only possible in your OCI tenancy** (Console or `oci` CLI). No one else can do it without your account.

### What you do once (Oracle Console)

1. Log in to **Oracle Cloud Console** and check the **region** in the top bar (e.g. Chile → often **`sa-santiago-1`** if that is your home region). Write down the **region identifier** exactly as shown for API/CLI.
2. Open **Storage** → **Buckets** → **Create bucket**.
3. **Name** — must be unique in the compartment; use lowercase, e.g. `francis-ingest-dev` or `estacion-francis-runs-dev`.
4. **Standard** tier; default encryption is fine.
5. Fill the table below with **region + bucket name**; for **prefix**, pick one pattern and stick to it (examples below).

### Suggested prefix (agree with estacion-inmobiliaria)

- **`francis-runs/`** — keys like `francis-runs/<run_dir>/LISTINGS_ABC12345.NDJSON`
- Or mirror manifest paths: **`ingest/{ingestion_run_id}/`** — keys like `ingest/<uuid>/listings.ndjson`

### Optional — CLI (after `oci setup config` and API key)

```bash
oci os bucket create --compartment-id "<COMPARTMENT_OCID>" --name "francis-ingest-dev"
```

Use the same region as in `~/.oci/config`.

| Field | Value |
|-------|--------|
| Region (public name) | **`sa-santiago-1`** |
| Bucket name | **`bucket-20260402-0333`** |
| Object key prefix pattern | **`francis-runs/`** (objects: `francis-runs/<run_folder>/LISTINGS_<SHORT>.NDJSON` or equivalent) |

Francis does **not** upload to OCI by default; use a script/cron/`oci os object put` after each run.

## Next steps (shared)

1. [x] Bucket + prefix + region filled in here; [ ] same values copied to `docs/FRANCIS_SUITE_HANDOFF.md` (estacion-inmobiliaria)
2. [ ] Upload path automated from VM (or CI)
3. [ ] Real-estate workflow / production runs when ready
4. [ ] E2E: object in bucket → job → Postgres → `/buscar`

*Last aligned: region `sa-santiago-1`, bucket `bucket-20260402-0333`, prefix `francis-runs/`.*
