# Project Agent Entrypoint

This file is the cross-tool entrypoint for Markio.

## Read Order

1. Start at [.trellis/spec/README.md](.trellis/spec/README.md)
2. Use [.trellis/spec/backend/index.md](.trellis/spec/backend/index.md) before changing FastAPI, parser, task, SDK, or CLI code
3. Use [.trellis/spec/frontend/index.md](.trellis/spec/frontend/index.md) before changing the Vue console
4. Use [.trellis/spec/shared/verification.md](.trellis/spec/shared/verification.md) before claiming completion

## Working Rules

- Treat `.trellis/spec/` as the detailed source of truth for AI-assisted work.
- Markio is an API-first document parsing platform, not a generic Python/Vite template.
- Preserve JWT auth on `/v1/*` routes and owner isolation for async tasks.
- Keep Redis optional; the default local task backend remains in-memory unless explicitly configured.
- Keep the Vue console same-origin friendly and built to `markio/webapp`.
- Update Trellis specs whenever behavior, routes, parser contracts, task semantics, scripts, or verification commands change.

## Execution Style

- Read the relevant router, parser, service, schema, frontend store/API client, and tests before editing.
- Keep parser and task changes explicit and covered by existing pytest suites where possible.
- For UI work, follow the existing Vue 3 + Pinia + Tailwind 4 console patterns.
- Run targeted checks first, then the repository verification gate.
