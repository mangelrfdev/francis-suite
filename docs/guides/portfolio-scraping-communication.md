# Portfolio, scraping y cómo comunicar las decisiones (Estación Inmobiliaria + Francis)

Notas para **Miguel**: decisiones de producto/datos, marco mental sobre scraping, y **frases útiles** ante reclutadores o terceros. No es asesoría legal.

---

## 1. Qué estás construyendo (mensaje corto)

- **EstacionInmobiliaria.cl** (o demo): proyecto de **portafolio técnico** — agregación demostrativa de avisos, con datos mínimos, **enlace a la publicación original** y transparencia en el sitio (términos, contacto, baja).
- **Francis Suite**: motor declarativo de extracción; workflows exportan NDJSON alineado al contrato `listing` del sitio.

---

## 2. Decisiones de producto / datos (resumen)

| Decisión | Motivo |
|----------|--------|
| **Solo listados** (sin ficha detalle por defecto) | Menos requests por aviso, runs más cortos, menos carga en orígenes. |
| **Tope por run** (`maxListingRecordsPerRun` en `properties_workflow_template`) | Límite explícito por scraper/fuente; respeto operativo hacia los sitios. |
| **Alcance geográfico acotado** (ej. pocas comunas) | Menos superficie, más fácil de probar y mantener. |
| **Moneda Chile** (UF / CLP + fallback) | Contrato claro para ingest y UI. |
| **`publisher_name`** | Atribución “publicado por …” además de `source_url`; ver `integrations/web/PUBLISHER_NAME-ROLLOUT.md` y repo del sitio. |
| **`source`** (slug técnico) vs **marca en portal** | `source` identifica el pipeline/portal en ingest; `publisher_name` es la etiqueta visible (corredora/marca). |

---

## 3. Sincronización técnica (dónde vive cada cosa)

- **Francis:** `record-set-field` / `record-add-field` en `examples/demos/record_pipeline_minimal.xml`, `examples/demos/properties_workflow_template.xml` y gemelos `workflows/`.
- **Sitio (otro repo):** migración Postgres, tipos, job de ingesta, UI — ver mensaje de handoff y `integrations/web/07-PARA-FRANCIS-ALINEAR-RECORD-SCHEMA.md`.
- **Supabase:** columna nullable `publisher_name` en `properties` (no tabla nueva); aplicar migración en el proyecto correcto.

---

## 4. Scraping: marco mental (para vos y para explicar)

- **“Público en el navegador” ≠ “libre para cualquier reutilización”.** Los sitios tienen **términos de uso**; a veces limitan acceso automatizado o republicación.
- **`robots.txt`**: por dominio, en la raíz — `https://ejemplo.cl/robots.txt`. Es una señal para crawlers; **no reemplaza** términos ni resuelve todos los casos legales.
- **Portales grandes** suelen tener más ingeniería anti-abuso; **no** implica “están acostumbrados = te permiten scrapear”.
- **Agregadores** (Trovit, Mitula): peor **linaje** de datos para contar “fuente primaria”; mejor priorizar portales donde el aviso **nace**.
- **Prioridad práctica de fuentes** (solo como **orden de prueba técnica/narrativa**, no permiso): vertical chileno reconocible (Portal Inmobiliario, Toctoc, Emol propiedades, Economicos) antes que ML; evitar agregadores como primera historia; ML suele ser más exigente técnicamente.

---

## 5. Cómo explicarlo a un **reclutador** (guion ~30 s)

> “Uso datos que aparecen en sitios públicos para una **demo de portafolio**, pero no asumo que ‘visible’ sea ‘reutilizable sin contexto’. Limito **volumen y frecuencia**, guardo **solo lo necesario**, **siempre enlazo a la publicación original** y dejo **claro en el sitio** que es una demo técnica con canal de contacto. En un entorno **productivo** priorizaría **APIs, acuerdos o fuentes con licencia clara** y alinearía con legal/compliance del equipo.”

**Si preguntan por legalidad / vacío normativo:**

> “Depende del caso y la jurisdicción; por eso en demo **minimizo riesgo** y en empresa seguiría la **política del producto y abogados**. Entiendo la distinción entre hechos, bases de datos y contenido expresivo, pero no baso el diseño en un ‘gris’ — baso en **uso razonable, transparencia y límites**.”

**Si preguntan qué harías en la empresa:**

> “Primero fuentes **permitidas** o con contrato; si hubiera extracción automatizada, con **rate limits**, **monitoreo**, **atribución** y **plan de apagado** si el proveedor lo pide.”

---

## 6. Comunicación con **terceros** (reclamo, curiosidad)

- Responder con **tono profesional**: enlace a términos de tu proyecto, ofrecer **baja** o aclaración según tu proceso documentado.
- **No prometer** “no sabrán que scrapeás” como estrategia; la narrativa sólida es **transparencia + moderación**.

---

## 7. Probabilidad y expectativas (recordatorio)

- Baja probabilidad de que una corredora **concreta** entre por LinkedIn y reconozca su aviso **no** equivale a **riesgo cero** ni a permiso implícito.
- Objetivo del portafolio: mostrar **pipeline y producto**, no maximizar volumen de datos ajenos.

---

## 8. Referencias en este repo

| Tema | Archivo |
|------|---------|
| Contrato ingest / tablas | `integrations/web/01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md` |
| Alinear record con DB | `integrations/web/07-PARA-FRANCIS-ALINEAR-RECORD-SCHEMA.md` |
| `publisher_name` rollout | `integrations/web/PUBLISHER_NAME-ROLLOUT.md` |
| Template propiedades | `examples/demos/properties_workflow_template.xml` |
| Demo mínimo listing | `examples/demos/record_pipeline_minimal.xml` |

---

## 9. Mantenimiento

Cuando cambies **comunas**, **topes** o **campos** del `listing`, actualizá este doc solo si querés que siga siendo la “fuente narrativa” de decisiones; el **contrato técnico** manda en XML + migraciones + ingest.
