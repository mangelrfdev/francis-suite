# ADR-004 — Diseño del hand `set-proxy` (probe, pool, rotación)

## Estado

**Diseño acordado (documentación).** El hand **no está implementado** en el motor a la fecha de este ADR. Cuando se implemente, este documento es la referencia de contrato XML; los detalles finos (valor de retorno en `FVariable`, cliente httpx por sesión) se cerrarán en código y tests.

---

## Contexto

Se necesita configurar proxies para extracción de forma **manual**, desde **archivo**, **API** o **base de datos**, con un **probe** HTTP contra una URL de referencia y una regla de **match** (regex y/o XPath). Si el match falla, se **rota** al siguiente proxy de la lista (patrón conocido: pool de hasta N proxies por provider, p. ej. 10 aleatorios de la pool). Si ninguno pasa, el workflow puede seguir y el autor usa una shared-box tipo `siteAvailable` + `exit` u otra convención.

Los clientes HTTP pueden divergir (**httpx** hoy; **Playwright** / **Scrapling** en el futuro). El atributo `client` delimita qué stack aplica; la compatibilidad de cada cliente se validará al implementar.

---

## Decisión

- Un hand **`<set-proxy>`** (nombre tentativo; alinear con registro `@hand`) con atributos **`client`** y **`type`**.
- **`type`:** `local` | `manual` | `file` | `api` | `db`.
- **`local`:** sin proxy upstream: las peticiones salen con la IP de la máquina (conexión directa). Solo tiene sentido el **probe** + **match** para validar disponibilidad del sitio.
- **`manual`:** host, puerto y credenciales declarados en el XML (o vía `${...}`).
- **`file`:** lista de proxies leída de un archivo (formato acordado, p. ej. JSON).
- **`api`:** lista obtenida de un endpoint HTTP (JSON acordado).
- **`db`:** lista obtenida vía configuración segura (DSN / query fuera del repo, referencia por clave en config).
- Nombres de tags y atributos en **kebab-case** y **autodescriptivos** (convención del proyecto).

---

## Reglas comunes a todos los `type`

| Qué | Obligatorio / regla |
|-----|---------------------|
| `client` | Obligatorio (p. ej. `httpx`). |
| `type` | Obligatorio. |
| `<proxy-param name="url">` | Obligatorio: URL del **probe** (petición de prueba). |
| Criterio de “hit” | **Al menos uno** de: `match-regex`, o `match-xpath` (solo existencia de nodo), o la pareja `match-xpath` + `match-expected-text`. Si no hay ninguno → **error al ejecutar**, no un `false` silencioso. |
| `<set-proxy-method>` | Opcional; valor por defecto se fija en implementación (suele ser `GET` para probes). |
| `<set-proxy-header name="...">` | Opcional (0..N); aplican al **probe**. |
| `<set-proxy-http-param name="...">` | Opcional (0..N); útil en POST / form del probe. |

### Parámetros de match (hijos típicos)

| `name` en `<proxy-param>` | Uso |
|---------------------------|-----|
| `url` | URL del probe (obligatorio). |
| `match-regex` | Si el cuerpo de la respuesta coincide con la regex → hit. |
| `match-xpath` | Si el documento parseado tiene el nodo → hit; o se combina con `match-expected-text`. |
| `match-expected-text` | Solo con `match-xpath`: el texto del nodo debe coincidir. |
| `proxy-list-url` | Solo `type="api"`: endpoint que devuelve la lista de proxies. |
| `datasource` | Solo `type="db"`: clave hacia config (no SQL en el repo). |
| `provider` | Opcional en `api` / `db`: filtro de provider. |
| `pool-size` | Opcional: tamaño máximo de la lista a traer (p. ej. 10). |

### Comportamiento de pool y rotación (objetivo)

1. Obtener lista de proxies según `type` (hasta `pool-size` entradas, p. ej. aleatorias de la pool del provider).
2. Para cada entrada, configurar el cliente y ejecutar el **probe** a `url`.
3. Evaluar **match** sobre el cuerpo (y/o árbol XML/HTML según implementación).
4. Primer **hit** → proxy elegido para el resto de la sesión (según `client`).
5. Si **ningún** proxy hace hit → resultado de fallo coherente con el contrato de retorno (ver implementación futura); el workflow puede continuar para que el usuario haga `exit` condicional.

### Formato de lista (API / archivo / DB)

Se definirá un **JSON canónico** de lista de proxies, p. ej. objetos con: `scheme`, `host`, `port`, `username`, `password` (y opcionales). Si el archivo o la respuesta no parsean → error claro (“invalid proxy list format”), no lista vacía tratada como éxito.

---

## Parámetros obligatorios y opcionales por `type`

### `type="local"`

| Elemento | Obligatorio |
|----------|-------------|
| Atributos extra en `<set-proxy>` | Ninguno. |
| `proxy-param name="url"` | Sí. |
| Al menos un criterio de match | Sí. |
| `set-proxy-method`, headers, body params | No. |

### `type="manual"`

| Elemento | Obligatorio |
|----------|-------------|
| `<proxy-host>` | Sí. |
| `<proxy-port>` | Sí. |
| `<proxy-username>` / `<proxy-password>` | Obligatorios si el upstream exige auth; opcionales si el proxy es anónimo. |
| `proxy-param name="url"` | Sí. |
| Al menos un criterio de match | Sí. |
| `set-proxy-method`, headers, body params | No. |

### `type="file"`

| Elemento | Obligatorio |
|----------|-------------|
| Atributo `proxy-list-path` (o nombre final acordado) | Sí: ruta al archivo del pool. |
| `proxy-param name="url"` | Sí. |
| Al menos un criterio de match | Sí. |
| `set-proxy-method`, headers, body params | No. |

### `type="api"`

| Elemento | Obligatorio |
|----------|-------------|
| `proxy-param name="proxy-list-url"` | Sí. |
| `proxy-param name="url"` (probe) | Sí. |
| Al menos un criterio de match | Sí. |
| `proxy-param name="provider"` | No. |
| `proxy-param name="pool-size"` | No. |
| Headers / params adicionales | Opcional (p. ej. auth para la API del pool). |

*Nota:* distinguir en implementación la petición a la **API del pool** de la petición del **probe** (URLs y credenciales distintas).

### `type="db"`

| Elemento | Obligatorio |
|----------|-------------|
| `proxy-param name="datasource"` | Sí. |
| `proxy-param name="url"` (probe) | Sí. |
| Al menos un criterio de match | Sí. |
| `proxy-param name="provider"` | No. |
| `proxy-param name="pool-size"` | No. |

---

## Ejemplos XML por tipo

Los ejemplos usan `<box-def>` como contenedor ilustrativo; el hand real puede ejecutarse dentro de cualquier contexto válido.

### `local` — sin proxy upstream

```xml
<box-def name="setProxyValues">
    <set-proxy client="httpx" type="local">
        <proxy-param name="url">https://www.ejemplo.com/status</proxy-param>
        <proxy-param name="match-regex">(?i)operativo</proxy-param>
        <set-proxy-method>GET</set-proxy-method>
        <set-proxy-header name="Accept">text/html</set-proxy-header>
    </set-proxy>
</box-def>
```

### `manual`

```xml
<box-def name="setProxyValues">
    <set-proxy client="httpx" type="manual">
        <proxy-host>proxy.proveedor.com</proxy-host>
        <proxy-port>8080</proxy-port>
        <proxy-username>usuario</proxy-username>
        <proxy-password>secreto</proxy-password>

        <proxy-param name="url">https://www.ejemplo.com/</proxy-param>
        <proxy-param name="match-xpath">//span[@id='ok']</proxy-param>
        <set-proxy-method>GET</set-proxy-method>
    </set-proxy>
</box-def>
```

### `file`

```xml
<box-def name="setProxyValues">
    <set-proxy client="httpx" type="file" proxy-list-path="config/proxies.json">
        <proxy-param name="url">https://www.ejemplo.com/ping</proxy-param>
        <proxy-param name="match-regex">200\s*OK</proxy-param>
        <set-proxy-method>POST</set-proxy-method>
        <set-proxy-http-param name="check">1</set-proxy-http-param>
        <set-proxy-header name="Content-Type">application/x-www-form-urlencoded</set-proxy-header>
    </set-proxy>
</box-def>
```

### `api`

```xml
<box-def name="setProxyValues">
    <set-proxy client="httpx" type="api">
        <proxy-param name="proxy-list-url">https://api.interno/proxies/pool</proxy-param>
        <proxy-param name="provider">datacenter-east</proxy-param>
        <proxy-param name="pool-size">10</proxy-param>

        <proxy-param name="url">https://www.ejemplo.com/</proxy-param>
        <proxy-param name="match-xpath">//meta[@name='site-available']</proxy-param>
        <proxy-param name="match-expected-text">true</proxy-param>

        <set-proxy-method>GET</set-proxy-method>
        <set-proxy-header name="Authorization">Bearer ${apiToken}</set-proxy-header>
    </set-proxy>
</box-def>
```

### `db`

```xml
<box-def name="setProxyValues">
    <set-proxy client="httpx" type="db">
        <proxy-param name="datasource">francis-config:proxy_pool_main</proxy-param>
        <proxy-param name="provider">residential-cl</proxy-param>
        <proxy-param name="pool-size">10</proxy-param>

        <proxy-param name="url">https://www.ejemplo.com/</proxy-param>
        <proxy-param name="match-regex">&lt;title&gt;Bienvenido&lt;/title&gt;</proxy-param>

        <set-proxy-method>GET</set-proxy-method>
    </set-proxy>
</box-def>
```

---

## Extensiones relacionadas (fuera del alcance inmediato de este ADR)

- **Valor de retorno:** estructura en variable (p. ej. éxito del probe, último HTML, vista XML) — definir tipo `FVariable` o múltiples shared-boxes en la implementación.
- **Indexar resultados tipo `item="1"` en `<box-def>`:** no existe en el motor hoy; requeriría cambio de contexto/parser o convención de nombres de variables.
- **Hands de introspección httpx:** último status, headers, cookies — requieren **cliente/sesión httpx compartida** en la sesión Francis y actualización tras cada `httpx-call`; mensaje claro si aún no hubo petición.
- **Cookies:** identificación por nombre; si hay ambigüedad, atributos extra (dominio / URL) según el modelo de `httpx`.

---

## Consecuencias

- El **schema XML** del plugin deberá incluir `set-proxy` y sus hijos cuando el hand exista.
- **Playwright / Scrapling** pueden necesitar variante del mismo concepto o `client` distinto con implementación separada.
- Implementación por fases es razonable: p. ej. `manual` + `file` + probe + rotación primero; `api` y `db` después, con JSON de lista unificado.

---

## Referencias

- Roadmap: [Sistema de proxy](../roadmap.md) (sección futuro).
- `httpx-call`: [guides/httpx-call.md](../guides/httpx-call.md), [ADR-002](ADR-002-http-response-formats.md).
