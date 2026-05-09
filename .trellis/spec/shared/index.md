# Shared Spec Index

## Current Product

Markio exposes document parsing as REST APIs, async tasks, SDK/CLI commands, and a browser console. The backend owns auth, parser dispatch, task execution, Redis integration, settings, logs, and static console serving.

## Pre-Development Checklist

- Read [dependencies.md](dependencies.md) before changing packages or runtime assumptions.
- Read [project-docs.md](project-docs.md) before editing public docs.
- Read [code-quality.md](code-quality.md) before code changes.
- Read [verification.md](verification.md) before claiming completion.

## Quality Check

- API, SDK, CLI, docs, and tests agree on route names and parser support.
- Auth remains enforced on `/v1/*`.
- Redis-related changes preserve in-memory fallback unless explicitly scoped otherwise.
- Vue console changes keep `/console` static serving and `/v1` proxy assumptions intact.
