# Para Cursor — reglas y tono (proyecto sitio web)

Copiá este bloque en **Cursor → Settings → Rules → User Rules** o creá **`.cursor/rules/proyecto-estacion.mdc`** con `alwaysApply: true` y el contenido de abajo (sin los títulos markdown si preferís texto plano).

---

## Tono

- Responder en **español**. Código y comentarios en **inglés**.
- Trato **cálido y claro**, sin cursilería ni emojis forzados.
- Prosa legible; evitar relleno y negritas decorativas.

## Portafolio (repo público)

- El código se verá en **Git**: debe verse **humano y profesional**, no como tutorial genérico ni con “olor a IA”.
- Comentarios **solo donde aporten** (decisiones no triviales). Nada de explicar lo obvio ni docstrings vacíos en cadena.
- Nombres y estructura claros valen más que comentar cada línea.

## Trabajo

- Cambios **mínimos** al pedido; respetar estilo del repo.
- No inventar APIs de Supabase o Next: revisar el código del proyecto o la doc.
- **Git:** indicar comandos para que el usuario los ejecute, salvo que pida lo contrario.
- **Secretos:** solo variables de entorno; nunca en el código versionado.

## Alcance de este repo

- Este proyecto es el **sitio + admin + esquema DB + ingesta** según `01-ESPECIFICACION-SITIO-INGESTA-ADMIN.md`.
- **Francis Suite** vive en otro repo: aquí solo se **consume** el contrato de datos y se **muestra** el historial de corridas.
