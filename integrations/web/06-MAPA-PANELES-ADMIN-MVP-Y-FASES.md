# Mapa de paneles, dashboards y páginas — MVP y fases

**Para:** alinear el repo del sitio (admin + público) con la estrategia **primero observar y auditar, después orquestar**.  
**Relacionado:** `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md`, `05-COMO-QUIERO-EL-PANEL-ADMIN.md`.

---

## Sitio público (fuera del admin)

| Ruta / área | Contenido |
|-------------|-----------|
| Listado de propiedades | Filtros básicos; datos desde DB (solo lectura). |
| Detalle de propiedad | Ficha pública. |
| (Opcional) Sobre / contacto | Estático. |

**No** incluye disparar scrapes ni ver archivos crudos de GCS.

---

## Admin — MVP (prioridad: cerrar valor sin orquestar GCP desde el browser)

Objetivo: **ver el estado del sistema**, **auditar corridas**, **gestionar datos ya en DB**, **preview/aprobación de ingesta** si implementan staging.

| # | Ruta sugerida | Qué es | Contenido principal |
|---|----------------|--------|----------------------|
| 1 | `/admin` o `/admin/dashboard` | **Dashboard** | KPIs: últimas corridas, semáforo por `source`, conteos rápidos, enlace a detalle. Botón **Actualizar** solo del bloque (ver `05`). |
| 2 | `/admin/runs` | **Historial de corridas** | Tabla `ingestion_runs`: fecha, `source`, estado, filas, errores. Filtros. **Actualizar** en la tabla. |
| 3 | `/admin/runs/[id]` | **Detalle de corrida** | Metadata, links a log/artefacto (signed URL vía backend), conteos, mensaje de error si falló. **Actualizar** solo este detalle. |
| 4 | `/admin/properties` | **Listado admin de propiedades** | Tabla con columnas clave; filtros; `last_ingestion_run_id` visible; link a detalle. **Actualizar** la lista. |
| 5 | `/admin/properties/[id]` | **Detalle admin** | Todo lo público + linaje (corrida que última vez tocó); opcional historial si lo guardan. |
| 6 | `/admin/health` o sección en dashboard | **Salud de datos** | Queries simples: sin imagen, sin comuna, etc. **Actualizar** el reporte. |

**Opcional MVP+ (si hay staging):**

| Ruta | Contenido |
|------|-----------|
| `/admin/ingestion/pending` | Cola de propuestas pendientes de aplicar; botón **Aplicar a producción** (con confirmación). |

**Login/Auth:** todas las rutas `/admin/*` protegidas por rol.

---

## Admin — Fase 2 (cuando el MVP esté estable)

**No** bloqueante para lanzar.

| Ruta / feature | Qué es |
|----------------|--------|
| **Disparar ejecución** (una fuente) | Botón “Ejecutar ahora” que llama al **backend** → GCP (Cloud Run/Job); **nunca** llaves en el cliente. |
| **Catálogo de workflows** | Lista de workflows XML/versiones (desde manifest o tabla); solo lectura al principio. |
| **Preview de archivo** | Vista parcial del NDJSON desde GCS (signed URL o líneas vía API). |
| **“Actualizar todo”** | Job asíncrono largo; pantalla de estado, no un click sin confirmación. |

---

## Navegación sugerida (sidebar o top)

- **Resumen** → Dashboard  
- **Corridas** → Lista + detalle  
- **Propiedades** → Lista + detalle  
- **Calidad** → Salud de datos  
- (Fase 2) **Orquestación** o **Workflows**  

---

## Qué NO va en el MVP del admin

- Disparar scrapes desde cualquier página sin auth fuerte.  
- Edición masiva de JSON en bruto.  
- Exponer **service role** de Supabase al navegador.  

---

## Resumen en una frase

**MVP:** dashboard + corridas + detalle de corrida + propiedades (lista/detalle) + salud de datos + **refresco por módulo**; **staging opcional** con aprobación.  
**Fase 2:** ejecutar jobs y catálogo de workflows desde la UI, con seguridad de backend.

---

*Documento vivo: al copiar al repo del sitio, ajustar rutas a la convención del framework (App Router, etc.).*
