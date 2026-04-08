# Docker, Oracle Cloud y pipeline — checklist ordenado

Guía para **buenas prácticas** (Docker + experiencia de portfolio) y **pendientes** mientras termina de aprovisionarse tu cuenta OCI.

---

## Parte A — Entender Docker (qué te llevas de experiencia)

| Concepto | En una frase |
|----------|----------------|
| **Imagen** | Receta + capas: SO, Python, dependencias, tu código; es **inmutable** una vez buildeada (salvo tags nuevos). |
| **Contenedor** | Una **instancia** de una imagen en ejecución (o parada): proceso aislado con su filesystem efímero salvo volúmenes. |
| **Dockerfile** | Instrucciones para **construir** la imagen (`FROM`, `COPY`, `RUN`, `CMD`). |
| **Build context** | Carpeta que Docker envía al daemon; `.dockerignore` evita meter `.git`, `output/`, cachés. |
| **Volumen** | Carpeta del **host** montada en el contenedor para **persistir** salidas (p. ej. `listings.ndjson`). |
| **CMD / ENTRYPOINT** | Comando por defecto al arrancar; lo podés **sobreescribir** al hacer `docker run ... otra-cosa`. |

**Flujo mental:** `docker build` → imagen local (o la subís a un **registry**: OCIR, Docker Hub). `docker run` → contenedor que ejecuta Francis y escribe en un volumen o sube a Object Storage.

**Comandos mínimos** (desde la raíz de **francis-suite**, con Docker Desktop o engine instalado):

```bash
docker build -t francis-suite:local .
docker run --rm -v "%cd%/docker-output:/app/output" francis-suite:local
# default CMD runs workflows/record_pipeline_minimal.xml (inside image)
```

(PowerShell: `-v "${PWD}/docker-output:/app/output"`. Linux/macOS: igual con `$PWD`.)

El workflow por defecto escribe bajo `output/...`; al montar `/app/output` los archivos quedan en `./docker-output` en tu máquina.

**Otro workflow:**

```bash
docker run --rm -v "${PWD}/docker-output:/app/output" francis-suite:local \
  francis-suite run workflows/record_pipeline_minimal.xml
```

---

## Parte B — Pendientes en orden (hasta pipeline completo)

Marcalos a medida que avanzás.

### B0 — Cuenta Oracle (donde estás ahora)

- [ ] Que termine el **aprovisionamiento** del tenancy (a veces tarda).
- [ ] Anotar **región** home, **OCID** del usuario/compartment (los vas a usar en CLI y Terraform después).
- [ ] Instalar **OCI CLI** (opcional pero útil) y hacer `oci setup config` cuando tengas API key.

### B1 — Docker local (Francis)

- [ ] Instalar **Docker Desktop** (Windows) o Docker Engine.
- [ ] En la raíz de francis-suite: `docker build -t francis-suite:local .` (ver `Dockerfile` en el repo).
- [ ] `docker run` con volumen y comprobar que aparece NDJSON (u otros exports) en `docker-output/`.
- [ ] `uv run pytest` en host cuando toques código (Docker no reemplaza tests en CI).

### B2 — Oracle Object Storage

- [ ] Crear **bucket** (p. ej. `francis-runs` o por entorno `dev`/`prod`).
- [ ] Políticas IAM: usuario o recurso que escriba objetos en ese bucket (principio de mínimo privilegio).
- [ ] Probar subida manual: `oci os object put` o consola web, con un `.ndjson` de prueba.

### B3 — Dónde corre Francis en OCI (elegí uno para MVP)

- [ ] **Opción simple:** VM **Always Free** (Ampere o AMD), Docker instalado en la VM, `git pull` + `docker build` o `uv sync`, **cron** diario: run workflow → subir objeto al bucket.
- [ ] **Opción más “cloud”:** misma VM pero imagen subida a **OCIR** (Oracle Container Registry); en la VM `docker pull` + `docker run` (menos drift).
- [ ] Documentar en un README propio del deploy (dónde está el workflow XML, secrets, horario).

### B4 — Job de ingesta → Supabase

- [ ] Implementación en **repo del sitio** (o microservicio): leer objeto desde OCI (SDK o URL firmada), parsear NDJSON, upsert `properties`, actualizar `ingestion_runs`.
- [ ] Secretos: **Supabase service role** en OCI **Vault** o en el proveedor donde hospedes el job (Vercel env, etc.) — nunca en el repo.
- [ ] Probar con un archivo que generaste desde Docker (mismo contrato que migración `properties`).

### B5 — Observabilidad y orden

- [ ] Logs de corrida (Francis + job) en un solo lugar razonable para debug.
- [ ] Convención de paths en bucket: `runs/{ingestion_run_id}/{source}/listings.ndjson` (alineado a `08-GCP-PIPELINE-Y-JOB-INGESTA.md`).

---

## Parte C — Relación con otros docs

| Archivo | Uso |
|---------|-----|
| `08-GCP-PIPELINE-Y-JOB-INGESTA.md` | Arquitectura nube (GCP u OCI); bucket + job + Supabase. |
| `Dockerfile` (raíz del repo) | Imagen reproducible con Playwright + `uv` + francis-suite. |
| Repo **estacion-inmobiliaria** | Job de ingesta fino, `INGESTION-JOB-NEXT-STEPS.md`. |

---

## Parte D — Salida lista para el job de ingesta (VM + `docker-compose.ocir.yml`)

Después de una corrida exitosa, el **contrato mínimo** para **estacion-inmobiliaria** (o sync a bucket) es:

| Artefacto | Rol |
|-----------|-----|
| `BOOKS_*/LISTINGS_<SHORT>.NDJSON` (o el prefijo que use el workflow) | Líneas NDJSON con `_type` / campos alineados al esquema de ingesta. |
| `BOOKS_*/RUN_MANIFEST.JSON` | Metadatos de corrida (timestamps, `run_short_id`, paths relativos si el workflow los escribe). |

**Ruta típica en la VM:** `~/francis-run/docker-output/<carpeta_de_corrida>/`.

**Permisos:** el `docker-compose.ocir.yml` del repo define `user: "${DOCKER_UID:-1000}:${DOCKER_GID:-1000}"` para que los archivos **no** queden como `root`. En `.env` de la VM podés fijar `DOCKER_UID` / `DOCKER_GID` a lo que devuelve `id -u` / `id -g`. Si alguna corrida anterior quedó en `root:root`, una vez: `sudo chown -R ubuntu:ubuntu ~/francis-run/docker-output`.

**Siguiente paso hacia producción:** subir el NDJSON (y opcionalmente el manifiesto) a **Object Storage** con un prefijo estable (ver convención de paths en `08-GCP-PIPELINE-Y-JOB-INGESTA.md`) y que el job lea desde ahí o por URL firmada.

---

## Parte E — Si GCP volvés más adelante

El mismo `Dockerfile` sirve en **Artifact Registry** + **Cloud Run Job**; solo cambia dónde subís la imagen y quién dispara el contenedor. OCI y GCP comparten el **mismo modelo mental**.

---

*Ubicación: `integrations/web/09-DOCKER-OCI-CHECKLIST.md`.*
