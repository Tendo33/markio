# Claude Project Entrypoint

Use Trellis as the working memory for this repository:

1. Read [.trellis/spec/README.md](.trellis/spec/README.md)
2. Read [.trellis/spec/backend/index.md](.trellis/spec/backend/index.md) for API, parser, task, SDK, and CLI changes
3. Read [.trellis/spec/frontend/index.md](.trellis/spec/frontend/index.md) for Vue console changes
4. Read [.trellis/spec/shared/verification.md](.trellis/spec/shared/verification.md)

Keep this file thin. Long architecture, API, parser, frontend, and verification facts belong in `.trellis/spec/`.

## Guardrails

- Markio converts documents and web content to Markdown through FastAPI routes, async tasks, SDK/CLI, and a Vue console.
- Every `/v1/*` route requires JWT auth.
- Redis is optional and must not become mandatory for default local development.
- The Vue console is served at `/console` from `markio/webapp` after `npm --prefix frontend run build`.
- Keep Python on `>=3.11` and frontend package management on npm with `frontend/package-lock.json`.
