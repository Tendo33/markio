# Project Agent Entrypoint

This file is the cross-tool entrypoint for Markio.

## Working Rules

- Markio is an API-first document parsing platform, not a generic Python/Vite template.
- Preserve JWT auth on `/v1/*` routes and owner isolation for async tasks.
- Keep Redis optional; the default local task backend remains in-memory unless explicitly configured.
- Keep the Vue console same-origin friendly and built to `markio/webapp`.

## Execution Style

- Read the relevant router, parser, service, schema, frontend store/API client, and tests before editing.
- Keep parser and task changes explicit and covered by existing pytest suites where possible.
- For UI work, follow the existing Vue 3 + Pinia + Tailwind 4 console patterns.
- Run targeted checks first, then the repository verification gate.
