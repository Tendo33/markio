# Backend Spec Index

## Current Backend

Markio uses FastAPI to expose authenticated parser APIs under `/v1`, async task APIs under `/v1/tasks/*`, health/readiness endpoints, a static Vue console mount at `/console`, and an optional MCP server.

Important modules:

- `markio/main.py`: app creation, middleware, router registration, lifecycle, `/console`, `/healthz`, `/readyz`
- `markio/routers/`: sync parser routes, task routes, and request guards
- `markio/parsers/`: format-specific parsing
- `markio/services/`: task runtime, parser registry, sync parse service, Redis task store, serialization
- `markio/settings/`: environment-driven configuration
- `markio/auth/`: JWT auth and admin role checks
- `markio/sdk/`: CLI and SDK entrypoints
- `markio/mcps/`: optional MCP integration

## Pre-Development Checklist

- Read [directory-structure.md](directory-structure.md) before moving backend modules.
- Read [http-api-when-added.md](http-api-when-added.md) before changing routes or auth.
- Read [python-package.md](python-package.md) before changing package, SDK, CLI, or parser exports.
- Read [config-logging.md](config-logging.md) before changing settings, logs, startup, or Redis.
- Read [database-when-added.md](database-when-added.md) before touching task persistence/cache behavior.
- Read [type-safety.md](type-safety.md) before schema or typing work.
- Read [testing.md](testing.md) before verification.

## Quality Check

- Route behavior, SDK/CLI docs, and tests agree.
- Parser dispatch still handles supported file extensions intentionally.
- Auth remains enforced on `/v1/*`.
- Task visibility and admin-only queue controls remain protected.
- Redis fallback behavior is preserved.
