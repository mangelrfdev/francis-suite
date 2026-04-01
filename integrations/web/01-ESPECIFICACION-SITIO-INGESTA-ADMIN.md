# Especificación de producto — Sitio web + panel admin + pipeline de datos

**Para:** implementación en el repo del sitio (Estación Inmobiliaria u otro front).  
**Contexto:** este documento resume arquitectura, datos y UX acordados con el pipeline **Francis Suite** + **GCP** + **Supabase**. El objetivo es que el sitio, la base de datos y el admin tengan **cada cosa en su lugar**.

**Idioma del código:** según el repo (TypeScript, etc.). **Esta spec** puede vivir en español para el equipo.

---

## 1. Visión en una frase

Scrapers declarativos (Francis) generan **archivos estructurados + metadata de corrida** → almacenamiento → **ingesta** a Postgres → **sitio público** lee la DB; el **panel de administración** permite **auditar corridas**, **previsualizar cambios**, gestionar **duplicados** y, en fases avanzadas, **aprobar** antes de impactar datos visibles.

---

## 2. Arquitectura lógica (quién hace qué)

| Capa | Responsabilidad | Tecnología de referencia |
|------|-----------------|---------------------------|
| Extracción | Scrape, normalización, validación ligera, export NDJSON/CSV | **Francis Suite** (workflows XML) |
| Ejecución programada | Disparar scrapers cada X tiempo | **GCP Cloud Scheduler** → **Cloud Run** (contenedor que ejecuta `francis-suite run …`) |
| Artefactos | Guardar archivos por corrida y fuente | **GCS** (ruta tipo `runs/{ingestion_run_id}/{source}/listings.ndjson`) |
| Base de datos | Fuente de verdad para el sitio | **Supabase (Postgres)** |
| Ingesta | Leer NDJSON, upsert, diff opcional, escribir staging o producción | Job (Edge Function, Cloud Function, servicio Node/Python) **en el proyecto web o repo aparte** |
| Sitio público | Listar/filtrar propiedades | Frontend (Next.js, etc.) **solo lectura** a datos publicados |
| Admin | Historial, preview, duplicados, aprobaciones | Misma app o subdominio, **autenticación obligatoria** |

**Regla:** el frontend público **no** lee buckets ni archivos crudos; lee **tablas** (o vistas) en Postgres.

---

## 3. Contrato de datos por aviso (mínimo)

Cada línea del NDJSON (o fila CSV) debe incluir al menos:

| Campo | Tipo | Notas |
|-------|------|--------|
| `external_id` | string | ID estable en ese portal; si no existe, regla documentada (ej. hash URL canónica). |
| `source` | string | snake_case estable, ej. `portal_mercadolibre`. |
| `title` | string | |
| `price` | number | Sin símbolos; punto decimal si aplica. |
| `currency` | string | `CLP` o `UF` normalizado. |
| `property_type` | string | ej. `departamento`, `casa`. |
| `operation_type` | string | `arriendo` o `venta`. |
| `comuna` | string | Texto como en el portal (idealmente normalizar después). |
| `bedrooms` | number \| null | |
| `bathrooms` | number \| null | |
| `surface` | number \| null | m² o null. |
| `image_url` | string \| null | HTTPS absoluta. |
| `source_url` | string | URL pública del aviso (obligatorio). |
| `published_at` | string \| null | ISO 8601 si existe. |

**Opcionales generados en pipeline:**

- `scraped_at` — ISO 8601, momento de extracción.
- `ingestion_run_id` — identificador de la corrida (debe coincidir con carpeta/manifest).

**Clave natural de negocio:** `(source, external_id)` — upsert idempotente.

**Convenciones:** UTF-8; una fila por aviso; sin cabeceras repetidas a mitad de archivo (CSV: cabecera solo al inicio).

---

## 4. Qué entrega Francis (y qué no)

**Sí (objetivo del workflow):**

- Archivo canónico NDJSON/CSV en ruta predecible.
- Sesión con nombre / logs (trazabilidad en logs de Cloud Run).
- Si el workflow usa records: metadata de guardado, archivos auxiliares de **duplicados** / **errores de validación** (según hands configurados).

**No es obligación del motor del sitio:**

- Francis **no** sustituye al job de ingesta ni al panel; **emite** datos y metadata acordada.

**El sitio debe asumir:** puede existir un **manifest** por corrida (`run.json` en GCS o fila en `ingestion_runs`) con: `ingestion_run_id`, `source`, timestamps, conteos, paths a artefactos, estado.

---

## 5. Tablas sugeridas (Postgres / Supabase)

Nombres orientativos; ajustar al estilo del proyecto.

### 5.1 `properties` (o nombre de negocio)

Columnas alineadas al contrato + columnas de control:

- Todas las de negocio del §3.
- `last_ingestion_run_id` (FK opcional) — **linaje**: de qué corrida vino la última actualización.
- `updated_at`, `created_at`.

**Índice único:** `(source, external_id)`.

### 5.2 `ingestion_runs`

- `id` (uuid, PK) — mismo valor que `ingestion_run_id` en archivos.
- `source` (text).
- `started_at`, `finished_at`.
- `status` — `pending` \| `success` \| `partial` \| `failed`.
- `rows_total`, `rows_valid`, `rows_rejected` (enteros).
- `artifact_uri` — URI del NDJSON en GCS (o path lógico).
- `manifest_uri` — opcional, JSON de metadata extendida.
- `error_message` — nullable.
- `workflow_version` — opcional (string).

### 5.3 Opcional: staging (modo “aprobación humana”)

- `staging_properties` o tabla genérica `ingestion_proposals` con JSONB del diff.
- Estados: `pending_review` → `approved` → job copia a `properties`.

### 5.4 Opcional: eventos / auditoría

- `audit_log` — quién aprobó, cuándo, qué run.

**RLS:** políticas estrictas: público **solo lectura** a vistas/materialized si aplica; admin con rol `service_role` o JWT de admin **solo** en rutas server-side.

---

## 6. Panel de administración — alcance por módulos

Cada módulo debe tener **ruta en el router**, **rol requerido** y **datos de API**.

### 6.1 Dashboard / resumen

- Últimas N **ingestion runs** (fecha, fuente, estado, conteos).
- Indicadores: última corrida exitosa por `source`, tasa de error simple.
- Enlaces rápidos a detalle de corrida.

### 6.2 Historial de sesiones (ingestion runs)

- Lista paginada/filtrada por `source`, rango de fechas, estado.
- Detalle de una corrida: metadata, link a log (Cloud Logging o URL guardada), link a artefacto en Storage (firmado o vía backend), tabla resumen de conteos.

### 6.3 Preview de ingesta (cuando el job lo soporte)

- Para una corrida completada pero no aplicada (o modo staging): mostrar **nuevos**, **actualizaciones** (cambio de precio, título), **sin cambios**, **retirados del listado** (si la lógica lo define).
- Vista tabular con columnas clave; filtros.

### 6.4 Duplicados y conflictos

- Lista de conflictos: mismo `(source, external_id)` con datos inconsistentes en un lote, o duplicados detectados por el pipeline.
- Acción: regla por defecto (última corrida gana) o resolución manual documentada.

### 6.5 Aprobación (fase WOW opcional)

- Botón **“Aplicar a producción”** solo para rol admin.
- Solo habilitado si `ingestion_runs.status` y reglas de negocio lo permiten.
- Tras aplicar: actualizar `properties`, marcar run como `applied_at` o equivalente.

### 6.6 Salud de datos

- Avisos sin `image_url`, precios fuera de rango, comunas vacías — queries de calidad simples.

### 6.7 Linaje

- En ficha de propiedad (admin): mostrar `last_ingestion_run_id` y link al detalle de esa corrida.

---

## 7. Ideas “WOW” para portfolio (reclutadores)

Priorizar las que se puedan **defender en entrevista** (no solo UI).

1. **Ingestion runs como primera clase** — No es un CRUD genérico: es el corazón operativo del negocio.
2. **Staging + aprobación** — Muestra pensamiento en **riesgo** y **gobernanza de datos**.
3. **Linaje por fila** — `last_ingestion_run_id` y link a la corrida.
4. **Diff / preview** antes de producción — “Qué va a cambiar” en lenguaje de negocio.
5. **Observabilidad** — Estado de corridas, errores visibles, no solo “falló”.
6. **Demo de 30 segundos** — Narrar: corrida → aparece en historial → preview → aprobar → sitio actualizado.

---

## 8. Flujos de usuario (admin)

1. **Consultivo:** Admin abre historial → abre una corrida → ve conteos y enlaces → no aplica cambios (solo auditoría).
2. **Con staging:** Job escribe propuesta → admin revisa preview → aprueba → datos en `properties`.
3. **Directo (MVP):** Job hace upsert automático tras corrida; admin solo **monitorea** historial y salud (menos WOW, más simple).

Definir cuál es **MVP** y cuál es **fase 2** en el mismo README del repo web.

---

## 9. Seguridad y secretos

- Claves de Supabase service role **solo** en servidor (Edge Function, API route, Cloud Function), nunca en el bundle del cliente admin sin protección.
- Buckets GCS: acceso por **signed URLs** generadas en backend o cuenta de servicio; no exponer credenciales en el front.
- Admin protegido por **auth** (Supabase Auth u otro) + verificación de rol.

---

## 10. Separación para el equipo / otros asistentes

| Repo / herramienta | Propósito |
|---------------------|-----------|
| **francis-suite** | Workflows de extracción, formato de salida, metadata de sesión en medida de lo declarado en XML. |
| **Repo sitio web** | UI pública, UI admin, esquema Supabase (migraciones), jobs de ingesta, integración con GCS. |
| **GCP** | Scheduler, Run, Storage, IAM, secretos de runtime del scraper. |

Este archivo es **entrada de producto** para el Cursor del sitio web: implementar rutas, tablas, componentes y APIs según prioridad MVP vs fase 2.

---

## 11. Checklist de entrega mínima (sitio + datos)

- [ ] Tabla `properties` con índice único `(source, external_id)`.
- [ ] Tabla `ingestion_runs` y escritura desde el job al finalizar/fallar corrida.
- [ ] Admin: lista + detalle de `ingestion_runs`.
- [ ] Sitio público: lectura solo de datos listos para mostrar.
- [ ] Documento o pantalla interna: reglas de `external_id` cuando el portal no expone ID.

---

## 12. Glosario rápido

- **NDJSON / JSON Lines:** una línea = un objeto JSON; UTF-8.
- **Upsert:** insert o update según clave natural.
- **Linaje:** saber qué proceso/corrida produjo un dato en la tabla.
- **Staging:** datos pendientes de revisión antes de producción.

---

*Copia portable desde `integrations/web/`; ajustar nombres de tablas y rutas según el stack elegido.*
