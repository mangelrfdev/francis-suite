# Plantillas para Claude (web / app)

Dos archivos complementarios:

| Archivo | Dónde va | Qué es |
|---------|----------|--------|
| [`custom-instructions.md`](custom-instructions.md) | **Instrucciones personalizadas** de tu cuenta o de un **Proyecto** en Claude | Reglas estables: cómo responder, cómo trabajar, idioma, seguridad. Copiá **todo** el contenido (sin el título del README). |
| [`contexto-inicial-chat-PLANTILLA.md`](contexto-inicial-chat-PLANTILLA.md) | **Primer mensaje** de un chat nuevo (o “Project knowledge” / nota fija del proyecto) | Contexto del repo, objetivo del día, stack. Completá los `[...]` y pegá al abrir conversación. |

## Cómo usarlo en la práctica

1. **Instrucciones:** en Claude → *Settings* → *Custom instructions* (o en un **Project**, *Project instructions*). Pegá el texto de `custom-instructions.md`. Son reglas que aplican a muchas conversaciones.
2. **Contexto de chat nuevo:** al crear un chat, pegá **después** el bloque ya rellenado de `contexto-inicial-chat-PLANTILLA.md` (o un resumen corto si ya cargaste el proyecto con archivos).

Si Claude tiene límite de caracteres en instrucciones, podés acortar `custom-instructions.md` quitando secciones que no uses.

## Nota

Estas plantillas están alineadas en espíritu con [`../cursor-reusable-rules/`](../cursor-reusable-rules/README.md), pero en formato **copiar/pegar** para Claude, no como `.mdc` de Cursor.

El archivo `custom-instructions.md` incluye **tono cálido y cercano** (equivalente a lo que en Cursor serían **User Rules** globales). Para Cursor global, ver también [`../user-rules-cursor-example.md`](../user-rules-cursor-example.md).
