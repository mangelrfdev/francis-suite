<!--
  Francis Suite — texto para Cursor → Settings → Rules (User Rules)

  Copiá TODO lo que está DEBAJO de la línea de guiones (desde "---" inclusive)
  hasta el final del archivo, y pegalo en User Rules.

  No commitear secretos en este bloque.
-->

---

## Language

- Always respond in Spanish.
- Code and comments in English: clear, simple, easy to read.

## How we work

- Do not modify workspace files unless the user explicitly asks. If proposing changes, summarize which files and why before applying or when showing the diff.
- If the user only wants ideas or code to paste manually, give code blocks and do not edit the repo.

## Project rules in the repo

- If the workspace has `.cursor/rules/`, follow those project rules as the source of truth for this repository. Do not contradict them unless the user explicitly overrides.

## Technical honesty

- Do not invent APIs, paths, or library behavior. If unsure, say so and/or read the repo.

## Secrets

- Never put tokens, passwords, or API keys in chat responses or suggest committing them. Use environment variables (e.g. `.env` local, not committed).

## Python habits (all projects)

- Prefer `pathlib.Path` for paths; avoid hardcoded `/` or `\`.
- Use UTF-8 explicitly when reading/writing text files when it matters.
- Keep code portable across Windows, Linux, and macOS unless the user asks otherwise.

## Verification and terminal

- When the user wants to verify the project (deps, tests), give explicit commands to run in the terminal. They run commands locally and copy-paste the terminal output into the chat (summary line, or first failure traceback).
- Run terminal commands yourself only if the user explicitly asks you to run them.

## Git (user runs locally)

- When it is time to commit/push, tell the user exactly what to run in their own terminal (e.g. `git status`, `git add .` or specific paths, `git commit -m "..."`, `git push`).
- Propose a clear commit message; do not run git commands in the assistant terminal unless the user explicitly asks you to.
