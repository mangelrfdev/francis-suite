# Flujo de datos — una página

## Diagrama en texto

```
[ Portales web ]
       │
       ▼
[ Francis Suite ]  ← workflows XML, scrape + normalización + record-save NDJSON
       │
       ▼
[ GCP Cloud Run ]  ← ejecución programada (Scheduler dispara el contenedor)
       │
       ▼
[ GCS bucket ]     ← runs/{ingestion_run_id}/{source}/listings.ndjson (+ opcional run.json)
       │
       ▼
[ Job de ingesta ] ← lee NDJSON, valida, upsert; opcional: staging antes de prod
       │
       ▼
[ Supabase Postgres ]  ← tabla properties + ingestion_runs (+ staging si aplica)
       │
       ├──────────────────────┐
       ▼                      ▼
[ Sitio público ]      [ Panel admin ]
  solo lectura            auth + historial + preview + aprobación
```

## Frases útiles para el otro Cursor

- **El sitio no ejecuta Francis:** solo consume datos ya en Postgres (y opcionalmente metadatos de corridas vía API).
- **La clave de negocio es** `(source, external_id)` **en** `properties`.
- **Cada corrida de scrape** debe poder registrarse en `ingestion_runs` para el panel (historial, WOW, linaje).
- **GCP** es donde viven los **artefactos** y la **ejecución** del extractor; **Supabase** es donde vive lo que ve el usuario final.

## Qué implementa el repo del sitio (resumen)

| Pieza | Dónde |
|-------|--------|
| Tablas, RLS, migraciones | Supabase / SQL en el repo web |
| API o server actions que hablen con la DB | Repo web (backend) |
| Job que lee GCS e inserta | Repo web o servicio aparte (mismo equipo) |
| UI pública + UI admin | Repo web |

## Qué NO implementa el repo del sitio

- Definición de scrapers Francis (eso es **repo francis-suite** u otro repo de workflows).
