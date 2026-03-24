# converts — Guía de uso

Hands de conversión de datos entre formatos.
Todos siguen el patrón `convert-[origen]-to-[destino]`.

---

## Base64

### convert-binary-to-base64

Convierte bytes a string base64. Para enviar archivos a APIs de IA u otras APIs que requieran base64.

```xml
<!-- descargar imagen y convertir a base64 -->
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<box-def name="foto_base64">
    <convert-binary-to-base64>
        <box name="foto"/>
    </convert-binary-to-base64>
</box-def>

<!-- enviar a API de IA -->
<httpx-call url="https://api.ejemplo.com/analyze" method="POST">
    <httpx-param name="image">${foto_base64}</httpx-param>
</httpx-call>
```

**Importante:** siempre descargar con `response="binary"` antes de convertir. Si se descarga con `response="text"` el archivo puede estar corrupto.

---

### convert-base64-to-binary

Convierte string base64 a bytes. Para decodificar respuestas de APIs y guardar en disco.

```xml
<!-- API devuelve imagen en base64 -->
<box-def name="imagen_base64">
    <httpx-call url="https://api.ejemplo.com/imagen"/>
</box-def>

<!-- decodificar y guardar -->
<box-def name="imagen_bytes">
    <convert-base64-to-binary>
        <box name="imagen_base64"/>
    </convert-base64-to-binary>
</box-def>
<file-write path="downloads/imagen.jpg" encoding="binary">
    <box name="imagen_bytes"/>
</file-write>
```

---

### convert-text-to-base64

Convierte texto a string base64.

```xml
<box-def name="texto_base64">
    <convert-text-to-base64>${mensaje}</convert-text-to-base64>
</box-def>
```

---

### convert-base64-to-text

Convierte string base64 a texto. Si los bytes no son UTF-8 válido, usar `convert-base64-to-binary`.

```xml
<box-def name="texto">
    <convert-base64-to-text>
        <box name="texto_base64"/>
    </convert-base64-to-text>
</box-def>
```

---

## CSV

### convert-json-to-csv

Convierte un JSON array de objetos a CSV. Aplana objetos anidados con notación punto.

```xml
<!-- desde API -->
<box-def name="data">
    <httpx-call url="https://api.ejemplo.com/propiedades"/>
</box-def>
<box-def name="csv">
    <convert-json-to-csv>
        <box name="data"/>
    </convert-json-to-csv>
</box-def>
<file-write path="output/propiedades.csv">
    <box name="csv"/>
</file-write>
```

Con delimitador personalizado:
```xml
<box-def name="csv">
    <convert-json-to-csv delimiter=";">
        <box name="data"/>
    </convert-json-to-csv>
</box-def>
```

Input JSON:
```json
[{"nombre": "Casa", "precio": 100000}, {"nombre": "Depto", "precio": 80000}]
```

Output CSV:
```
nombre,precio
Casa,100000
Depto,80000
```

---

### convert-csv-to-json

Convierte CSV a JSON array. La primera fila es el header.

```xml
<!-- leer CSV de corredora -->
<box-def name="csv">
    <file-read path="feeds/corredora.csv"/>
</box-def>
<box-def name="data">
    <convert-csv-to-json>
        <box name="csv"/>
    </convert-csv-to-json>
</box-def>
```

---

### convert-xml-to-csv

Convierte XML a CSV. Cada hijo del root es una fila. Los tags de los nietos son las columnas.

```xml
<box-def name="csv">
    <convert-xml-to-csv>
        <box name="data_xml"/>
    </convert-xml-to-csv>
</box-def>
```

Input XML:
```xml
<items>
    <item><nombre>Casa</nombre><precio>100000</precio></item>
    <item><nombre>Depto</nombre><precio>80000</precio></item>
</items>
```

Output CSV:
```
nombre,precio
Casa,100000
Depto,80000
```

---

## Texto

### convert-text-to-url

Codifica texto para uso seguro en URLs. Espacios y caracteres especiales se convierten a formato percent-encoded.

```xml
<box-def name="busqueda_url">
    <convert-text-to-url>${busqueda}</convert-text-to-url>
</box-def>
<box-def name="url">
    <compose>https://portal.cl/buscar?q=${busqueda_url}</compose>
</box-def>
```

```
"departamento en santiago"  →  "departamento%20en%20santiago"
"precio=100&tipo=casa"      →  "precio%3D100%26tipo%3Dcasa"
```

---

### convert-url-to-text

Decodifica un string URL-encoded de vuelta a texto plano.

```xml
<box-def name="ruta_limpia">
    <convert-url-to-text>
        <box name="href_extraido"/>
    </convert-url-to-text>
</box-def>
```

```
"departamento%20en%20santiago"  →  "departamento en santiago"
"/propiedad%20en%20venta"       →  "/propiedad en venta"
```

---

### convert-html-entities-to-text

Convierte entidades HTML a sus caracteres originales. Funciona en cualquier texto — no solo HTML.

```xml
<box-def name="titulo_limpio">
    <convert-html-entities-to-text>${titulo}</convert-html-entities-to-text>
</box-def>
```

```
"Casa &amp; Jardín"   →  "Casa & Jardín"
"precio &lt; 100 UF"  →  "precio < 100 UF"
"100m&sup2;"          →  "100m²"
"&nbsp;"              →  " "
```

**Nota en tests:** las entidades HTML no son válidas en XML. Para testear usar `&amp;amp;` en vez de `&amp;`:
```xml
<!-- en XML del workflow -->
<convert-html-entities-to-text>Casa &amp;amp; Jardín</convert-html-entities-to-text>
<!-- resultado: "Casa & Jardín" -->
```

---

## Patrones comunes para Estación Inmobiliaria

### Procesar feed CSV de corredora:
```xml
<box-def name="csv">
    <file-read path="feeds/corredora_xyz.csv"/>
</box-def>
<box-def name="propiedades">
    <convert-csv-to-json>
        <box name="csv"/>
    </convert-csv-to-json>
</box-def>
```

### Limpiar título de propiedad:
```xml
<box-def name="titulo_limpio">
    <convert-html-entities-to-text>${titulo_raw}</convert-html-entities-to-text>
</box-def>
```

### Construir URL de búsqueda:
```xml
<box-def name="ciudad_url">
    <convert-text-to-url>${ciudad}</convert-text-to-url>
</box-def>
<box-def name="url_busqueda">
    <compose>https://portal.cl/arriendos?ciudad=${ciudad_url}&amp;tipo=departamento</compose>
</box-def>
```

### Enviar foto a API de IA:
```xml
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<box-def name="foto_base64">
    <convert-binary-to-base64>
        <box name="foto"/>
    </convert-binary-to-base64>
</box-def>
<box-def name="analisis">
    <use-ia model="vision">
        <box name="foto_base64"/>
    </use-ia>
</box-def>
```
