# Verification

## General Checks

```bash
git status --short --branch
rg -n "ai_docs|START_HERE|sync_ai_adapters|check_ai_docs" . \
  -g "!node_modules" -g "!.git" -g "!frontend/node_modules" -g "!dist" -g "!build" -g "!markio/webapp"
git diff --check
```

## Quality Gate

```bash
uv sync
uv run pytest
pnpm --prefix frontend install --frozen-lockfile
pnpm --prefix frontend run build
AUTH_JWT_SECRET=dev-secret REDIS_PASSWORD=dev-redis-password docker compose config
```

## Optional Focused Checks

```bash
uv run pytest tests/test_task_auth_and_idor.py
uv run pytest tests/test_parser_registry_dispatch.py
uv run pytest tests/test_console_frontend.py
uv run pytest tests/test_url_parser.py
```

Use `uv run pytest -m live` only when a running external Markio service is intentionally part of the task.
