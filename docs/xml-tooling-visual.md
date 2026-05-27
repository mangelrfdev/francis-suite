# Francis Suite — Tooling XML para VS Code (Guía Visual, solo clicks)

> **Autocompletado, IntelliSense y snippets al escribir workflows XML.**
>
> Esta guía no usa comandos de terminal. Todo se hace con clicks dentro de VS Code/Cursor.

---

## Tabla de contenidos

- [Francis Suite — Tooling XML para VS Code (Guía Visual, solo clicks)](#francis-suite--tooling-xml-para-vs-code-guía-visual-solo-clicks)
  - [Tabla de contenidos](#tabla-de-contenidos)
  - [Paso 0: Qué vas a lograr](#paso-0-qué-vas-a-lograr)
  - [Paso 1: Instalar la extensión Red Hat XML](#paso-1-instalar-la-extensión-red-hat-xml)
  - [Paso 2: Crear la carpeta .vscode](#paso-2-crear-la-carpeta-vscode)
  - [Paso 3: Copiar los 2 archivos de tooling](#paso-3-copiar-los-2-archivos-de-tooling)
  - [Paso 4: Verificar que el XSD está en su lugar](#paso-4-verificar-que-el-xsd-está-en-su-lugar)
  - [Paso 5: Recargar VS Code](#paso-5-recargar-vs-code)
  - [Paso 6: Probar el autocompletado](#paso-6-probar-el-autocompletado)
  - [Paso 7: Probar los snippets](#paso-7-probar-los-snippets)
  - [Qué pasa si no funciona (solución rápida)](#qué-pasa-si-no-funciona-solución-rápida)
  - [Mantenimiento: agregar una hand nueva (clicks)](#mantenimiento-agregar-una-hand-nueva-clicks)
  - [Mantenimiento: agregar un snippet nuevo (clicks)](#mantenimiento-agregar-un-snippet-nuevo-clicks)

---

## Paso 0: Qué vas a lograr

Cuando termines estos pasos, al abrir cualquier archivo `.xml` dentro de las carpetas `workflows/`, `examples/` o `templates/`, VS Code te va a:

- **Sugerir tags** cuando escribas `<`
- **Sugerir atributos** cuando escribas `Ctrl + Espacio` dentro de un tag
- **Mostrar errores** si escribes un atributo que no existe
- **Completar snippets** cuando escribas `fs-` y aprietes `Tab`

---

## Paso 1: Instalar la extensión Red Hat XML

1. En VS Code, mira a la **barra lateral izquierda**.
2. Haz **click** en el icono de **cuadrados** (Extensions / Extensiones). Es el último icono de la barra.
   - Si no lo ves, presiona `Ctrl + Shift + X` una sola vez.
3. En la caja de búsqueda arriba, escribe: `Red Hat XML`
4. Aparece una extensión llamada **XML** de **Red Hat**. Haz **click** en el botón azul **Install**.
5. Espera a que termine la instalación (el botón cambia a **Installed** o **Installed**).

> **¿Por qué?** Esta extensión es la única que le enseña a VS Code a leer archivos `.xsd` y autocompletar XML.

---

## Paso 2: Crear la carpeta .vscode

1. En el **Explorador de archivos** (barra lateral izquierda, icono de dos hojas de papel), haz **click derecho** en la raíz del proyecto (la carpeta `francis-suite`).
2. En el menú que aparece, selecciona **New Folder** (Nueva carpeta).
3. Escribe exactamente: `.vscode`
4. Presiona `Enter`.

> Si la carpeta ya existe, no pasa nada. Sigue al paso 3.

---

## Paso 3: Copiar los 2 archivos de tooling

Necesitas copiar 2 archivos desde `tools/vscode/` a la carpeta `.vscode/` que acabas de crear.

### Archivo 1: `settings.json`

1. En el Explorador, navega a `tools/vscode/`.
2. Haz **click derecho** sobre `settings.json`.
3. Selecciona **Copy** (Copiar).
4. Haz **click derecho** sobre la carpeta `.vscode`.
5. Selecciona **Paste** (Pegar).

### Archivo 2: `francis-suite.code-snippets`

1. En el Explorador, sigue en `tools/vscode/`.
2. Haz **click derecho** sobre `francis-suite.code-snippets`.
3. Selecciona **Copy** (Copiar).
4. Haz **click derecho** sobre la carpeta `.vscode`.
5. Selecciona **Paste** (Pegar).

Al final, tu carpeta `.vscode/` debe verse así:

```
.vscode/
  settings.json
  francis-suite.code-snippets
```

> **Nota:** No copies todo el contenido y lo pegues manualmente. Copia los archivos completos para no cometer errores de formato.

---

## Paso 4: Verificar que el XSD está en su lugar

1. En el Explorador, navega a la carpeta `schema/`.
2. Busca el archivo `francis-workflow.xsd`.
3. Si lo ves, estás listo. Si **no** lo ves, avisa: es un archivo crítico que valida tu XML.

> No necesitas abrirlo ni entenderlo. Solo confirmar que existe.

---

## Paso 5: Recargar VS Code

1. Presiona `Ctrl + Shift + P` (Paleta de comandos).
2. Escribe: `reload window`
3. Haz **click** en la opción que dice **Developer: Reload Window**.
4. VS Code se reinicia en 2 segundos.

> Esto es necesario para que VS Code lea la nueva configuración que acabas de copiar.

---

## Paso 6: Probar el autocompletado

1. Abre cualquier archivo `.xml` del proyecto, por ejemplo:
   `workflows/record_pipeline_minimal.xml`
   - Si no lo tienes, crea uno nuevo: click derecho en `workflows/` → **New File** → `test.xml`.
2. Dentro del archivo, escribe `<` (menor que).
3. Debe aparecer una lista de sugerencias con tags como `<francis-workflow>`, `<log>`, `<httpx-call>`, etc.
4. Prueba escribir `<log level="` y luego presiona `Ctrl + Espacio`.
5. Debe aparecer una lista desplegable con: `info`, `debug`, `warning`, `error`.

Si ves la lista desplegable, **¡funcionó!**

---

## Paso 7: Probar los snippets

1. Con un archivo `.xml` abierto, borra todo y escribe: `fs-workflow`
2. Presiona `Tab`.
3. Debe aparecer un esqueleto completo de `<francis-workflow>` con hijos vacíos.

Otros para probar:

| Escribe | Presiona | Resultado |
|---|---|---|
| `fs-log` | `Tab` | Tag `<log>` completo |
| `fs-sleep` | `Tab` | Tag `<sleep>` con segundos |
| `fs-httpx-get` | `Tab` | Tag `<httpx-call>` con método GET |
| `fs-xpath` | `Tab` | Tag `<xpath>` con extractor |

---

## Qué pasa si no funciona (solución rápida)

### No aparece la lista al escribir `<`

1. Mira la esquina **inferior derecha** de VS Code. Debe decir **XML**.
   - Si dice otra cosa (ej. `Plain Text`), haz **click** sobre el texto → selecciona **XML**.
2. Confirma que el archivo está dentro de `workflows/`, `examples/` o `templates/`.
   - Si está en otra carpeta, el autocompletado no se activa.
3. Recarga VS Code de nuevo: `Ctrl + Shift + P` → `reload window`.

### No aparecen los snippets

1. `Ctrl + Shift + P` → escribe `Insert Snippet` → haz click.
2. En la lista que aparece, busca algo que empiece con `fs-`.
3. Si no aparece nada con `fs-`, los snippets no se copiaron bien. Repite el **Paso 3**.

---

## Mantenimiento: agregar una hand nueva (clicks)

Supón que programaste una hand nueva y quieres que VS Code la sugiera.

### Parte A: Agregar el tag al XSD

1. En el Explorador, abre `schema/francis-workflow.xsd`.
2. Presiona `Ctrl + F` para buscar. Escribe: `HandLaxType`.
3. Verás una lista larga de `<xs:element name="..."`. Ve hasta el final de esa lista.
4. Agrega una nueva línea antes del `</xs:choice>` de cierre:

   ```xml
   <xs:element name="mi-nueva-hand" type="HandLaxType"/>
   ```

5. Guarda el archivo (`Ctrl + S`).

### Parte B: Agregar el snippet

1. En el Explorador, abre `.vscode/francis-suite.code-snippets`.
2. Ve al final del archivo (justo antes del último `}`).
3. Agrega una coma `,` después de la última entrada existente.
4. Pega esto:

   ```json
   "mi-nueva-hand — descripción": {
     "scope": "xml",
     "prefix": "fs-mi-nueva-hand",
     "description": "Qué hace esta hand",
     "body": [
       "<mi-nueva-hand attr=\"${1:valor}\">",
       "  $0",
       "</mi-nueva-hand>"
     ]
   }
   ```

5. Guarda (`Ctrl + S`).
6. Recarga VS Code: `Ctrl + Shift + P` → `reload window`.

---

## Mantenimiento: agregar un snippet nuevo (clicks)

1. Abre `.vscode/francis-suite.code-snippets`.
2. Busca cualquier snippet existente para usarlo como plantilla.
3. Copia todo el bloque JSON de ese snippet (desde la llave de apertura hasta el cierre).
4. Ve al final del archivo, agrega una coma `,` y pega tu copia.
5. Modifica:
   - El **nombre** (primera línea, entre comillas)
   - El **prefix** (lo que escribes para activarlo)
   - El **body** (el XML que se inserta)
6. Guarda y recarga VS Code.

---

> Guía visual. Si necesitas la versión técnica con comandos de terminal, vé `xml-tooling.md`.
