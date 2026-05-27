# Francis Suite — Tooling XML para VS Code

> **Autocompletado, IntelliSense y snippets al escribir workflows XML.**

Este documento explica cómo instalar, configurar y **mantener** las piezas de tooling que hacen que VS Code entienda los workflows de Francis Suite.

---

## Tabla de contenidos

- [Francis Suite — Tooling XML para VS Code](#francis-suite--tooling-xml-para-vs-code)
  - [Tabla de contenidos](#tabla-de-contenidos)
  - [1. Qué incluye este tooling](#1-qué-incluye-este-tooling)
  - [2. Instalación paso a paso](#2-instalación-paso-a-paso)
    - [Paso 1 — Instalar la extensión Red Hat XML](#paso-1--instalar-la-extensión-red-hat-xml)
    - [Paso 2 — Copiar la config y los snippets](#paso-2--copiar-la-config-y-los-snippets)
    - [Paso 3 — Verificar que el XSD existe](#paso-3--verificar-que-el-xsd-existe)
    - [Paso 4 — Probar el autocompletado](#paso-4--probar-el-autocompletado)
  - [3. Cómo usar los snippets](#3-cómo-usar-los-snippets)
  - [4. Cómo mantenerlo al evolucionar Francis Suite](#4-cómo-mantenerlo-al-evolucionar-francis-suite)
    - [Escenario A — Agregar una hand nueva](#escenario-a--agregar-una-hand-nueva)
    - [Escenario B — Agregar atributos a una hand existente](#escenario-b--agregar-atributos-a-una-hand-existente)
    - [Escenario C — Renombrar o quitar una hand](#escenario-c--renombrar-o-quitar-una-hand)
    - [Escenario D — Agregar un snippet nuevo](#escenario-d--agregar-un-snippet-nuevo)
  - [5. Relación con `francis-suite schema`](#5-relación-con-francis-suite-schema)
  - [6. Troubleshooting](#6-troubleshooting)
  - [7. Ideas futuras](#7-ideas-futuras)

---

## 1. Qué incluye este tooling

| Archivo | Ubicación | Propósito |
|---|---|---|
| `francis-workflow.xsd` | `schema/` | XSD enriquecido: valida estructura y atributos |
| `francis-workflow.schema.json` | `schema/` | Manifiesto de tags (auto-generado) |
| `settings.json` | `tools/vscode/` → copiar a `.vscode/` | Asocia el XSD a los workflows |
| `francis-suite.code-snippets` | `tools/vscode/` → copiar a `.vscode/` | Snippets para escritura rápida |

La carpeta `tools/vscode/` existe porque `.vscode/` está en `.gitignore`. Copias los archivos a tu `.vscode/` local después de clonar.

---

## 2. Instalación paso a paso

### Paso 1 — Instalar la extensión Red Hat XML

1. Abre VS Code.
2. `Ctrl + Shift + X` → busca **XML** de **Red Hat**.
3. Instala (ID: `redhat.vscode-xml`).

Esta extensión es la que realmente valida XML contra XSD y ofrece IntelliSense.

### Paso 2 — Copiar la config y los snippets

Desde la raíz del repo, ejecuta en PowerShell:

```powershell
# Crear .vscode si no existe
New-Item -ItemType Directory -Force -Path .vscode | Out-Null

# Copiar settings y snippets
Copy-Item tools/vscode/settings.json .vscode/settings.json
Copy-Item tools/vscode/francis-suite.code-snippets .vscode/francis-suite.code-snippets
```

O en bash/WSL:

```bash
mkdir -p .vscode
cp tools/vscode/settings.json .vscode/settings.json
cp tools/vscode/francis-suite.code-snippets .vscode/francis-suite.code-snippets
```

### Paso 3 — Verificar que el XSD existe

```powershell
Test-Path schema/francis-workflow.xsd
```

Debe imprimir `True`. Si no existe, genéralo:

```bash
francis-suite schema --out schema
```

(Esto escribe la versión **básica**. Si ya tienes la **enriquecida** en el repo, no lo corras — te sobrescribiría el XSD curado. Ver sección 5.)

### Paso 4 — Probar el autocompletado

1. Abre cualquier workflow, por ejemplo `workflows/record_pipeline_minimal.xml`.
2. Recarga la ventana: `Ctrl + Shift + P` → **Reload Window**.
3. Dentro de `<francis-workflow>`, escribe `<` y debería aparecer la lista de tags válidos.
4. Al escribir `<httpx-call ` y presionar `Ctrl + Space`, aparecen los atributos (`url`, `method`, `timeout`, etc).
5. En `<log level="` aparece la lista desplegable: `info`, `debug`, `warning`, `error`.

Si nada de esto pasa, revisa **Troubleshooting** al final.

---

## 3. Cómo usar los snippets

Con un archivo `.xml` abierto, escribe el prefijo y presiona `Tab`:

| Prefijo | Inserta |
|---|---|
| `fs-workflow` | Esqueleto `<francis-workflow>` completo |
| `fs-skeleton-scraper` | Workflow scraper completo (HTTP + XPath + record-save) |
| `fs-box-def` | `<box-def name="..">..</box-def>` |
| `fs-box` | `<box name=".."/>` |
| `fs-log` / `fs-log-level` | `<log>` con o sin nivel |
| `fs-sleep` / `fs-sleep-random` | Sleep fijo o gaussiano |
| `fs-if` | Bloque `<if>` + `<else>` |
| `fs-loop` | Loop con `loop-list` y `loop-body` |
| `fs-while` | While con `max-iterations` |
| `fs-try` | Try/catch |
| `fs-httpx-get` / `fs-httpx-full` | HTTP request |
| `fs-xpath` | XPath extract |
| `fs-regex` | Bloque regex completo |
| `fs-record-create` / `fs-record-add` / `fs-record-save` | Pipeline de record |
| `fs-function-create` / `fs-function-call` | Funciones |
| `fs-call-workflow` | Sub-workflow |

Lista completa: `Ctrl + Shift + P` → **Insert Snippet** → buscar `fs-`.

---

## 4. Cómo mantenerlo al evolucionar Francis Suite

Cuando agregues/cambies hands en el framework, actualiza el tooling siguiendo estos escenarios.

### Escenario A — Agregar una hand nueva

Supón que creaste `francis_suite/hands/core/my_hand.py` con `@hand(tag="my-hand")`.

**1. Regenera la lista base de tags:**

```bash
francis-suite schema --out schema
```

Esto actualiza `schema/francis-workflow.schema.json` y escribe un XSD **básico**.

> ⚠ Si tienes el **XSD enriquecido** (con atributos por hand), el comando anterior te lo sobrescribirá con la versión básica. Ver sección 5 para la estrategia recomendada.

**2. Agrega la entrada al XSD enriquecido** en `schema/francis-workflow.xsd`, dentro del `<xs:choice>` del root:

```xml
<xs:element name="my-hand" type="HandLaxType"/>
```

Si tu hand tiene atributos conocidos, define un tipo específico:

```xml
<!-- Al final del XSD, junto a los otros complexType -->
<xs:complexType name="MyHandType" mixed="true">
  <xs:sequence>
    <xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
  </xs:sequence>
  <xs:attribute name="required-attr" type="xs:string" use="required"/>
  <xs:attribute name="optional-attr" type="xs:string"/>
</xs:complexType>
```

Y referencia el tipo en el root:

```xml
<xs:element name="my-hand" type="MyHandType"/>
```

**3. Agrega un snippet** en `tools/vscode/francis-suite.code-snippets`:

```json
"my-hand — descripción": {
  "scope": "xml",
  "prefix": "fs-my-hand",
  "description": "Qué hace esta hand",
  "body": [
    "<my-hand required-attr=\"${1:value}\">",
    "  $0",
    "</my-hand>"
  ]
}
```

**4. Recarga VS Code**: `Ctrl + Shift + P` → **Reload Window**.

### Escenario B — Agregar atributos a una hand existente

1. Edita el `complexType` correspondiente en `schema/francis-workflow.xsd`.
2. Agrega el `<xs:attribute>` nuevo:
   ```xml
   <xs:attribute name="new-attr" type="xs:string"/>
   ```
3. Si el atributo acepta valores fijos, crea un `simpleType` o usa uno existente (ej. `BoolStringType`, `LogLevelType`).
4. Recarga VS Code.

### Escenario C — Renombrar o quitar una hand

1. Quita/renombra el `<xs:element name="...">` del root.
2. Quita el `complexType` asociado si era específico.
3. Quita el snippet en `francis-suite.code-snippets`.
4. Regenera el manifest: `francis-suite schema --out schema`.

### Escenario D — Agregar un snippet nuevo

Edita `tools/vscode/francis-suite.code-snippets` y agrega una entrada nueva. Sintaxis:

```json
"Nombre humano del snippet": {
  "scope": "xml",
  "prefix": "fs-algo",
  "description": "Qué hace",
  "body": [
    "<linea-1>",
    "  $1",
    "</linea-1>",
    "$0"
  ]
}
```

- `$1`, `$2` → tab stops
- `${1:default}` → tab stop con valor por defecto
- `${1|opt1,opt2,opt3|}` → dropdown
- `$0` → posición final del cursor

Guarda y recarga VS Code.

---

## 5. Relación con `francis-suite schema`

El repo tiene **dos fuentes de verdad** posibles para el XSD:

| Fuente | Qué produce | Ventaja | Desventaja |
|---|---|---|---|
| `francis-suite schema` | XSD básico (tags + `lax`) | Auto-generado, siempre al día con el registry | Sin atributos específicos |
| XSD curado en git | XSD enriquecido (tags + atributos + enums) | Autocompletado granular | Hay que mantenerlo a mano |

### Estrategia recomendada

- **Mantén el XSD enriquecido** en `schema/francis-workflow.xsd` **en git**.
- **No corras `francis-suite schema --out schema`** directamente en esa ruta, o te sobrescribirá el trabajo curado.
- Usa el comando para verificar la lista actual de tags y **compararla** con lo que hay en tu XSD:

```bash
francis-suite schema --out /tmp/fs-schema
diff /tmp/fs-schema/francis-workflow.schema.json schema/francis-workflow.schema.json
```

- Si aparece un tag nuevo en el manifest, agrégalo al XSD enriquecido siguiendo el **Escenario A**.

### Alternativa avanzada (futuro)

Puedes extender `francis_suite/schema_gen.py` para que genere directamente el XSD enriquecido leyendo un diccionario declarativo de atributos por hand. Plan sugerido:

1. Crea `francis_suite/schema_attributes.py` con:
   ```python
   HAND_ATTRIBUTES = {
       "log": {"level": {"enum": ["info", "debug", "warning", "error"]}},
       "httpx-call": {"url": {"required": True}, "method": {"enum": [...]}, ...},
       ...
   }
   ```
2. Modifica `build_xsd()` en `schema_gen.py` para consultar ese dict y emitir `complexType` específicos.
3. A partir de ahí, `francis-suite schema` produce directamente la versión enriquecida.

Ese refactor convierte el mantenimiento manual en mantenimiento declarativo.

---

## 6. Troubleshooting

### No aparece autocompletado

- **Verifica** que la extensión `redhat.vscode-xml` está instalada y habilitada.
- **Revisa** que `.vscode/settings.json` existe y tiene el bloque `xml.fileAssociations`.
- **Confirma** que el archivo abierto hace match con alguno de los patterns (`workflows/**`, `examples/**`, `templates/**`).
- Si tu workflow está en otra carpeta, agrégala al pattern.
- **Recarga** la ventana: `Ctrl + Shift + P` → **Reload Window**.

### El XSD no se encuentra

- Confirma que `schema/francis-workflow.xsd` existe.
- La ruta en `settings.json` es **relativa** a la raíz del workspace.

### El autocompletado sí anda, pero algunos tags no aparecen

- Son hands que están en el registry pero no en el `<xs:choice>` del root.
- Ejecuta `francis-suite schema --out /tmp/fs-schema` y compara con el XSD para ver qué falta.

### Los snippets no aparecen

- Confirma que `.vscode/francis-suite.code-snippets` existe.
- El `"scope": "xml"` debe coincidir con el language mode del archivo. Mira la esquina inferior derecha de VS Code: debe decir **XML**.
- `Ctrl + Shift + P` → **Insert Snippet** → busca `fs-` para verificar que se cargaron.

### El XSD muestra errores rojos en archivos válidos

- Puede faltar un tag nuevo en el root.
- Temporalmente puedes hacer el XSD más laxo reemplazando el tipo por `HandLaxType`.
- Reporta el tag faltante como issue y actualiza el XSD.

---

## 7. Ideas futuras

- **Generación automática enriquecida** desde docstrings de cada hand (extraer `Attributes:` con regex y emitir XSD).
- **LSP propio** para Francis Suite (diagnósticos semánticos: detectar `<box name="x"/>` cuando `x` no fue definido).
- **Task de VS Code** para ejecutar el workflow actual con un atajo.
- **Linter** que valide convenciones (sección `Usage in XML:` en cada docstring, nombres de tags en kebab-case, etc).
- **Snippets contextuales** que solo aparezcan dentro del padre correcto (p. ej. `sleep-min` solo dentro de `<sleep>`).

---

> Documento vivo. Actualízalo cada vez que cambie el tooling o aparezca una tecnología de soporte nueva (LSP, linter, etc).
