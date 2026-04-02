# Francis Suite ↔ estacion-inmobiliaria — sync status

Single-page mirror so this repo stays aligned with the web repo. **Canonical handoff** (updated by both sides): `docs/FRANCIS_SUITE_HANDOFF.md` in **estacion-inmobiliaria**.

## Agreed split

| Piece | Owner |
|-------|--------|
| Extract + NDJSON (e.g. `record_pipeline_minimal` → `listings.ndjson`: `_type` export line + `listing` rows) | francis-suite |
| Job, Supabase, public site, `/buscar` | estacion-inmobiliaria |

## NDJSON sample (contract for mapping)

- Run: `uv run francis-suite run examples/record_pipeline_minimal.xml`
- Output: `output/record_pipeline_minimal/listings.ndjson`

## OCI Object Storage — fill when infra is ready (names only, no secrets)

| Field | Value (placeholder) |
|-------|------------------------|
| Region (public name, e.g. `sa-santiago-1`) | _TBD_ |
| Bucket name | _TBD_ |
| Object key prefix pattern | _TBD_ (e.g. `runs/{ingestion_run_id}/{source}/listings.ndjson` or mirror `run_dir` from the workflow) |

Francis does **not** upload to OCI by default; use a script/cron/`oci os object put` after each run.

## Next steps (shared)

1. [ ] Bucket + prefix filled in here and in `FRANCIS_SUITE_HANDOFF.md`
2. [ ] Upload path automated from VM (or CI)
3. [ ] Real-estate workflow / production runs when ready
4. [ ] E2E: object in bucket → job → Postgres → `/buscar`

*Last aligned: pipeline status + NDJSON sample + pending OCI names._
