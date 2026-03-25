# ADR-004 — Diseño del hand `set-proxy` (probe, pool, rotación)

## Estado

**Diseño + implementación en código (salvo `type="db"`).** El hand **`<set-proxy>`** acepta **`client="httpx"`** y **`type`:** `local`, `manual`, `file`, `api`. **`type="db"`** no está implementado: hoy **no hay** capa genérica de “consultar una DB” en el motor (ni DSN en `francis-config` resuelto a conexión); cuando exista, se enlazará aquí.

- **Sesión (interno):** `FrancisSession` guarda el **proxy httpx elegido** y la **última `httpx.Response`** para que **`httpx-call`** use el mismo proxy sin repetirlo en cada tag y para que **`httpx-last-status`**, **`httpx-get-headers`**, **`httpx-get-cookies`** lean status/headers/cookies. Es mecanismo de motor; el contrato que ves en XML sigue siendo la lista de 3 valores de `set-proxy`.
- **`httpx-call`:** aplica proxy de sesión y registra la última respuesta (también tras **`response="stream"`** una vez obtenido `200` y antes de leer el cuerpo).
- **Retorno `set-proxy`:** siempre **`FListVariable` de 3 elementos:** (1) `"true"` o `"false"`, (2) texto del **último probe** (HTML o cuerpo tal cual), (3) XML derivado cuando el cuerpo no era XML válido (HTML pasado por lxml). **Incluso si (1) es `false`**, (2) y (3) corresponden a ese último intento — no se vacían.
- **“Limpiar proxy de sesión” si `false`:** solo significa `set_httpx_proxy_url(None)` para que **siguientes `httpx-call` no salgan por un proxy que falló el match**. No borra el retorno de la lista de 3; el usuario puede guardar esa lista en una box y ramificar con `exit` / condiciones.
- **`item` en `<box-def>` / `<shared-box-def>`:** atributo opcional **`item="N"`** (índice **1-based**). Requiere **exactamente un** hijo `<box name="lista"/>` o `<shared-box name="lista"/>` que apunte a la variable **`FListVariable`** (p. ej. resultado de `set-proxy`). Así podés hacer `siteAvailable` = ítem 1, `startHTML` = ítem 2, `startXML` = ítem 3.
- **Introspección:** implementados **`<httpx-last-status/>`**, **`<httpx-get-headers/>`** (opcional `name`), **`<httpx-get-cookies/>`** (opcional `name`). Si no hubo petición aún → `ValueError` con mensaje explícito. Cookies: vista plana `nombre → valor` en JSON; colisiones por dominio/path pueden requerir un hand futuro con más atributos.
- **Pendiente:** `type="db"`; Playwright/Scrapling.

Este ADR sigue siendo la referencia de contrato XML.

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

## Método del probe: GET por defecto

**`<set-proxy-method>`** por defecto es **`GET`** si el hijo falta o va vacío: los probes suelen ser lecturas idempotentes. Si tu URL de comprobación exige **POST** (como en tu flujo anterior), declará explícitamente `<set-proxy-method>POST</set-proxy-method>`. No es el default global de toda la web; es el default **opinado** solo para este probe.

---

## `pool-size` y `provider`

- **`pool-size`:** opcional en `<proxy-param name="pool-size">`. Si falta, el motor usa **10** como máximo de entradas tras mezclar la lista.
- **`provider`:** opcional; filtra entradas del JSON cuyo campo `provider` coincida (si el campo no existe en un ítem, ese ítem no pasa el filtro cuando `provider` está definido).

---

## Ejemplo JSON — lista de proxies (`file` / `api`)

Raíz **array** o objeto con **`proxies`** / **`items`**. Cada elemento es un objeto; **`host`** y **`port`** son obligatorios. Opcionales: **`scheme`** (default `http`), **`username`** / **`password`** (o `user` / `pass`), **`provider`** (para filtrar).

```json
[
  {
    "scheme": "http",
    "host": "proxy1.ejemplo.com",
    "port": 8080,
    "username": "user1",
    "password": "secret1",
    "provider": "datacenter-east"
  },
  {
    "scheme": "http",
    "host": "proxy2.ejemplo.com",
    "port": 3128
  }
]
```

Equivalente con envoltorio:

```json
{
  "proxies": [
    {"host": "10.0.0.1", "port": 8888, "scheme": "http"}
  ]
}
```

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

## Extensiones / futuro

- **`type="db"`** cuando exista configuración y driver de acceso a datos acordados.
- **Cookies con dominio/path** explícitos en XML si hace falta desambiguar (hoy: mapa plano por nombre en la última respuesta).
- **Playwright / Scrapling** — proxy y última respuesta por stack.

---

## Consecuencias

- El **schema XML** del plugin deberá incluir `set-proxy` y sus hijos cuando el hand exista.
- **Playwright / Scrapling** pueden necesitar variante del mismo concepto o `client` distinto con implementación separada.
- Implementación por fases es razonable: p. ej. `manual` + `file` + probe + rotación primero; `api` y `db` después, con JSON de lista unificado.

---

## Referencias

- Roadmap: [Sistema de proxy](../roadmap.md) (sección futuro).
- `httpx-call`: [guides/httpx-call.md](../guides/httpx-call.md), [ADR-002](ADR-002-http-response-formats.md).
