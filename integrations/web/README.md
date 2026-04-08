# Integración — producto web (Estación Inmobiliaria)

**Francis Suite** es un **framework general**; esta carpeta **no** es parte del núcleo del motor. Es **material de apoyo** para un proyecto que **usa** Francis (sitio agregador + Supabase + GCP): specs, admin UX, handoff con el otro repo.

**Narrativa portafolio + scraping + entrevistas:** [../docs/guides/portfolio-scraping-communication.md](../docs/guides/portfolio-scraping-communication.md).

El núcleo del framework sigue en `docs/architecture.md`, `docs/guides/record-save.md`, `francis_suite/`, etc.

---

## Ingestión y acuerdo con el otro repo

| Repo | Rol |
|------|-----|
| **francis-suite** | Workflows, `record-create` / `record-add`, exports NDJSON. |
| **estacion-inmobiliaria** | Tablas Postgres, tipos, **job de ingesta**, sitio y admin. |

Documento operativo en el sitio (NDJSON → DB, líneas `_type` / `export`, E2E): **`docs/INGESTION-JOB-NEXT-STEPS.md`** (en el repo del sitio).

Salida en VM / Docker OCIR lista para el job (paths, `LISTINGS_*.NDJSON`, `RUN_MANIFEST.JSON`, `DOCKER_UID`): **`09-DOCKER-OCI-CHECKLIST.md`** (Parte D).

Ejemplo de workflow alineado al contrato: **`examples/demos/record_pipeline_minimal.xml`**.

Estado compartido con el sitio (bucket/prefijo OCI cuando existan): **`FRANCIS-ESTACION-SYNC.md`**.

---

## Índice de archivos (copiar al otro Cursor o usar con `@`)

| Orden | Archivo | Contenido |
|-------|---------|-----------|
| 1 | **[`01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md`](01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md)** | Spec principal: tablas, admin, seguridad, checklist. |
| 2 | [`02-FLUJO-DATOS-EN-UNA-PAGINA.md`](02-FLUJO-DATOS-EN-UNA-PAGINA.md) | Pipeline en una página. |
| 3 | [`03-PARA-CURSOR-REGLAS-Y-TONO.md`](03-PARA-CURSOR-REGLAS-Y-TONO.md) | Reglas / tono para el repo del sitio. |
| 4 | [`04-PRIMER-MENSAJE-CHAT-NUEVO.md`](04-PRIMER-MENSAJE-CHAT-NUEVO.md) | Plantilla primer mensaje en Cursor. |
| 5 | [`05-COMO-QUIERO-EL-PANEL-ADMIN.md`](05-COMO-QUIERO-EL-PANEL-ADMIN.md) | Refresco F5 vs por módulo. |
| 6 | [`06-MAPA-PANELES-ADMIN-MVP-Y-FASES.md`](06-MAPA-PANELES-ADMIN-MVP-Y-FASES.md) | Rutas admin MVP vs fases. |
| 7 | [`07-PARA-FRANCIS-ALINEAR-RECORD-SCHEMA.md`](07-PARA-FRANCIS-ALINEAR-RECORD-SCHEMA.md) | Alinear `record-create` con la tabla `properties`. |
| — | [`PUBLISHER_NAME-ROLLOUT.md`](PUBLISHER_NAME-ROLLOUT.md) | Campo opcional `publisher_name`: SQL, tipos, ingesta, UI + Francis. |
| 8 | [`08-GCP-PIPELINE-Y-JOB-INGESTA.md`](08-GCP-PIPELINE-Y-JOB-INGESTA.md) | Nube (GCP u OCI), bucket, job → Supabase; **§8** NDJSON vs metadata/journal y cómo el job encuentra archivos. |
| 9 | [`09-DOCKER-OCI-CHECKLIST.md`](09-DOCKER-OCI-CHECKLIST.md) | Docker (conceptos + comandos), checklist OCI + pipeline; enlaza al `Dockerfile` del repo. |
| — | [`FRANCIS-ESTACION-SYNC.md`](FRANCIS-ESTACION-SYNC.md) | Estado compartido con estacion-inmobiliaria; bucket/prefijo OCI (rellenar). |
| — | [`seed-example-properties.sql`](seed-example-properties.sql) | `INSERT` de ejemplo para Supabase (misma tabla que listado + admin; `source = 'demo_seed'`). |

**Uso:** copiá **`integrations/web/`** entera al repo del sitio (p. ej. `docs/contexto-francis/`) o referenciá archivos con `@`.

---

*Ubicación en francis-suite: `integrations/web/` — todo lo que antes estaba disperso en `Archivos-nuevos/` y el puntero `docs/ingestion-job-handoff.md`.*
