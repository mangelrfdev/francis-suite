# Cursor — reglas reutilizables (plantilla)

Copia estos `.mdc` a **cualquier proyecto nuevo** en:

```
<tu-proyecto>/.cursor/rules/
```

## User Rules globales (Cursor)

En **Settings → Rules → User Rules** podés pegar texto que aplique a **todos** los repos. Un ejemplo alineado con estas plantillas (tono cálido + criterios generales) está en **[`../user-rules-cursor-example.md`](../user-rules-cursor-example.md)**. Las reglas del **proyecto** (esta carpeta) suman detalle por repo; las **User Rules** son tu capa personal.

## Instalación rápida

1. Creá la carpeta si no existe: `.cursor/rules/`
2. Copiá los archivos de esta carpeta:
   - `general-always.mdc` (incluye sección de **tono cálido**, estilo user rules)
   - `workflow-and-tools.mdc`
3. (Opcional) Renombrá o editá el `description` en el frontmatter si querés distinguir proyectos en el selector de reglas de Cursor.
4. (Opcional) Agregá **otra** regla solo para ese repo (p. ej. `my-app-conventions.mdc`) con `alwaysApply: true` y contexto del dominio.

## Qué cubre cada archivo

| Archivo | Enfoque |
|---------|---------|
| `general-always.mdc` | Idioma, honestidad técnica, calidad de código, portabilidad, secretos |
| `workflow-and-tools.mdc` | Cuándo tocar archivos, git, tests, terminal (personalizable) |

## Cursor User Rules vs Project Rules

- **User Rules** (configuración global de Cursor): ideal para lo que **nunca** cambia entre repos (tono, idioma).
- **Project Rules** (esta carpeta): ideal para lo que **sí** versionás con el equipo o clonás en cada repo.

Podés pegar el mismo contenido en ambos niveles; evitá duplicar texto enorme en los dos sitios.

## Personalizar

- Abrí cada `.mdc` y reemplazá comentarios `<!-- ... -->` o secciones marcadas **EDITAR** si tu flujo difiere (por ejemplo: si preferís que el agente ejecute tests sí o sí).
- Si un proyecto es solo frontend, podés añadir `globs` y reglas por stack en archivos nuevos (`globs: "**/*.tsx"`).
