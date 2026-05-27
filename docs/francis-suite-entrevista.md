# Francis Suite — Guía de Entrevista Técnica

> Documento para explicar con confianza qué construiste, cómo funciona, y responder preguntas difíciles en entrevistas de RPA / Python / Backend.

---

## 1. Elevator Pitch (30 segundos)

> **"Francis Suite es un framework low-code declarativo para extracción y procesamiento de datos. En vez de escribir scripts Python imperativos para cada scraper, definís workflows en XML con tags reutilizables — como `<httpx-call>`, `<xpath-extract>`, `<record-add>` — y el motor las ejecuta secuencialmente, resolviendo variables, manejando errores con retries, y exportando a CSV/Excel/Supabase. Lo construí porque cada scraper nuevo me obligaba a repetir el mismo boilerplate: HTTP, parseo, paginación, sanitización de precios, guardado. Ahora agrego un workflow nuevo en 20 minutos en vez de 4 horas."**

---

## 2. ¿Qué problema resuelve? (El "por qué")

| Antes (sin framework) | Después (con Francis Suite) |
|---|---|
| Cada scraper = script Python desde cero | Cada scraper = archivo XML declarativo |
| Repetir: HTTP, retry, parseo, paginación, CSV | Reusar: tags predefinidos, motor central |
| Precios UF/CLP se sanitizan a mano en cada script | Expresiones `${price.replace(".","").replace(",","").trim()}` en el XML |
| Errores de red crashean todo | Hand-level retry + circuit breaker + liveness watchdog |
| Output disperso: CSV acá, Excel allá, JSON en otro | Pipeline de records unificado: create → add → save (CSV/Excel/NDJSON) |

**Números que podés mencionar:**
- 66 hands registradas en el framework
- 200+ tests automatizados
- 18 regression tests sobre el motor de expresiones
- Workflows de scrapers corriendo en ~3 minutos (vs. horas de scripting manual)
- Motor de expresiones propio con method chaining y masking de variables sensibles

---

## 3. Arquitectura — cómo explicarla visualmente

**Patrón: Hexagonal / Ports & Adapters**

```
┌─────────────────────────────────────────┐
│            XML Workflow                  │  ← Declarativo, lo escribe el usuario
│   <francis-workflow>                     │
│     <httpx-call url="..."/>             │
│     <xpath-extract>...                  │
│     <record-add>...                      │
│   </francis-workflow>                   │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         FParser  →  FNode tree           │  ← Parseo XML con lxml
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         HandRegistry                     │  ← Registry pattern: @hand(tag="...")
│         │                                │
│         ▼                                │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│   │httpx-   │ │xpath-   │ │record-   │ │  ← 66 hands registradas
│   │ call    │ │extract  │ │  add     │ │
│   └────┬────┘ └────┬────┘ └────┬─────┘ │
│        │           │          │        │
│        └───────────┴──────────┘        │
│                   │                     │
│              FContext                  │  ← Variables + scopes + shared-box
│              │                         │
│         FrancisExpression              │  ← Motor ${...} con method chaining
│              │                         │
│              ▼                         │
│         FRuntime.execute()             │  ← Orquestador + liveness watchdog
└─────────────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│ Playwright│  │  httpx   │  │ Supabase │  ← Adapters externos
│ (browser) │  │ (HTTP)   │  │ (DB)     │
└─────────┘  └──────────┘  └──────────┘
```

**Claves para decir en voz alta:**
- "El core no sabe de HTTP ni de navegadores. Solo sabe de hands, nodos, y variables."
- "Los adapters se inyectan por configuración, no por código."
- "El motor de expresiones es propio: parsea `${variable.metodo(args).otroMetodo()}` con un scanner que respeta comillas y llaves anidadas."

---

## 4. Stack Tecnológico

| Capa | Tecnología | Por qué la elegí |
|---|---|---|
| Lenguaje | Python 3.11+ | Ecosistema de scraping, async, tipado moderno |
| Parseo XML | lxml | Velocidad + XPath nativo + validación XSD |
| HTTP | httpx | Async/sync, timeouts, proxy rotation, session cookies |
| Browser | Playwright | Renderizado JS, anti-bot, screenshots |
| Motor de expresiones | Custom + simpleeval | Seguridad (sandboxed eval) + method chaining propio |
| Registry | Decorador `@hand` + dict | Simple, extensible, zero magic |
| Records / Pipeline | Custom (FRecord) | Unificado: NDJSON journal + CSV + Excel + metadata |
| API / Orchestrator | FastAPI + uvicorn | Endpoints REST para ejecutar workflows remotamente |
| Persistencia | Supabase (PostgreSQL) | Metadata de ejecución, logs, estados |
| Testing | pytest + respx | 200+ tests, mocks de HTTP, regression tests |
| Validación XML | XSD enriquecido + snippets VS Code | Autocompletado en el IDE |

---

## 5. Logros destacados (para tu CV y para contar)

### 5.1 Motor de expresiones robusto
> "El motor resuelve variables `${...}` con method chaining. Detecté y fixeé 4 bugs críticos: regex greedy, coerción numérica agresiva, leaking de variables sensibles en logs, y parsing de llaves anidadas dentro de argumentos. Agregué 18 regression tests."

### 5.2 Sistema de records unificado
> "Cualquier workflow puede crear un record (`record-create`), agregarle filas (`record-add`), y exportarlo a múltiples formatos (`record-save` para CSV/Excel/NDJSON + `record-save-metadata` para JSON de metadatos). Los metadatos incluyen hostname, versión del framework, timestamp, cantidad de filas, hashes, y campos custom definidos en XML."

### 5.3 Liveness y límites operativos
> "El runtime tiene un watchdog thread que monitorea: deadline de sesión (wall-clock), silence limit (si no hay progreso en X ms aborta), y RSS memory limit (si el proceso consume más de X MB aborta). Esto evita que un scraper con memory leak deje el servidor caído."

### 5.4 Proxy rotation con probing
> "La hand `set-proxy` rota proxies desde un pool (JSON local o API), les hace un probe HTTP a una URL de test, y solo usa el proxy si el body matchea un regex o xpath esperado. Si ninguno funciona, continúa sin proxy."

### 5.5 Documentación y tooling de desarrollo
> "Generé un XSD enriquecido con tipos por atributo (enums para log levels, métodos HTTP, formatos de record) + 20 snippets de VS Code para que escribir workflows sea con autocompletado y validación en tiempo real."

---

## 6. Preguntas frecuentes de entrevista — con respuestas preparadas

### "¿Por qué XML y no YAML/JSON/TOML?"

> "Elegí XML porque: 1) lxml es extremadamente rápido para parseo y XPath, 2) permite mix de atributos y texto body (`<log level='info'>mensaje</log>`), 3) se valida contra XSD nativamente, 4) en scraping el HTML ya es XML-like, entonces el workflow y el input comparten mental model. Reconozco que es verboso; por eso agregué snippets de VS Code que reducen el boilerplate a `fs-httpx-get` + Tab."

### "¿Por qué construiste tu propio motor de expresiones en vez de usar Jinja2?"

> "Jinja2 es potente pero complejo para este caso. Necesitaba: method chaining con FrancisString (`trim()`, `replace()`, `contains()`), auto-masking de variables sensibles en logs, y parsing tolerante que no crashee el workflow entero si una variable no existe. Mi motor tiene 400 líneas, zero dependencias para el parser, y cubre el 100% de los casos reales del framework. Jinja2 hubiera sido overkill y más difícil de sandboxear."

### "¿Cómo manejás errores y retries?"

> "A tres niveles: 1) Hand-level: algunas hands como `httpx-call` tienen retry interno con backoff; 2) Session-level: si una hand falla, el runtime captura la excepción, marca la sesión como failed, persiste el journal NDJSON, y emite un evento; 3) Liveness-level: el watchdog thread aborta si hay memory leak o un hand se queda colgado por más de X segundos sin progreso."

### "¿Cómo escalás esto?"

> "Hoy corre localmente o en un contenedor Docker. La arquitectura es hexagonal: el core no depende de infraestructura. Para escalar horizontalmente, separaría el runtime en workers independientes: FastAPI recibe el workflow, lo encola (Redis/RabbitMQ), los workers ejecutan en containers efímeros, y el resultado se sube a Supabase. El estado de sesión ya está desacoplado del runtime porque `FrancisSession` es serializable."

### "¿Cómo testeás un framework que toca HTTP, archivos, y browsers?"

> "Tres capas de tests: 1) Unitarios del motor de expresiones (18 regression tests con asserts directos); 2) Mocks de HTTP con respx para probar `httpx-call` sin tocar la red; 3) Tests de integración limitados para Playwright (usan headless browser real, pero solo en CI). Las hands se registran vía `@hand`, entonces puedo inyectar una hand fake en tests sin tocar el registry de producción."

### "¿Qué harías diferente si empezaras de cero?"

> "Dos cosas: 1) El motor de expresiones lo haría con un parser formal (PEG/ANTLR) en vez de regex + scanner manual. Ya me mordió 4 veces y cada fix agrega complejidad. 2) Separaría el expression engine del contexto con una interfaz explícita (`VariableResolverPort`) para mantener la pureza hexagonal. Hoy `FrancisExpression` recibe `FContext` directamente."

### "¿Cómo asegurás que no haya data leakage de credenciales?"

> "El sistema tiene un flag `sensitive` en variables. Si una variable se define con `sensitive='true'` o su nombre contiene palabras clave (`api_key`, `token`, `password`), el método `to_display()` retorna `***` en vez del valor real. Esto afecta logs (`LogHand` usa `resolve_display`) y metadata. Fixeé un bug donde method chains (`${secret.toUpperCase()}`) filtraban el valor real porque no propagaban el flag `display`."

### "¿Cuál fue el bug más difícil de debuggear?"

> "Un bug silencioso en el motor de expresiones: `${price.replace('.', '').replace(',', '')}` retornaba el valor del primer `replace` y ignoraba el segundo. La causa era un regex greedy (`\$\{([^}]+)\}`) que consumía hasta el último `}` de la cadena entera, en vez de parsear call por call. Lo fixeé reescribiendo el parser como un scanner iterativo con balanced parenthesis parsing. Tomó horas porque no fallaba con error — simplemente daba resultado parcial sin que nadie se diera cuenta."

---

## 7. Preguntas técnicas difíciles — y cómo responder honestamente

### "¿Usás microservicios?"

> "No aún. Hoy es monolítico modular: el core, las hands, y los adapters están separados por paquetes, pero corren en un solo proceso. La arquitectura documentada es hexagonal, lo que facilita extraer un servicio cuando sea necesario. El siguiente paso sería separar el runtime en un worker independiente con FastAPI como gateway."

### "¿Tenés CI/CD?"

> "Tengo tests automatizados con pytest. CI/CD con GitHub Actions es el siguiente paso: correr tests en PR, generar el XSD desde el registry, y publicar Docker image."

### "¿Usás Docker en producción?"

> "Tengo Dockerfile y docker-compose para desarrollo. Para producción, Railway o un VPS con Docker Swarm serían la primera opción por simplicidad."

### "¿Manejás concurrencia?"

> "Hoy el runtime es single-threaded secuencial. El liveness watchdog corre en un thread daemon, pero las hands se ejecutan una por una. httpx soporta async, pero el runtime aún no orquesta workflows concurrentes. Es una limitación conocida."

### "¿Qué tan "enterprise-grade" es?"

> "Es production-ready para workloads de scraping individuales o pipelines batch. No es un SaaS multi-tenant: no tiene auth, rate limiting por usuario, ni isolation de recursos entre workflows. Para eso necesitaría: auth layer, queue con prioridad, sandbox de filesystem (chroot), y audit logging completo."

---

## 8. Demo rápido (si te piden mostrar algo)

**30 segundos de terminal:**

```bash
# Ejecutar un workflow que scrapea propiedades
uv run python -m francis_suite run examples/corredoras-con-limites/bValue-limit.xml

# Output:
# [RECORD] created 'listingsRecords' with 1 group(s)...
# [OK] Workflow 'bValue-limit' completed successfully.
# [OK] Duration: 215.67s
```

**Mostrar el XML:**
Abrir `examples/corredoras-con-limites/bValue-limit.xml`, destacar:
- `<set-proxy>` con probing
- `<httpx-call>` con paginación
- `<xpath-extract>` para precios, metros cuadrados, comuna
- `<record-add>` para cada propiedad
- `<record-save>` para CSV

**Mostrar el output:**
Abrir `output/BVALUE_PROPERTIES_*/PROPERTIES_BVALUE.CSV` y `LISTINGSRECORDS_PRIVATE_METADATA_*.JSON`.

**Mostrar un test:**
Abrir `tests/test_expression_chain.py` y ejecutar `pytest tests/test_expression_chain.py -v`.

---

## 9. Frases clave para cerrar fuerte

- **"Francis Suite demuestra que puedo diseñar abstracciones que reducen trabajo repetitivo: pasé de 4 horas por scraper a 20 minutos por workflow."**
- **"El motor de expresiones propio me obligó a pensar en parsing formal, tokenización, y edge cases — habilidades transferibles a cualquier sistema de templates o DSL."**
- **"Escribí 200+ tests porque sé que en scraping los edge cases son la regla, no la excepción: precios con UF, HTML roto, proxies caídos, timeouts."**
- **"Documenté arquitectura hexagonal, operación, deployment, y tooling porque un sistema solo es mantenible si otra persona puede entenderlo sin preguntarme."**

---

> Usá este documento como guía de estudio. No memorices frases de memoria — entendé la arquitectura y contá tu historia. La diferencia entre un junior y un senior no es la tecnología, es saber **por qué** tomaste cada decisión.
