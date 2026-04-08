# Qué pedirle al Cursor del sitio web para alinear `record-create` (Francis)

Francis exporta filas según el **schema del `<record-set-field>`**. La tabla Postgres del sitio debería coincidir en **nombres de columnas** y **tipos** (o el job de ingesta mapea explícitamente).

Copiá o pedí en el repo del **sitio web**:

## 1. Migración SQL o definición de tabla `properties` (o nombre real)

- Lista de **columnas** con tipos: `text`, `numeric`, `timestamptz`, `integer`, `jsonb`, etc.
- **Índice único** acordado: normalmente `(source, external_id)`.
- Columnas extra solo del producto: `last_ingestion_run_id`, `created_at`, `updated_at`, `active`, etc.

## 2. Tipos TypeScript / Zod (si existen)

- El **mismo** shape que espera el front o el job de ingesta al leer NDJSON.

## 3. Valores permitidos (enums)

- `currency`: `CLP` \| `UF` (u otros).
- `property_type`, `operation_type`: lista cerrada o convención de strings.

## 4. Campos que vienen solo del scrape vs solo del sistema

- Ej.: `scraped_at` lo rellena el workflow; `last_ingestion_run_id` lo rellena el job al insertar.

## 5. Una línea de ejemplo

- Un **objeto JSON** de una fila “ideal” como la guardaría Supabase después del upsert.

## 6. Fechas en `record-set-field` tipo `datetime` (Francis)

- En el engine, valores como `YYYY-MM-DDTHH:MM:SS` **sin** sufijo `+00:00` en el XML (ver `examples/demos/record_pipeline_minimal.xml`).
- El job de ingesta puede convertir a `timestamptz` en Postgres según convenga.

---

Con eso, en **francis-suite** se ajusta el `<record-create>` para que el NDJSON **aplane** al mismo contrato (nombres snake_case iguales a la tabla, o documentación de mapeo 1:1).

**Referencia de contrato mínimo (producto):** `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md` §3.

---

## Respuesta desde el repo del sitio (Estación Inmobiliaria)

Cuando el equipo del **sitio web** ya respondió, los artefactos suelen estar **en ese repo** (no en francis-suite). Ejemplo de layout entregado:

| Recurso | Ruta típica |
|---------|-------------|
| Migración `properties` | `supabase/migrations/20260401100000_properties.sql` |
| Migración `ingestion_runs` (+ FK `last_ingestion_run_id`, etc.) | `supabase/migrations/20260401120000_ingestion_runs.sql` |
| Resumen + JSON de ejemplo “como en producción” | `docs/FRANCIS_SCHEMA_PROPERTIES.md` |
| Tipo `Property` | `lib/types.ts` |
| Índice de docs | `docs/README.md`, `docs/HANDBOOK.md`, `docs/ARCHIVOS-NUEVOS.md` |

**Reglas que suelen cerrar con Francis:**

- NDJSON / filas con **snake_case** alineado a columnas SQL.
- **Único negocio:** `(source, external_id)`.
- Enums en texto (ej. CHECK o app): `currency` **CLP \| UF**; `property_type` **departamento \| casa**; `operation_type` **arriendo \| venta**.

**Mensaje corto para pegar en Cursor (Francis Suite), si ya existe el repo del sitio:**

> En estacion-inmobiliaria: `docs/FRANCIS_SCHEMA_PROPERTIES.md`, migraciones `supabase/migrations/20260401100000_*.sql` y `20260401120000_*.sql`, tipos en `lib/types.ts`. NDJSON con snake_case igual que la tabla; único `(source, external_id)`; currency CLP|UF, property_type departamento|casa, operation_type arriendo|venta. Ajustar `record-create` en francis-suite a eso.

**Nota:** `examples/demos/record_pipeline_minimal.xml` ya usa esos campos y enums de ejemplo; compará nombres exactos con la migración real (si difieren, renombrá `record-set-field` o mapeá en el job de ingesta). Material de producto web: carpeta **`integrations/web/`** en francis-suite.

**Campo opcional `publisher_name`:** guía paso a paso (SQL, TS, ingesta, UI) en **`PUBLISHER_NAME-ROLLOUT.md`**.
