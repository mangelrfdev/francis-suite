# Campo `publisher_name` (publicado por / corredora)

Contrato NDJSON / `listing` alineado entre **francis-suite** y el sitio (Estación Inmobiliaria). Nombre técnico en snake_case: **`publisher_name`**. En pantalla podés decir “Publicación de …” o “Publicado por …”.

## Orden recomendado (para no romper ingesta)

1. **Supabase (DB)** — migración con la columna.
2. **Repo web** — tipos + job de ingesta (mapear JSON → fila).
3. **Francis** — ya actualizado en `record_pipeline_minimal` y `properties_workflow_template` (y gemelos `workflows/`).

Si el job **ignora** claves desconocidas, podés desplegar Francis antes que la DB y no romper; si el job **falla** con columnas faltantes, hacé primero DB + ingesta.

---

## 1. Supabase — migración SQL

Crear archivo en el repo web, p. ej. `supabase/migrations/20260402120000_properties_publisher_name.sql`:

```sql
-- Nullable: scrapers viejos o cards sin dato en listado
ALTER TABLE public.properties
  ADD COLUMN IF NOT EXISTS publisher_name text;

COMMENT ON COLUMN public.properties.publisher_name IS
  'Display name of the listing publisher on the source portal (brand/agency).';
```

Aplicar con el flujo habitual del proyecto (`supabase db push`, CI, etc.).

---

## 2. Repo web — tipo TypeScript (ejemplo)

En `lib/types.ts` (o donde definas `Property`):

```ts
export type Property = {
  // ... campos existentes
  source_url: string;
  publisher_name: string | null;
  published_at: string | null;
  // ...
};
```

Si usás **Zod**, añadí algo equivalente:

```ts
publisher_name: z.string().min(1).nullable().optional(),
```

(Ajustá a la convención real del repo: `null` vs `undefined` vs omitir clave.)

---

## 3. Job de ingesta — mapeo NDJSON → Postgres

El nombre de la clave en cada línea del NDJSON debe ser **`publisher_name`** (igual que la columna).

Ejemplo **conceptual** (Node), donde `row` es un objeto ya parseado por línea:

```ts
const publisher_name =
  typeof row.publisher_name === "string" && row.publisher_name.trim() !== ""
    ? row.publisher_name.trim()
    : null;

await supabase.from("properties").upsert(
  {
    // ... otros campos
    source_url: row.source_url,
    publisher_name,
    // ...
  },
  { onConflict: "source,external_id" }
);
```

Si tu upsert usa un **spread** de columnas permitidas, incluí `publisher_name` en la lista blanca; si no, el campo se pierde aunque venga en el JSON.

---

## 4. Frontend — mostrar en la ficha (ejemplo React)

```tsx
{publisher_name ? (
  <p className="text-sm text-neutral-600">
    Publicación de <span className="font-medium">{publisher_name}</span>
  </p>
) : null}
```

Mantené el botón/enlace **“Ver publicación original”** con `source_url`.

---

## 5. Francis — qué tocar vos en cada scraper

| Archivo / bloque | Acción |
|------------------|--------|
| `<record-set-field name="publisher_name" …/>` | Ya está en los templates de referencia; en scrapers clonados copiá el mismo campo dentro de `<record-set-group name="listing">`. |
| `record-add-field` | Rellenar con XPath del portal o `${placeholderPublisherName}` fijo por fuente. |
| `properties_workflow_template` | Ajustá `xpathListingPublisherText` al nodo del listado; si no hay dato en la card, usá `placeholderPublisherName` (ej. marca del portal). |

**No** hace falta regenerar `schema/francis-workflow.xsd` por un campo nuevo de record (solo aplica a hands/tags).

---

## 6. Verificación rápida

```bash
uv run francis-suite run examples/demos/record_pipeline_minimal.xml
```

Abrí `output/record_pipeline_minimal/listings.ndjson`: las filas `listing` deben incluir `"publisher_name": "..."` cuando el demo lo rellena.

---

## Referencia cruzada

- Contrato mínimo producto: `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md` §3.
- Alinear con DB: `07-PARA-FRANCIS-ALINEAR-RECORD-SCHEMA.md`.
