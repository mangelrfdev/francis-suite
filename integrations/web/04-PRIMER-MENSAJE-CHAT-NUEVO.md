# Primer mensaje — pegar al abrir un chat nuevo en Cursor (sitio web)

Completá los `[...]` y copiá todo el bloque de **Contexto** como **primer mensaje** del chat.

---

## Contexto

**Proyecto:** Estación Inmobiliaria (agregador RM Chile) — repo del **sitio web** (front + admin + Supabase).

**Objetivo del código en este chat:** [ej. implementar tabla ingestion_runs + pantalla historial]

**Stack:** [ej. Next.js + Supabase + TypeScript]

**Pipeline de datos (no implementado en este repo, solo contexto):** los scrapers corren en **Francis Suite** en **GCP**; generan NDJSON en **GCS**; un **job** hace upsert en **Postgres**. Este repo implementa **consumo en DB**, **panel admin** y **sitio público** según la spec adjunta.

**Documentación de verdad:** el archivo `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md` en esta carpeta (o `@` ese archivo).

**Restricciones:** [ej. MVP primero: solo ingestion_runs listado, sin staging]

**Qué no quiero:** [ej. refactors masivos / cambiar todo el diseño sin pedirlo]

---

Cuando respondas, asumí este contexto y la spec en `01-…`. Si falta algo crítico, preguntá antes de diseñar en grande.
