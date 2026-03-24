# sensitive — Variables sensibles

Sistema de protección automática para valores sensibles.
Aplica a `box-def` y `shared-box-def`.

---

## ¿Cómo funciona?

Las variables sensibles tienen dos valores:
- `to_string()` — valor real, usado internamente por el engine
- `to_display()` — valor maskeado, usado por logs y UI

El engine siempre trabaja con el valor real internamente.
Los logs y el Plugin VSCode siempre muestran el valor maskeado.

---

## Detección automática por nombre

Si el nombre de la variable contiene alguna de estas palabras,
se marca automáticamente como sensible sin que el usuario haga nada:

```
api_key, apikey, token, password, passwd,
secret, credential, auth, private_key, access_key
```

```xml
<!-- automático — detectado por nombre -->
<box-def name="api_key">sk-abc123xyz</box-def>
<shared-box-def name="my_token">abc123secreto</shared-box-def>
<shared-box-def name="openai_api_key">sk-proj-xyz</shared-box-def>
```

Logs:
```
[INFO]    api_key = *******xyz
[INFO]    my_token = *******eto
[INFO]    openai_api_key = *******xyz
```

---

## Explícito — sensitive="true"

Para variables cuyo nombre no es obvio pero el valor es sensible.

```xml
<box-def name="codigo_cliente" sensitive="true">abc123</box-def>
<shared-box-def name="clave_jumbo" sensitive="true">secreto123</shared-box-def>
```

---

## Forzar no-sensible — sensitive="false"

Para variables cuyo nombre contiene una palabra sensible
pero el valor NO es sensible.

```xml
<!-- "token_count" contiene "token" — pero es solo un contador -->
<box-def name="token_count" sensitive="false">100</box-def>

<!-- "auth_level" contiene "auth" — pero es solo un nivel -->
<shared-box-def name="auth_level" sensitive="false">admin</shared-box-def>
```

---

## Formato del masking

```
Valor con más de 4 caracteres  → 7 asteriscos + últimos 3 chars
Valor con 4 o menos caracteres → 10 asteriscos (longitud nunca revelada)
```

Ejemplos:
```
"sk-abc123xyz"   → "*******xyz"
"secreto"        → "*******eto"
"mi_password"    → "*******ord"
"ab"             → "**********"
"abcd"           → "**********"
"abcde"          → "*******cde"
```

---

## Uso con --param en CLI

Las variables inyectadas con `--param` no se muestran en logs.
Si la variable tiene nombre sensible, igual se maskea si aparece en un `<log>`.

```bash
francis-suite run scraper.xml --param api_key=sk-abc123xyz
```

Output:
```
[PARAMS] Context variables loaded.
```

El valor nunca aparece en el output del CLI.

---

## Hand `workflow-param` con from-env (opcional / futuro)

Si algún día se implementa el hand en XML, podría verse así (hoy no existe en el motor):

```xml
<workflow-param name="api_key" from-env="OPENAI_API_KEY"/>
```

Hoy la key suele venir de `--param` o de inyección en código. La idea sería la misma: valor desde el sistema operativo — nunca hardcodeada en git — y masking en logs por el nombre `api_key`.

---

## Regla de desarrollo

Nunca usar `resolve_body_text()` en contextos de display.
Usar `resolve_body_text_display()` o `engine.resolve_display()` en su lugar.

```python
# MAL — muestra valor real en logs
message = self.resolve_body_text()
print(message)

# BIEN — maskea automáticamente si hay variables sensibles
message = self.resolve_body_text_display()
print(message)
```

---

## Notas importantes

- El engine internamente siempre usa `to_string()` — el valor real nunca se altera
- Solo los logs y el Plugin VSCode usan `to_display()` — el valor maskeado
- El masking no revela la longitud real del valor — siempre 7* fijos
- `sensitive` aplica a `box-def` y `shared-box-def` — no a otras hands
- En el Plugin VSCode el inspector mostrará el valor maskeado — el desarrollador lo ve sin confirmación adicional
