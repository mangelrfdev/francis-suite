# ADR-002 — HTTP Response Formats

## Contexto

Francis Suite necesita manejar respuestas HTTP de distintos tipos —
texto, binarios, archivos grandes, datos estructurados — de manera
eficiente, predecible y sin consumir recursos innecesarios.

La pregunta central era: ¿cómo debe `httpx-call` devolver la respuesta,
y cómo debe el usuario indicar qué formato espera?

---

## Decisión

`httpx-call` tiene un atributo `response` que controla cómo se devuelve
el contenido. Los valores posibles son:

| Valor | Comportamiento interno | Cuándo usarlo |
|---|---|---|
| `text` | `response.text` — string decodificado | HTML, XML, CSV, JSON, texto plano |
| `binary` | `response.content` — bytes crudos | PDF, Excel, Word, ZIP, imágenes |
| `stream` | escribe directo a disco chunk por chunk | Video, audio, archivos grandes (+50MB) |

`text` es el valor por defecto — compatible con el comportamiento actual.

**Cookie jar (sesión):** `auto-cookies="true"` en `<httpx-call>` usa un `httpx.Client` compartido por la sesión del workflow para enviar cookies entre llamadas (como un navegador). `<httpx-close/>` cierra el cliente y bloquea `<httpx-call>` y las hands de introspección hasta que termine `<set-proxy>` de nuevo. Ver [guides/httpx-call.md](../guides/httpx-call.md).

---

## Reglas por formato

### Texto y datos estructurados
- **JSON** → `response="text"` — en bruto, sin conversión
- **XML** → `response="text"` — en bruto, sin conversión
- **HTML** → `response="text"` — luego `convert-html-to-xml` lo procesa
- **CSV** → `response="text"` — en bruto, sin conversión
- **SVG** → `response="text"` — es XML, texto plano

### Documentos
- **PDF** → `response="binary"` — bytes crudos, sin conversión
- **Excel (.xlsx)** → `response="binary"` — bytes crudos, sin conversión
- **Word (.docx)** → `response="binary"` — bytes crudos, sin conversión
- **ZIP** → `response="binary"` — bytes crudos, sin conversión

### Imágenes
- **JPG, PNG, WebP, GIF** → `response="binary"` para guardar en disco
- Para pasar a `use-ia` → `response="binary"`, el hand convierte internamente si la API lo requiere

### Audio y video
- **MP3, WAV, MP4, y similares** → `response="stream"` obligatorio
- Son archivos grandes — cargarlos en RAM como `binary` es un error

### APIs
- **REST JSON** → `response="text"` — en bruto
- **REST binaria** → `response="binary"` o `response="stream"` según tamaño
- **SOAP XML** → `response="text"` — en bruto
- **GraphQL** → `response="text"` — JSON en bruto

---

## Regla general

```
Es texto                          → text (default)
Es binario pequeño/mediano        → binary
Es binario grande (+50MB)         → stream obligatorio
Requiere base64                   → lo maneja la hand destino internamente
```

---

## Base64 — decisión explícita

Base64 NO es una opción de `response` en `httpx-call`.

**Razones:**
- Base64 es 33% más pesado que el binario original
- Si el servidor devuelve base64, se recibe como `text` y se decodifica
  donde se necesite — no automáticamente
- Si una API destino requiere base64 (como APIs de visión IA), la hand
  correspondiente (`use-ia`) maneja la conversión internamente
- El usuario nunca necesita saber si algo se convirtió a base64 o no

---

## `file-download` y `file-upload` — decisión de eliminación

`file-download` y `file-upload` fueron eliminados del framework.

**Razones:**
- `file-download` era `httpx-call` + `file-write` combinados — redundante
- `file-upload` cubría solo multipart POST — caso muy específico
- Cada cliente futuro (playwright, scrapling) manejará sus propias
  descargas internamente dentro de su propio contexto
- `httpx-call` con `response="binary"` o `response="stream"` + `file-write`
  cubre todos los casos de descarga con httpx
- Menos tags = framework más simple y predecible

---

## Consecuencias

- `httpx-call` necesita implementar `response="binary"` y `response="stream"`
- `file-write` necesita soportar `encoding="binary"` correctamente con `open("wb")`
- `file-download` y `file-upload` se eliminan del codebase y la documentación
- `use-ia` manejará la conversión a base64 internamente cuando sea necesario
- Para archivos grandes siempre usar `response="stream"` — nunca `binary`

---

## Ejemplos

```xml
<!-- HTML scraping — default -->
<box-def name="html">
    <httpx-call url="https://ejemplo.com"/>
</box-def>

<!-- JSON API -->
<box-def name="data">
    <httpx-call url="https://api.ejemplo.com/productos"/>
</box-def>

<!-- PDF -->
<box-def name="reporte">
    <httpx-call url="https://ejemplo.com/reporte.pdf" response="binary"/>
</box-def>
<file-write path="downloads/reporte.pdf" encoding="binary">
    <box name="reporte"/>
</file-write>

<!-- Excel -->
<box-def name="planilla">
    <httpx-call url="https://ejemplo.com/datos.xlsx" response="binary"/>
</box-def>
<file-write path="downloads/datos.xlsx" encoding="binary">
    <box name="planilla"/>
</file-write>

<!-- Imagen para procesar con IA -->
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<box-def name="datos_foto">
    <use-ia model="vision">
        <box name="foto"/>
    </use-ia>
</box-def>

<!-- Video — stream obligatorio -->
<httpx-call url="https://ejemplo.com/video.mp4" response="stream" path="downloads/video.mp4"/>
```
