# Post de LinkedIn - Presentacion del Portfolio (End-to-End)

## Version Principal (Recruiter-Friendly)

Hoy quiero compartir algo en lo que estuve trabajando: un portfolio tecnico end-to-end donde construi tanto la capa de datos como el producto que los consume.

Dos proyectos complementarios:
- Un **framework propio de extraccion y procesamiento de datos** en Python.
- **EstacionInmobiliaria.cl** — plataforma web de busqueda inmobiliaria construida sobre esos datos.

### Lo que resuelve en conjunto

Del dato crudo al usuario final, sin depender de APIs externas ni terceros:

- Pipelines declarativos en XML que estandarizan como se obtienen, transforman y exportan los datos.
- Plataforma web con filtros avanzados, favoritos y estados de carga/error bien resueltos.
- El output del framework alimenta directamente la base de datos que consume la plataforma.

### Stack completo

**Capa de datos (framework propio)**
- **Python 3.11+**
- **lxml** para parsing y XPath
- **httpx** para requests HTTP
- **Playwright** para automatizacion de browser
- **XML workflows** como capa declarativa
- **Docker** para containerizacion
- **Oracle Cloud** (principal) y **GCP** para infraestructura cloud
- **pytest + uv** para calidad y entorno

**Capa de producto (EstacionInmobiliaria.cl)**
- **Next.js 14 (App Router)**
- **TypeScript (strict mode)**
- **Tailwind CSS**
- **Supabase + PostgreSQL**
- **Vercel** para deploy

### Decisiones tecnicas destacables

**En la capa de datos:**
- Arquitectura por capas: parser → runtime → context → handlers reutilizables.
- Modelo de estado con boxes para trazabilidad del flujo de datos.
- Exportacion en NDJSON/JSON/CSV para consumo directo por otros sistemas.
- Containerizacion con Docker para consistencia entre entornos.
- Deploy en Oracle Cloud (capa gratuita) con experiencia adicional en GCP.

**En la capa de producto:**
- Cache de queries con `unstable_cache` para consultas repetidas.
- Reintentos limitados en queries para errores transitorios.
- Manejo de errores orientado a UX: no mostrar "0 resultados" cuando hay falla de conexion.
- Navegacion sin salto al top durante cambios de filtros (`scroll: false`).
- Deploy continuo en Vercel integrado con el flujo de desarrollo.

### Aprendizaje principal

Construir el stack completo me hizo entender algo importante:
**los problemas de UX muchas veces tienen raiz en la capa de datos**, y viceversa.
Tener control sobre ambos extremos — y sobre el deploy de cada uno — permite iterar con mucha mas velocidad y calidad.

Si te interesa, feliz de compartir arquitectura, decisiones de diseno y roadmap de ambos proyectos.

#Python #NextJS #TypeScript #PostgreSQL #Supabase #Docker #GCP #OracleCloud #Vercel #DataEngineering #Frontend #FullStack #SoftwareEngineering #Portafolio

---

## Version Corta

Comparto mi portfolio tecnico end-to-end: dos proyectos que se complementan.

Un **framework propio en Python** para pipelines declarativos de datos — containerizado con Docker y deployado en Oracle Cloud y GCP.

**EstacionInmobiliaria.cl** — plataforma web que consume esos datos (Next.js, TypeScript, Supabase/PostgreSQL), deployada en Vercel.

Aprendizaje principal: controlar tanto la produccion como el consumo de datos te da una perspectiva que no se consigue trabajando solo en uno de los extremos.

#Python #NextJS #TypeScript #Docker #OracleCloud #GCP #Vercel #DataEngineering #FullStack #Portafolio

---

## Mini Seccion de Portfolio (CV / GitHub / LinkedIn)

**Portfolio End-to-End: Framework de datos + EstacionInmobiliaria.cl**
**Rol:** Arquitectura, desarrollo de framework y producto web
**Stack:** Python, lxml, httpx, Playwright, XML, Docker, Oracle Cloud, GCP · Next.js, TypeScript, Tailwind, Supabase, PostgreSQL, Vercel

**Problema:** construir un producto web de datos sin depender de APIs externas, con control total sobre la calidad, estructura e infraestructura.

**Solucion:**
- Motor declarativo containerizado con Docker y deployado en cloud.
- Plataforma web con filtros, favoritos y UX responsive deployada en Vercel.
- Pipeline completo: ingestion → transformacion → exportacion → consumo en producto.

**Enfoque tecnico clave:** separar responsabilidades entre capa de datos y capa de producto, con contratos de datos claros y deploy independiente para cada capa.
