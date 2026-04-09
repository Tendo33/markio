# CLAUDE.md

This file gives repository-specific guidance to coding agents working in this project.

## Project Overview

Markio is an API-first document parsing platform. It converts documents and web content into Markdown through:

- FastAPI sync parse routes under `/v1/parse_*`
- FastAPI async task routes under `/v1/tasks/*`
- a Vue console served at `/console`
- local Python SDK and CLI entrypoints
- an optional Gradio UI for preview/demo-style flows

Current status:

- version `0.1.3`
- development stage: alpha
- every `/v1/*` route requires JWT auth

## Core Stack

- Python `3.11+`
- FastAPI
- Docling
- MinerU
- Vue 3 + TypeScript + Vite
- pytest
- optional Redis backend for tasks/cache

## Preferred Local Setup

```bash
uv sync
uv pip install -e .
cp .env.example .env
```

Before starting the app, set:

```bash
AUTH_JWT_SECRET=<strong-random-secret>
```

## Common Commands

### Run backend

```bash
python markio/main.py
```

### Run frontend dev server

```bash
cd frontend
npm install
npm run dev
```

### Build console assets

```bash
cd frontend
npm run build
```

The backend serves `/console` from `markio/webapp` only when those assets exist.

### Run tests

```bash
uv run pytest
uv run pytest -q
uv run pytest -m live
```

### Code quality

```bash
black markio tests
ruff check markio tests
mypy markio
```

## Architecture Notes

### Backend

- `markio/main.py` wires middleware, routes, readiness endpoints, and the `/console` mount
- `markio/routers/` exposes type-specific parse routes plus task endpoints
- `markio/parsers/` contains format-specific parse logic
- `markio/services/` contains task backends, orchestration, and runtime helpers
- `markio/settings/` defines env-driven configuration

### Frontend

- source lives in `frontend/`
- build output lives in `markio/webapp`
- same-origin API access is the default deployment model

### URL safety

The authoritative URL fetch safety logic lives in:

- `markio/parsers/url_parser.py`

When working on URL-related behavior, keep local parser mode, SDK local mode, and remote `/v1/parse_url` behavior aligned.

## Important Current Constraints

- the console is the primary browser workflow; fallback helper pages are only for missing assets
- JWT transport is still frontend token-based for now; do not silently redesign auth storage without an explicit scope change
- Redis is optional and must not become a hard requirement for default local development
- FASTA and GenBank have dedicated routes/parsers, but no first-class SDK façade or CLI subcommands yet

## Testing Guidance

- prefer direct `pytest` invocations over the legacy helper scripts in `tests/`
- if a change affects `/console`, verify both frontend build success and `tests/test_console_frontend.py`
- if a change affects URL fetching or SSRF boundaries, verify `tests/test_url_parser.py`
- if a change affects auth or task visibility, verify `tests/test_task_auth_and_idor.py`

## Documentation Expectations

If you change behavior in any of these areas, update the matching docs:

- `README.md` / `README.zh.md`
- `docs/cli_usage*.md`
- `docs/sdk_usage*.md`
- `docs/console_frontend*.md`
- `docs/REDIS_INTEGRATION.md`
- `tests/README.md`
