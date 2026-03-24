# httpx-call — Guía de uso

Tag para hacer peticiones HTTP.
Soporta: text, binary, stream.

---

## Uso básico — text (default)

Para HTML, XML, JSON, CSV y cualquier respuesta de texto.

```xml
<!-- GET simple -->
<box-def name="html">
    <httpx-call url="https://ejemplo.com"/>
</box-def>

<!-- GET con headers y params -->
<box-def name="data">
    <httpx-call url="https://api.ejemplo.com/productos">
        <httpx-header name="Authorization">Bearer ${token}</httpx-header>
        <httpx-param name="ciudad">santiago</httpx-param>
    </httpx-call>
</box-def>

<!-- POST -->
<box-def name="respuesta">
    <httpx-call url="https://api.ejemplo.com/login" method="POST">
        <httpx-param name="usuario">${usuario}</httpx-param>
        <httpx-param name="password">${password}</httpx-param>
    </httpx-call>
</box-def>
```

---

## response="binary" — archivos no-texto

Para PDF, Excel, Word, ZIP, imágenes.
Devuelve bytes crudos — guardar con `file-write encoding="binary"`.

```xml
<!-- descargar PDF -->
<box-def name="reporte">
    <httpx-call url="https://ejemplo.com/reporte.pdf" response="binary"/>
</box-def>
<file-write path="downloads/reporte.pdf" encoding="binary">
    <box name="reporte"/>
</file-write>

<!-- descargar Excel -->
<box-def name="planilla">
    <httpx-call url="https://ejemplo.com/datos.xlsx" response="binary"/>
</box-def>
<file-write path="downloads/datos.xlsx" encoding="binary">
    <box name="planilla"/>
</file-write>

<!-- descargar imagen para procesar con IA -->
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<box-def name="datos_foto">
    <use-ia model="vision">
        <box name="foto"/>
    </use-ia>
</box-def>

<!-- descargar imagen en loop -->
<loop item="producto" index="i">
    <loop-list>
        <box name="productos"/>
    </loop-list>
    <loop-body>
        <box-def name="foto">
            <httpx-call url="${producto_foto_url}" response="binary"/>
        </box-def>
        <box-def name="nombre_foto">
            <compose>downloads/fotos/producto_${i}.jpg</compose>
        </box-def>
        <file-write path="${nombre_foto}" encoding="binary">
            <box name="foto"/>
        </file-write>
    </loop-body>
</loop>
```

---

## response="stream" — archivos grandes (+50MB)

Para video, audio, datasets grandes.
Escribe directo a disco en chunks de 1MB — nunca carga todo en RAM.
Requiere atributo `path` obligatorio.
Usa archivo `.tmp` durante la descarga — si falla, el `.tmp` se elimina y el archivo final nunca se crea.

```xml
<!-- descargar video -->
<box-def name="archivo">
    <httpx-call url="https://ejemplo.com/video.mp4" response="stream" path="downloads/video.mp4"/>
</box-def>
<log>Descargado en: ${archivo}</log>

<!-- descargar con path dinámico -->
<box-def name="ruta">
    <compose>downloads/${nombre_archivo}</compose>
</box-def>
<box-def name="archivo">
    <httpx-call url="${url_video}" response="stream" path="${ruta}"/>
</box-def>
```

---

## Regla general por tipo de contenido

```
HTML, XML, JSON, CSV, texto plano  → text (default)
PDF, Excel, Word, ZIP, imágenes    → binary
Video, audio, archivos grandes     → stream
```

---

## Atributos

| Atributo   | Requerido | Default  | Descripción |
|---|---|---|---|
| `url`      | sí        | —        | URL a consultar |
| `method`   | no        | GET      | GET, POST, PUT, DELETE, PATCH, HEAD |
| `timeout`  | no        | 30000    | timeout en milisegundos |
| `response` | no        | text     | text, binary, stream |
| `path`     | solo stream | —      | ruta donde guardar el archivo |

## Child tags

| Tag | Descripción |
|---|---|
| `<httpx-header name="...">` | Agregar header HTTP |
| `<httpx-param name="...">` | Agregar parámetro (query string en GET, body en POST) |

---

## Notas importantes

- `file-download` fue eliminado — usar `httpx-call response="binary"` + `file-write encoding="binary"`
- `file-upload` fue eliminado — usar `httpx-call method="POST"` con los params necesarios
- `response="binary"` devuelve bytes — si lo pasás a un hand que espera texto puede corromperse
- `response="stream"` requiere `path` — si falta, el workflow falla con error claro
- Cada cliente futuro (playwright, scrapling) manejará sus propias descargas internamente
