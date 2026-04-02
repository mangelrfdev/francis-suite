# GCP: motor Francis, artefactos e ingesta a Supabase

Este documento **ordena** qué hace cada pieza en Google Cloud, cómo encaja con **Francis Suite** y con el **sitio web** (Supabase). No sustituye el detalle línea a línea del NDJSON: eso sigue en el repo del sitio, p. ej. `docs/INGESTION-JOB-NEXT-STEPS.md`.

**Facturación / proveedor:** Google Cloud suele pedir **tarjeta** y a veces un **cargo o garantía** de verificación al activar facturación. Si elegís **Oracle Cloud Infrastructure (OCI) Free Tier** (u otro cloud) por eso, **el flujo es el mismo**: ejecutar Francis → subir NDJSON a **almacenamiento de objetos** → job que lee y escribe **Supabase**. Los nombres cambian (GCS → bucket OCI, etc.); ver §10.

---

## 1. Idea central (qué “subís” y qué no)

| Pregunta | Respuesta corta |
|----------|-----------------|
| ¿Subimos “el motor” a GCP? | Sí en el sentido de **ejecutar** Francis (contenedor o VM) en GCP de forma **programada** o bajo demanda. El **código** del motor vive en **git** (francis-suite); en GCP corre un **build** (imagen) o un entorno que lo instala. |
| ¿Guardamos el motor en un bucket? | **No** como sustituto del repo. En **GCS** guardás **salidas**: NDJSON, manifiestos, logs de corrida. El motor es código versionado, no el archivo principal del bucket. |
| ¿Quién escribe en la base de datos? | Un **job de ingesta** (servicio en GCP o en el backend del sitio) que **lee** el NDJSON desde GCS y hace **upsert** en Supabase con la **service role** (nunca desde el navegador). |
| ¿El sitio ejecuta Francis? | **No.** El sitio lee **Postgres** (y opcionalmente metadatos de `ingestion_runs`). |

La data queda **ordenada para el sitio** cuando: (1) el NDJSON respeta el contrato de `properties`, (2) el job valida y normaliza, (3) Supabase tiene RLS acorde al producto.

---

## 2. Flujo recomendado (alto nivel)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. EJECUCIÓN DEL EXTRACTOR (Francis)                             │
│    Cloud Run Job / Cloud Run (servicio) / Compute VM / CI         │
│    Entrada: workflows XML + config (params, secrets desde Secret  │
│    Manager, no en el repo).                                        │
│    Salida: archivo(s) NDJSON en disco local del contenedor →       │
│    subida a GCS.                                                   │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ALMACENAMIENTO (GCS)                                          │
│    Bucket dedicado, p. ej. gs://.../runs/{ingestion_run_id}/     │
│         {source}/listings.ndjson                                  │
│    Opcional: run.json (metadata), logs.                           │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. JOB DE INGESTA                                                │
│    Cloud Run (HTTP o evento), Cloud Function, o Worker en tu      │
│    backend Next.js disparado por cola/webhook.                    │
│    Lee NDJSON desde GCS → valida → upsert `properties` →          │
│    insert/actualiza `ingestion_runs` (status, conteos, URIs).     │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SUPABASE + SITIO                                              │
│    Misma tabla `properties` que ya consume el listado y admin.   │
└─────────────────────────────────────────────────────────────────┘
```

**Disparadores típicos del paso 3:**

- **Evento en GCS** (nuevo objeto en prefijo `runs/...`) vía Eventarc → Cloud Run/Function.
- **Cloud Scheduler** que llama a un endpoint “procesar último run” o encola un mensaje.
- **Manual** desde admin (botón “aplicar corrida”) que invoca el mismo servicio.

Elige uno para MVP; Eventarc + objeto nuevo es muy alineado con “archivo cerrado en GCS”.

---

## 3. Qué implementa cada repo

| Pieza | Repo / lugar |
|-------|----------------|
| Workflows Francis, `record-save` NDJSON | **francis-suite** |
| Dockerfile o script “run + upload to GCS” | **francis-suite** o repo “deploy” tuyo (documentá dónde queda) |
| Bucket GCS, IAM, Scheduler, Eventarc | **Infra** (Terraform / consola / doc en sitio) |
| Contrato SQL `properties`, `ingestion_runs` | **estacion-inmobiliaria** (migraciones) |
| Código del job que lee GCS y escribe Supabase | **estacion-inmobiliaria** o microservicio aparte (mismo equipo) |
| Detalle NDJSON (`_type`, `export`, errores por línea) | **estacion-inmobiliaria** — `INGESTION-JOB-NEXT-STEPS.md` |

---

## 4. “Subir el motor a GCP” — opciones concretas

### A) Cloud Run Job (muy habitual para batch)

- Imagen con Python + `francis-suite` instalado (o copia del repo en build).
- Variables: `SUPABASE_URL` no hace falta en el runner de Francis si solo sube a GCS; sí secretos de portales si scrapeás.
- Comando: `francis-suite run workflow.xml` → script que sube `output/.../*.ndjson` a `gs://...`.
- **Cloud Scheduler** → ejecutar el Job cada N horas.

### B) Cloud Run (servicio) + endpoint interno

- Menos típico para scrape largo (timeouts, coste); útil si las corridas son cortas o disparadas por HTTP autenticado.

### C) VM + cron

- Simple para empezar; vos mantenés SO y actualizaciones.

### D) GitHub Actions (u otro CI) + `gcloud storage cp`

- Francis corre en CI, artefacto a GCS; el job de ingesta igual puede ser GCP. Útil si ya vivís en GitHub.

**Recomendación para portfolio clara:** **Cloud Run Job + GCS + segundo servicio (ingesta)** en GCP, o ingesta como ruta API en el proyecto Next con **service role** (menos piezas GCP, más acoplado al deploy del sitio).

---

## 5. Seguridad (mínimo indispensable)

- **GCS:** cuenta de servicio del runner Francis con permiso **solo** `storage.objects.create` (y list si hace falta) en el bucket de runs.
- **Job de ingesta:** cuenta de servicio con lectura GCS + **Supabase service role** en Secret Manager; nunca anon key para escribir `properties`.
- **Workflows:** URLs y credenciales de portales en **Secret Manager** o variables del Job, no en XML commiteado con secretos.

---

## 6. Fases sugeridas (orden de trabajo)

1. **Local:** NDJSON válido (`record_pipeline_minimal` o workflow real) alineado a migración `properties`.
2. **GCS:** bucket + subida manual del NDJSON (consola o `gsutil`) para probar el job sin aún automatizar Francis en GCP.
3. **Job de ingesta:** lee un objeto fijo o por `ingestion_run_id`, upsert en Supabase, escribe `ingestion_runs`.
4. **Francis en GCP:** imagen + Cloud Run Job + Scheduler que deja el archivo en GCS.
5. **Evento o Scheduler** que encadena “archivo listo → ingesta”.

Así **desacoplás**: el sitio ya mostró datos con seed; el job valida el pipeline real; el motor en la nube es el último eslabón de automatización.

---

## 7. Cómo se entrega la data “bien” al sitio

- **Contrato único:** columnas y CHECKs de Postgres (migración `properties`) = referencia.
- **Francis:** export con mismos nombres snake_case y enums (`CLP`/`UF`, etc.).
- **Job:** rechazar o loguear líneas inválidas; actualizar `ingestion_runs` con `rows_valid` / `rows_rejected`.
- **Sitio:** solo lectura a `properties`; admin ve corridas en `ingestion_runs`.

---

## 8. NDJSON, metadata, journal y cómo el job sabe qué leer

Francis puede generar **varios archivos** en la misma corrida (`record-save`, `record-save-metadata`, `record-save-duplicates`, journal, JSON, etc.). **No todo va a Postgres:** hay que acordar qué es **canónico** para el job.

### Qué suele ir a la base vs qué queda como artefacto

| Artefacto (ejemplos) | Rol típico |
|----------------------|------------|
| **Un NDJSON de filas de negocio** (`listings.ndjson` o `listings_{short_id}.ndjson` si el workflow lo parametriza) | **Entrada del job** → upsert en `properties` (una línea JSON = una fila lógica, según contrato del sitio). |
| **Journal** (`*.journal.ndjson`) | Auditoría / replay; el job **puede** ignorarlo en el MVP. |
| **Metadata pública / privata** (`*_metadata.json`) | Linaje, debug, admin; **no** suelen ser el archivo que “alimenta” el upsert masivo. |
| **Duplicados** | Revisión humana o métricas; opcional para el job. |

El detalle de líneas (`_type`, `export`, etc.) lo cierra el repo del sitio en **`INGESTION-JOB-NEXT-STEPS.md`**.

### IDs que conviene usar bien

| ID | Alcance | Para qué sirve |
|----|---------|----------------|
| **`ingestion_run_id`** | **Una corrida completa** (un batch) | UUID en DB (`ingestion_runs`); la carpeta en bucket puede ser `runs/{ingestion_run_id}/...` **o** un segmento auditable tipo `runs/{utc}_{short_id}_{source}/` si el workflow y el job acuerdan el mismo patrón. |
| **`source`** | Fuente de datos (portal, partner, etc.) | Subcarpeta y parte de la clave de negocio `(source, external_id)` en la tabla. |
| **`external_id`** | **Cada propiedad / aviso** | Va **dentro** de cada línea del NDJSON; identifica el ítem en el origen. |

Los **nombres de archivo** pueden ser **fijos por convención** (`listings.ndjson`, `run.json`) para que el job **no tenga que inventar** reglas raras: solo arma la ruta `prefix + nombres acordados`.

### Cómo “sabe” el job cuáles son los archivos (no adivina)

Elegís **una** estrategia y la documentás en el repo del sitio:

1. **Ruta determinística:** siempre el mismo patrón, p. ej.  
   `runs/{ingestion_run_id}/{source}/listings.ndjson`  
   **o** (ejemplo `all_books_pages`)  
   `{source}_{run_utc}_{run_short_id}/LISTINGS_{run_short_id}.NDJSON` bajo el prefijo `output/` (sin carpeta intermedia `runs/`).  
   y archivos opcionales **al mismo nivel** (journal, metadata, manifest).
2. **Evento con URI:** el storage dispara al cerrar un objeto; el payload trae la **URI completa** del NDJSON principal; el job descarga solo ese objeto (y si querés, hermanos por prefijo común).
3. **Manifiesto:** un `run.json` en la carpeta de la corrida lista URIs o nombres por rol (`primary_ndjson`, `journal`, …).

Francis debe escribir en disco con paths que el **script de subida** copie al bucket **preservando** esa jerarquía. En el CLI: **`--param ingestion_run_id=...`**, **`source=...`**, y si el workflow lo define, **`run_utc`**, **`run_short_id`** para carpeta y nombres de archivo auditable.

---

## 9. Relación con otros archivos de esta carpeta

| Archivo | Tema |
|---------|------|
| `02-FLUJO-DATOS-EN-UNA-PAGINA.md` | Diagrama corto del pipeline |
| `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md` | Tablas, admin, RLS |
| `seed-example-properties.sql` | Prueba manual en Supabase (sin GCS) |
| **Este archivo** | Rol de GCP, dónde corre Francis, dónde vive el job |

**Repo del sitio:** implementación fina del job y pasos E2E en `docs/INGESTION-JOB-NEXT-STEPS.md` (o el nombre vigente allí).

---

## 10. Oracle Cloud (OCI) Free Tier — mismo patrón, otros nombres

Si **GCP** no encaja por política de pago o garantías, **OCI** sirve para el mismo diseño:

| Rol en el diagrama | GCP (este doc) | OCI (orientativo) |
|--------------------|----------------|-------------------|
| Objeto NDJSON | Cloud Storage (GCS) | **Object Storage** (bucket) |
| Ejecutar Francis (batch) | Cloud Run Job / VM | **Compute** (VM Ampere/AMD free tier), o contenedor en VM |
| Programar corridas | Cloud Scheduler | **Cron** en la VM, o OCI **Events** + Functions (cuando lo tengas) |
| Job de ingesta | Cloud Run / Function | Mismo proceso en **otra VM**, **función** OCI, o **ruta en el backend** del sitio (lee vía API S3-compatible o URL firmada) |

**Supabase** sigue siendo la base del producto; OCI no la reemplaza. El job de ingesta necesita **Supabase service role** (secret), igual que en GCP.

**Idea práctica para empezar en OCI:** una **VM Always Free** + **bucket Object Storage** + script que tras `francis-suite run …` sube el `.ndjson` con `oci os object put` (o SDK); el job puede vivir en Vercel/Next con service role leyendo el objeto por URL firmada o descargándolo desde un endpoint interno.

---

*Ubicación: `integrations/web/08-GCP-PIPELINE-Y-JOB-INGESTA.md` en francis-suite.*
