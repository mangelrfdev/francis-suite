# Francis Suite

> Framework **low-code** en XML para **extracción y procesamiento de datos** —
> hecho en Python moderno por alguien que lleva años haciendo esto en serio, todos los días.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-150%2B%20passing-brightgreen)](tests/)
[![Status](https://img.shields.io/badge/estado-en%20desarrollo%20activo-orange)](docs/roadmap.md)

---

## Bienvenido / Bienvenida

Hola, soy **Miguel** — y Francis Suite es el toolkit de extracción de datos que siempre desee tener.

Después de cuatro años construyendo scrapers, parsers y pipelines de ingesta para clientes reales,
me topé una y otra vez con el mismo problema: **cada proyecto empieza desde cero**. Sitio nuevo, código nuevo.
PDF distinto, código nuevo. Misma lógica, otra forma. Mismos bugs, otra semana.

Entonces construí **un solo framework que lo hace todo** — de forma declarativa, en XML — y cambié el caos
de scripts ad-hoc por algo que mi equipo (y mi yo del futuro) pueda leer en 30 segundos.

Si sos **reclutador o reclutadora**: este es mi proyecto de portafolio. La cosa de la que estoy orgulloso.
Si sos **tech lead**: andá directo a *Arquitectura* — las decisiones de diseño están documentadas.
Si sos **dev**: hay un `Quick Start` más abajo. Debería andar a la primera.

---

## ¿Qué es Francis Suite?

Un **framework universal de extracción de datos** que te permite describir todo un pipeline en un único archivo XML:
hacer una llamada HTTP, parsear la respuesta, iterar resultados, validarlos, deduplicarlos y guardarlos —
a **JSON, CSV, NDJSON, XML, HTML, Excel, Parquet** (o cualquier combinación).

**No** es solo web scraping. Extrae datos desde:

- Sitios web (HTML estático o páginas renderizadas con JavaScript vía Playwright)
- APIs REST / HTTP (con cookie jars, reintentos, enmascaramiento de headers sensibles)
- Archivos locales: PDF, Excel, JSON, CSV, XML
- Imágenes (extracción asistida por IA — en el roadmap)
- Bases de datos (planificado)

**Todo fluye a través de un modelo de datos unificado llamado `boxes`** — predecible, tipado, con scoping,
y listo para componer. El mismo XML que hoy scrapea un portal inmobiliario en Chile te guarda los
resultados en Parquet mañana para análisis sin tocar una sola línea de Python.

---

## ¿Por qué XML?

Porque los workflows son **árboles de decisiones**, y XML resulta ser excelente para árboles —
con schema, con autocompletado en el editor, con validación que corre **antes** que tu código.
Y porque *cualquiera* del equipo (junior, senior, analista) puede leerlo y saber exactamente qué pasa.

```xml
<francis-workflow>
    <httpx-call url="http://books.toscrape.com" name="html"/>
    <convert-html-to-xml name="page">${html}</convert-html-to-xml>

    <loop item="libro">
        <loop-list>
            <xpath-extract expression="//article[@class='product_pod']">${page}</xpath-extract>
        </loop-list>
        <loop-body>
            <box-def name="titulo">
                <xpath-extract expression=".//h3/a/@title">${libro}</xpath-extract>
            </box-def>
            <log>Encontrado: ${titulo}</log>
        </loop-body>
    </loop>
</francis-workflow>
```

Eso es un workflow real. Corrélo. Funciona.

---

## Quick Start

Necesitás [Python 3.11+](https://www.python.org/downloads/) y [uv](https://docs.astral.sh/uv/)
(un gestor de dependencias de Python rapidísimo).

```bash
# 1. Clonar
git clone https://github.com/mangelrfdev/francis-suite
cd francis-suite

# 2. Instalar dependencias
uv sync

# 3. Correr un workflow de ejemplo
uv run francis-suite run workflows/all_books_pages.xml
```

Listo. Vas a ver al framework scrapear `books.toscrape.com`, paginar página por página
y guardar los resultados en **ocho formatos distintos** bajo `output/`.

> ¿Querés ver cómo se ve un pipeline real?
> Mirá [`workflows/properties_workflow_template.xml`](workflows/properties_workflow_template.xml) —
> una plantilla lista para producción de listings inmobiliarios con manifiestos, validación y salida estructurada.

---

## Qué podés hacer con esto

### Salida multi-formato declarada en una línea

```xml
<record-save from="listings" format="json"    path="output/data.json"/>
<record-save from="listings" format="csv"     path="output/data.csv"  clean-data="true"/>
<record-save from="listings" format="ndjson"  path="output/data.ndjson"/>
<record-save from="listings" format="excel"   path="output/data.xlsx" sheet-name="Properties"/>
<record-save from="listings" format="parquet" path="output/data.parquet"/>
```

Misma fuente, cinco formatos, cero código de pegamento. Referencia completa en
[**docs/guides/record-save.md**](docs/guides/record-save.md).

### Un lenguaje de expresiones incorporado

Inspirado en motores de templates, pensado para que se lea claro:

```xml
<if condition="${precio.toInt()} > 1000 and ${ciudad.toUpperCase()} == 'SANTIAGO'">
    <log>Listing premium en ${ciudad}</log>
</if>
```

Soporta variables, aritmética, comparaciones, operadores lógicos y métodos de string encadenables
(`isEmpty`, `trim`, `contains`, `startsWith`, `replace`, `toInt`, `toBoolean`, …).

### Records estructurados con metadata, journal y deduplicación

```xml
<record-create name="listings">
    <record-set-group name="listing" required="true">
        <record-set-field name="external_id"  type="string"  required="true"/>
        <record-set-field name="title"        type="string"/>
        <record-set-field name="price"        type="integer"/>
        <record-set-field name="currency"     type="string"/>
    </record-set-group>
    <record-key>
        <key-field name="external_id"/>
    </record-key>
</record-create>
```

Te llevás gratis:

- Validación de schema fila por fila (modos `strict` o `collect-errors`)
- Deduplicación automática por clave (con exportación aparte para los duplicados)
- Journal NDJSON append-only (en vivo, aunque el workflow explote a mitad)
- Metadata privada: cantidad de filas, % de completitud, duración, RAM, errores, OS, versión de Python, id de sesión…
- Metadata pública embebida donde el formato lo permite (JSON `_metadata`, hoja de Excel, nodo XML, …)

### Workflows reutilizables

```xml
<function-create name="fetchAndParse">
    <function-param name="url"/>
    <httpx-call url="${url}" name="html"/>
    <function-return>
        <convert-html-to-xml>${html}</convert-html-to-xml>
    </function-return>
</function-create>

<function-call name="fetchAndParse">
    <function-param name="url">https://example.com</function-param>
</function-call>
```

### Listo para producción desde el día uno

- **Imagen Docker** sin ejemplos ni secretos quemados adentro. Tus workflows se montan desde el host.
- **Parámetros por CLI**: `--param url=… --param token=…`.
- **Variables sensibles** enmascaradas automáticamente en logs (`api_key`, `token`, `password`, etc.).
- **Autocompletado en el editor**: `francis-suite schema` genera un XSD para enchufar en VS Code / Cursor.
- **Escrituras atómicas** en cada formato (no más CSVs cortados a medias después de un crash).
- **150+ tests** que cubren el pipeline completo.

---

## Arquitectura en 30 segundos

```
workflow.xml
   │
   ▼
FParser ──► árbol de FNodes (AST universal, desacoplado del XML)
   │
   ▼
FRuntime ──► ejecuta cada Hand
                  │
                  ▼
                Hand.execute() ──► FVariable
                                       │
                                       ▼
                                  FContext (boxes, scopes)
                                       │
                                       ▼
                                  EventBus (inicio, fin, error)
```

**Idea central:** *el motor no sabe que está leyendo XML*. El parser de XML construye un árbol de
`FNode`. Todo lo demás — runtime, hands, expresiones, eventos — trabaja sobre ese árbol.
Si algún día queremos YAML, JSON, un editor visual o un builder gráfico, es solo un parser nuevo.

Diseño completo en [**docs/architecture.md**](docs/architecture.md).

---

## Stack técnico

| Capa | Qué uso | Por qué |
|------|---------|---------|
| **Lenguaje** | Python 3.11+ | Typing moderno, performance, ecosistema |
| **XML** | lxml | Rápido, robusto, XPath completo |
| **HTTP** | httpx | Listo para async, API moderna, mocks fáciles con respx |
| **Browser** | Playwright | Cuando los sitios necesitan JavaScript |
| **Extracción inteligente** | Scrapling | Resiliente a cambios de layout |
| **Expresiones** | simpleeval | Evaluación segura, sin `eval()` por ningún lado |
| **Exportación** | openpyxl, pyarrow | Excel y Parquet, soporte nativo |
| **Métricas** | psutil | RAM, procesos, info de OS para metadata privada |
| **Packaging** | uv | Instalaciones rápidas, lockfiles reproducibles |
| **Tests** | pytest, respx | 150+ tests, HTTP mockeado end-to-end |
| **Linting** | ruff | Una sola herramienta, rápida |

Lista completa en [`pyproject.toml`](pyproject.toml).

---

## CLI

```bash
# Correr un workflow
francis-suite run workflow.xml

# Inyectar parámetros
francis-suite run workflow.xml --param ciudad=santiago --param paginas=10

# Regenerar el schema XSD (para autocompletado del editor)
francis-suite schema --out schema

# Ayuda / versión
francis-suite --help
francis-suite --version
```

---

## Docker

La imagen lleva **solo** el framework. Tus workflows se quedan en el host:

```bash
docker build -t francis-suite:local .
docker compose run --rm francis
```

La salida aparece en `./docker-output/`. Mirá [`workflows/README.md`](workflows/README.md) para
cómo montar workflows desde cualquier carpeta de tu sistema.

---

## Documentación

El repo viene con **documentación cuidada y con opinión** — no es un volcado de código sin contexto.

| Documento | Qué contiene |
|-----------|--------------|
| [`docs/README.md`](docs/README.md) | Índice de toda la documentación |
| [`docs/architecture.md`](docs/architecture.md) | Capas, FNode, hands, reglas de scoping, modelo mental completo |
| [`docs/roadmap.md`](docs/roadmap.md) | Qué está hecho, qué viene, qué quedó intencionalmente fuera |
| [`docs/guides/record-save.md`](docs/guides/record-save.md) | Sistema de exportación: formatos, metadata, `clean-data`, `allow-nested`, `allow-prefix` |
| [`docs/guides/httpx-call.md`](docs/guides/httpx-call.md) | HTTP en detalle: cookies, reintentos, headers sensibles |
| [`docs/guides/run-output-and-integration.md`](docs/guides/run-output-and-integration.md) | Qué produce el motor vs. el workflow; patrones de integración |
| [`docs/guides/workflow-schema.md`](docs/guides/workflow-schema.md) | Setup de editor (VS Code / Cursor), generación de XSD, validación |
| [`docs/decisions/`](docs/decisions/) | Architecture Decision Records — el *por qué* de las decisiones grandes |

---

## Estado

**En desarrollo activo.** El framework core está completo y testeado. El sistema de plugins
(`hands/ext/`) y formatos adicionales están en el roadmap. Hoy se usa en proyectos reales
(ingesta de listings inmobiliarios en Chile).

Ver [**docs/roadmap.md**](docs/roadmap.md) para la foto completa.

---

## Desarrollo

```bash
uv sync --extra dev
uv run pytest          # 150+ tests
uv run pytest -x       # se detiene en la primera falla
uv run ruff check .    # lint
```

---

## Una nota sobre este proyecto

Estoy construyendo Francis Suite en público — en parte porque amo el problema,
en parte porque estoy buscando activamente **trabajo donde la extracción, scraping, automatización o pipelines**
sean el core (o una parte grande). Si estás contratando para eso, me encantaría conversar.

Cada commit, cada doc, cada decisión: feliz de caminarte por todo en una llamada
(virtual o no). Escribime por el perfil de GitHub de arriba — o abrí un issue, lo que te quede más cómodo.

Gracias por pasar por acá. Espero que encuentres algo útil.

— Miguel

---

## Licencia

MIT. Usalo, forkealo, aprendé de él, construí algo con él.
Si terminás haciendo algo cool con Francis Suite, me encantaría saberlo.
