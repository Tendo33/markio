# Claude Project Entrypoint


## Guardrails

- Markio converts documents and web content to Markdown through FastAPI routes, async tasks, SDK/CLI, and a Vue console.
- Every `/v1/*` route requires JWT auth.
- Redis is optional and must not become mandatory for default local development.
- The Vue console is served at `/console` from `markio/webapp` after `pnpm --prefix frontend run build`.
- Keep Python on `>=3.11` and frontend package management on pnpm with `frontend/pnpm-lock.yaml`.
