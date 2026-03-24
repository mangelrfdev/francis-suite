# `<record-save>` — referencia (formatos implementados)

Hand que persiste un `FRecord` en disco. Solo estos formatos existen hoy en código:

| `format` | Descripción breve |
|----------|-------------------|
| `json` | Un archivo JSON: lista de objetos anidados (o envoltorio con `_metadata` + `data` si `include-metadata="true"`). |
| `csv` | Filas aplanadas con claves por punto; metadata pública como líneas `# name: value` al inicio si aplica. |
| `ndjson` | Una línea JSON por fila; opcionalmente primera línea de metadata con `_type: metadata`. |

**Diseño de formatos futuros** (xml, excel, etc.): [record-save-formats.md](record-save-formats.md).

---

## Atributos

| Atributo | Obligatorio | Valores | Notas |
|----------|-------------|---------|-------|
| `from` | Sí | nombre del record en el contexto (shared-box) | Debe existir un `<record-create name="…">` previo. |
| `format` | Sí | `json`, `csv`, `ndjson` (insensible a mayúsculas) | Otros valores → `ValueError` en `FRecord.save()`. |
| `path` | Sí | ruta de archivo | Soporta `${variables}`; se resuelve con el motor de expresiones. |
| `include-metadata` | No | `true` / `false` (default `false`) | Incluye **metadata pública** declarada en `<record-metadata>` dentro de `record-create`. Si no hubo metadata pública, el comportamiento sigue siendo válido (p. ej. JSON sin bloque `_metadata` o NDJSON sin línea de metadata). |

Todos los atributos de usuario pasan por `engine.resolve()` salvo flags booleanos interpretados en el hand (`include-metadata`).

---

## Comportamiento por formato

### `json`

- `include-metadata="false"` (default): escribe solo el array de filas (`self._rows`).
- `include-metadata="true"`: objeto con `"_metadata"` (mapa de metadata pública) y `"data"` (filas). Metadata vacía puede producir `"_metadata": {}`.

### `ndjson`

- Cada fila es un objeto JSON en una línea.
- Con `include-metadata="true"`: si hay metadata pública no vacía, la primera línea es un JSON con `"_type": "metadata"` y el resto de campos públicos.

### `csv`

- Sin filas: el archivo no se escribe (early return en `FRecord._save_csv`).
- Cabecera = unión ordenada de claves vistas al aplanar cada fila (`dict` anidado → claves `a.b.c`).
- Con `include-metadata="true"` y schema con metadata pública: líneas `# field_name: value` antes del CSV.

---

## Metadata privada y otros hands

- **Metadata privada / operativa** no es el foco de `record-save`. Para volcar solo eso: `<record-save-metadata>`.
- El runtime puede guardar metadata privada automáticamente bajo `sessions/<session_id>/` (ver README / architecture).

---

## Errores comunes

- Record inexistente o no es `FRecord` → mensaje del hand indicando que falta `record-create`.
- Formato no soportado → `[RECORD] unsupported format '…'` desde `FRecord.save()`.
- Record vacío → no escribe archivo; log `[RECORD] '…' is empty — skipping save`.
