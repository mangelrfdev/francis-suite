# file-manage — Guía de uso

Tag para operaciones del sistema de archivos.
Soporta: delete, move, copy, rename, mkdir, check-exists, get-size, list.

---

## delete — eliminar archivo o carpeta

```xml
<!-- eliminar archivo -->
<file-manage action="delete" path="output/reporte.tmp"/>

<!-- eliminar carpeta vacía -->
<file-manage action="delete" path="output/fotos/"/>

<!-- eliminar carpeta con contenido — forzar -->
<file-manage action="delete" path="output/fotos/" force-delete="true"/>
```

Logs:
```
[FILE-MANAGE] delete: removed file 'output/reporte.tmp'
[FILE-MANAGE] delete: removed directory 'output/fotos/'
[FILE-MANAGE] delete: ERROR — directory is not empty: 'output/fotos/' — use force-delete="true" to force delete
[FILE-MANAGE] delete: ERROR — not found: 'output/reporte.tmp'
[FILE-MANAGE] delete: ERROR — permission denied: 'output/reporte.tmp'
[FILE-MANAGE] delete: ERROR — file is locked by another process: 'output/reporte.tmp'
```

---

## move — mover archivo o carpeta

```xml
<!-- mover archivo -->
<file-manage action="move" path="old/reporte.pdf" to="new/reporte.pdf"/>

<!-- mover sobreescribiendo si destino existe -->
<file-manage action="move" path="old/reporte.pdf" to="new/reporte.pdf" force-move="true"/>

<!-- mover usando variables -->
<file-manage action="move" path="${ruta_origen}" to="${ruta_destino}"/>
```

Logs:
```
[FILE-MANAGE] move: 'old/reporte.pdf' → 'new/reporte.pdf'
[FILE-MANAGE] move: ERROR — not found: 'old/reporte.pdf'
[FILE-MANAGE] move: ERROR — destination already exists: 'new/reporte.pdf' — use force-move="true" to replace
[FILE-MANAGE] move: ERROR — permission denied: 'old/reporte.pdf'
[FILE-MANAGE] move: ERROR — file is locked by another process: 'old/reporte.pdf'
[FILE-MANAGE] move: ERROR — no space left on device
```

---

## copy — copiar archivo o carpeta

```xml
<!-- copiar archivo -->
<file-manage action="copy" path="orig/foto.jpg" to="backup/foto.jpg"/>

<!-- copiar sobreescribiendo si destino existe -->
<file-manage action="copy" path="orig/foto.jpg" to="backup/foto.jpg" force-copy="true"/>

<!-- copiar carpeta completa -->
<file-manage action="copy" path="output/fotos/" to="backup/fotos/"/>
```

Logs:
```
[FILE-MANAGE] copy: 'orig/foto.jpg' → 'backup/foto.jpg'
[FILE-MANAGE] copy: ERROR — not found: 'orig/foto.jpg'
[FILE-MANAGE] copy: ERROR — destination already exists: 'backup/foto.jpg' — use force-copy="true" to replace
[FILE-MANAGE] copy: ERROR — permission denied: 'orig/foto.jpg'
[FILE-MANAGE] copy: ERROR — file is locked by another process: 'orig/foto.jpg'
[FILE-MANAGE] copy: ERROR — no space left on device
```

---

## rename — renombrar archivo o carpeta

El archivo debe quedarse en el mismo directorio.
Para mover a otro directorio usar action="move".

```xml
<!-- renombrar manteniendo extensión -->
<file-manage action="rename" path="output/foto_1.jpg" to="output/foto_001.jpg"/>

<!-- renombrar cambiando extensión — genera WARNING -->
<file-manage action="rename" path="output/reporte.tmp" to="output/reporte.pdf"/>

<!-- renombrar usando variables -->
<box-def name="nombre_nuevo">
    <compose>output/fotos/propiedad_${id}_foto_${i}.jpg</compose>
</box-def>
<file-manage action="rename" path="${foto}" to="${nombre_nuevo}"/>
```

Logs:
```
[FILE-MANAGE] rename: 'foto_1.jpg' → 'foto_001.jpg'
[FILE-MANAGE] rename: 'reporte.tmp' → 'reporte.pdf'
[FILE-MANAGE] rename: WARNING — extension changed from '.tmp' to '.pdf' — file content was not converted
[FILE-MANAGE] rename: ERROR — not found: 'output/foto_1.jpg'
[FILE-MANAGE] rename: ERROR — destination already exists: 'output/foto_001.jpg'
[FILE-MANAGE] rename: ERROR — duplicate extension detected in 'foto_001.jpg.jpg'
[FILE-MANAGE] rename: ERROR — 'to' must be in the same directory as 'path'. Use action='move' to move files.
[FILE-MANAGE] rename: ERROR — permission denied: 'output/foto_1.jpg'
[FILE-MANAGE] rename: ERROR — file is locked by another process: 'output/foto_1.jpg'
```

---

## mkdir — crear carpeta

Crea la carpeta y todos los directorios padres necesarios.
Si ya existe no hace nada y loguea.

```xml
<!-- crear carpeta -->
<file-manage action="mkdir" path="output/fotos/"/>

<!-- crear con subdirectorios -->
<file-manage action="mkdir" path="output/propiedades/santiago/fotos/"/>

<!-- crear usando variable -->
<file-manage action="mkdir" path="output/${ciudad}/fotos/"/>
```

Logs:
```
[FILE-MANAGE] mkdir: created 'output/fotos/'
[FILE-MANAGE] mkdir: 'output/fotos/' already exists, skipping
[FILE-MANAGE] mkdir: ERROR — a file with that name already exists: 'output/fotos'
[FILE-MANAGE] mkdir: ERROR — permission denied: 'output/fotos/'
[FILE-MANAGE] mkdir: ERROR — no space left on device
```

---

## check-exists — verificar si existe

Devuelve "true" o "false". Nunca falla.
Funciona para archivos y carpetas.

```xml
<!-- verificar archivo -->
<box-def name="existe">
    <file-manage action="check-exists" path="output/reporte.pdf"/>
</box-def>

<!-- usar en condición -->
<if condition="${existe.toBoolean()}">
    <log>el archivo existe, procesando</log>
</if>
<else>
    <log>el archivo no existe, generando</log>
</else>

<!-- verificar carpeta -->
<box-def name="carpeta_existe">
    <file-manage action="check-exists" path="output/fotos/"/>
</box-def>
```

Logs:
```
[FILE-MANAGE] check-exists: 'output/reporte.pdf' → true
[FILE-MANAGE] check-exists: 'output/reporte.pdf' → false
```

---

## get-size — obtener tamaño

Para archivos devuelve el tamaño del archivo.
Para carpetas devuelve el tamaño total de todo su contenido.

```xml
<!-- bytes — default -->
<box-def name="tamano">
    <file-manage action="get-size" path="output/reporte.pdf"/>
</box-def>
<log>Tamaño: ${tamano}</log>
<!-- Tamaño: 2048 bytes -->

<!-- kb -->
<box-def name="tamano">
    <file-manage action="get-size" path="output/reporte.pdf" size-format="kb"/>
</box-def>
<!-- Tamaño: 2.00 KB -->

<!-- mb -->
<box-def name="tamano">
    <file-manage action="get-size" path="output/fotos/" size-format="mb"/>
</box-def>
<!-- Tamaño: 45.20 MB -->

<!-- auto — elige la unidad más legible -->
<box-def name="tamano">
    <file-manage action="get-size" path="output/fotos/" size-format="auto"/>
</box-def>
<!-- Tamaño: 45.20 MB -->
```

Logs:
```
[FILE-MANAGE] get-size: 'output/reporte.pdf' → 2048 bytes
[FILE-MANAGE] get-size: 'output/fotos/' → 150 files, 45.20 MB total
[FILE-MANAGE] get-size: ERROR — not found: 'output/reporte.pdf'
[FILE-MANAGE] get-size: ERROR — permission denied: 'output/reporte.pdf'
```

---

## list — listar contenido

Devuelve una lista de paths.
Las carpetas en el resultado terminan con / para distinguirlas de archivos.

```xml
<!-- listar archivos — default -->
<box-def name="archivos">
    <file-manage action="list" path="output/fotos/"/>
</box-def>

<!-- listar con filtro -->
<box-def name="jpgs">
    <file-manage action="list" path="output/fotos/" filter="*.jpg"/>
</box-def>

<!-- buscar en subcarpetas también -->
<box-def name="todos_los_jpgs">
    <file-manage action="list" path="output/" filter="*.jpg" search-in-subfolders="true"/>
</box-def>

<!-- listar solo carpetas -->
<box-def name="carpetas">
    <file-manage action="list" path="output/" type="folders"/>
</box-def>

<!-- listar todo — archivos y carpetas -->
<box-def name="todo">
    <file-manage action="list" path="output/" type="all"/>
</box-def>

<!-- usar resultado en loop -->
<loop item="foto" index="i">
    <loop-list>
        <box name="jpgs"/>
    </loop-list>
    <loop-body>
        <log>Foto ${i}: ${foto}</log>
    </loop-body>
</loop>
```

Logs:
```
[FILE-MANAGE] list: found 3 files in 'output/fotos/' matching '*.jpg'
[FILE-MANAGE] list: found 2 folders in 'output/'
[FILE-MANAGE] list: found 3 files and 2 folders in 'output/'
[FILE-MANAGE] list: 'output/fotos/' exists but is empty
[FILE-MANAGE] list: no items found in 'output/fotos/' matching '*.png'
[FILE-MANAGE] list: ERROR — not found: 'output/fotos/'
[FILE-MANAGE] list: ERROR — permission denied: 'output/fotos/'
```

---

## Patrones comunes

### Preparar carpeta limpia para output:
```xml
<box-def name="existe">
    <file-manage action="check-exists" path="output/fotos/"/>
</box-def>
<if condition="${existe.toBoolean()}">
    <file-manage action="delete" path="output/fotos/" force-delete="true"/>
</if>
<file-manage action="mkdir" path="output/fotos/"/>
```

### Descargar foto y guardar con nombre limpio:
```xml
<box-def name="foto">
    <httpx-call url="${foto_url}" response="binary"/>
</box-def>
<file-write path="output/fotos/foto.tmp" encoding="binary">
    <box name="foto"/>
</file-write>
<box-def name="nombre_final">
    <compose>output/fotos/propiedad_${id}.jpg</compose>
</box-def>
<file-manage action="rename" path="output/fotos/foto.tmp" to="${nombre_final}"/>
```

### Verificar tamaño antes de procesar:
```xml
<box-def name="tamano">
    <file-manage action="get-size" path="output/video.mp4" size-format="auto"/>
</box-def>
<log>Tamaño del video: ${tamano}</log>
```

### Listar y procesar todos los archivos de una carpeta:
```xml
<box-def name="archivos">
    <file-manage action="list" path="output/fotos/" filter="*.jpg"/>
</box-def>
<loop item="foto" index="i">
    <loop-list>
        <box name="archivos"/>
    </loop-list>
    <loop-body>
        <log>Procesando foto ${i}: ${foto}</log>
    </loop-body>
</loop>
```
