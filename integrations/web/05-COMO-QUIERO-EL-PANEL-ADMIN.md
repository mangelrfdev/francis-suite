# Cómo quiero el panel de administrador — datos, refresco y UX

**Para:** repo del sitio web (Next.js / React + Supabase u otro stack).  
**Objetivo:** que quede clarísimo **cómo se actualiza la data en pantalla**, cuándo sirve **F5** y cuándo quiero **botón “Actualizar” por módulo**, sin adivinar.

---

## 1. Cómo se “conecta” la data en el tiempo

- La **fuente de verdad** es **Postgres (Supabase)**. El panel **no** lee archivos de GCS ni Francis directamente; lee **tablas/vistas** y **APIs del propio backend** que consultan la DB.
- Cuando el **job de ingesta** termina y hace upsert, los datos **ya están en la DB**. El panel solo necesita **volver a pedir** esos datos (o recibir push si más adelante usamos realtime).

**Resumen:** “Conectarse y actualizar” = **volver a fetchear** desde el servidor lo que cambió en la DB, o **revalidar** la página si es SSR.

---

## 2. F5 (recargar página completa)

- **Sí:** con **F5** quiero que se **actualice todo lo que esa ruta carga** (como cualquier web seria).
- Es el comportamiento **por defecto** de seguridad: si algo quedó raro en caché, F5 lo arregla.
- No reemplaza botones por sección; **suma** a ellos.

---

## 3. Botón “Actualizar” por módulo (lo que pido explícito)

No quiero depender solo de F5 cuando estoy mirando **una sección** y quiero datos frescos **sin perder scroll/filtros** del resto.

| Módulo / pantalla | Qué debe hacer el botón “Actualizar” (o icono ↻) |
|-------------------|--------------------------------------------------|
| **Dashboard resumen** (KPIs, últimas corridas) | Volver a pedir **solo** los datos de ese dashboard (ej. invalidar query `dashboard` / refetch de `/api/admin/summary`). **No** recargar toda la app. |
| **Lista de ingestion runs** | Refetch **solo** la tabla de corridas (misma página, mismos filtros si los hay). |
| **Detalle de una corrida** (drawer o página) | Refetch **solo** el detalle de ese `run_id` + conteos asociados. |
| **Lista de propiedades (admin)** | Refetch **solo** la lista (con paginación/filtros actuales). |
| **Salud de datos / calidad** | Refetch **solo** las queries de ese reporte. |
| **Preview / staging** (si existe) | Refetch el **diff o propuesta** de esa corrida, no todo el admin. |

**Regla de oro:** el botón **no** debe simular F5 global salvo que sea un botón explícito “Recargar todo el panel” en **un** lugar (opcional, footer o ajustes).

---

## 4. Qué NO pido en el MVP (pero se puede más adelante)

- **WebSockets / Supabase Realtime** en cada tabla: **no obligatorio** al principio. Si el stack lo permite fácil, bienvenido para “la lista se actualiza sola”; si no, **polling ligero** o solo **refetch manual** por botón está bien.
- **Actualizar cada X segundos automático:** solo si es opt-in o en dashboard muy acotado (puede gastar cuota y marear).

---

## 5. Detalles de UX que quiero sí o sí

1. **Indicador “Última actualización”** en módulos con refresh manual: texto tipo *“Datos al 14:32:05”* tras un fetch exitoso.
2. **Estado de carga** al pulsar Actualizar: spinner o skeleton **solo en ese módulo**, no pantalla blanca entera si se puede evitar.
3. **Errores:** si falla el refetch, mensaje claro en ese módulo + posibilidad de reintentar.
4. **Consistencia:** mismo patrón en listas (runs, properties): arriba a la derecha **Actualizar** + timestamp opcional.

---

## 6. Ejemplo concreto (historia de usuario)

1. Entro a **Admin → Corridas**. Veo la tabla. Hago clic en **Actualizar** → se refresca **solo** la tabla; mis filtros “últimos 7 días” se mantienen.
2. Abro el **detalle** de una corrida. Pulso **Actualizar** ahí → se refresca **solo** el detalle y los números de esa corrida.
3. En otra pestaña termina el job de ingesta. Vuelvo a Corridas y pulso **Actualizar** → veo la corrida nueva **sin** F5.
4. Si algo va mal, **F5** como red de seguridad.

---

## 7. Relación con el pipeline (para no confundir)

- **Francis / GCP** actualizan **archivos** y luego el **job** actualiza la **DB**.
- El panel **solo refleja la DB**. “Actualizar” en el panel = “traer de nuevo el estado actual de la DB”, no “lanzar un scrape” (eso sería otro botón y otro flujo, si algún día se expone).

---

## 8. Una frase para el Cursor del sitio

> Implementar el admin con **datos desde Supabase/API**, **F5** para recarga completa de página, y **botón Actualizar por módulo** que haga **refetch acotado** (React Query / SWR / equivalente) sin recargar toda la SPA; mostrar **última actualización** y **loading** local por sección.

---

*Documento de intención de producto/UX; ajustar nombres de rutas y APIs al stack real del repo.*
