# Markio Trellis Spec

Markio is an API-first document parsing platform. It converts documents and web content into Markdown through FastAPI sync routes, async task routes, a Python SDK/CLI, an optional MCP server, an optional Gradio UI, and a Vue console served by the backend.

This repository is not a Python template. Specs must describe the current Markio product.

## Source Order

1. `README.md`, `README.zh.md`, docs under `docs/`, and `tests/README.md`
2. `pyproject.toml`, `uv.lock`, `pytest.ini`, `compose.yaml`, `frontend/package.json`, and `frontend/pnpm-lock.yaml`
3. `markio/`, `frontend/src/`, `scripts/`, and `tests/`
4. `.trellis/spec/`

## Spec Layers

- [backend](backend/index.md): FastAPI routes, parsers, services, task runtime, SDK/CLI, settings, and tests
- [frontend](frontend/index.md): Vue console, API client, Pinia stores, routing, and static build
- [shared](shared/index.md): dependencies, docs, verification, and cross-cutting rules
- [guides](guides/index.md): implementation and review flow
- [big questions](big-question/index.md): operational boundaries that need explicit decisions

## Non-Negotiables

- Python baseline is `>=3.11`.
- Frontend package management is pnpm with `frontend/pnpm-lock.yaml`.
- Frontend is Vue 3 + Vite + Tailwind CSS 4, not React.
- Every `/v1/*` route requires JWT auth.
- Redis remains optional; in-memory runtime remains the default local mode.
