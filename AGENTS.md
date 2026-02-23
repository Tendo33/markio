# Repository Guidelines

## Project Structure & Module Organization
- `markio/`: FastAPI backend, parsers, routers, services, settings, and SDK/CLI code.
- `tests/`: Pytest suite (`test_*.py`) plus test fixtures in `tests/test_docs/`.
- `frontend/`: Vue 3 + Vite console UI; built assets are served by the backend.
- `docs/`: usage guides, architecture notes, and design plans.
- `scripts/`: local helper scripts (for example concurrent/local processing).
- Runtime/output folders: `data/`, `logs/`, and `outputs/`.

## Build, Test, and Development Commands
- `uv sync && uv pip install -e .`: install Python dependencies and editable package.
- `python markio/main.py`: run the API locally at `http://localhost:8000`.
- `docker compose up -d`: start services with containerized dependencies.
- `uv run pytest`: run default test suite (`-m "not live"` from `pytest.ini`).
- `uv run pytest -m live`: run tests that require a running external Markio service.
- `cd frontend && npm install && npm run dev`: run frontend dev server.
- `cd frontend && npm run build`: type-check and build frontend assets.

## Coding Style & Naming Conventions
- Python: 4-space indentation, type hints on public interfaces, and small focused modules.
- Prefer `black` formatting, `ruff` linting, and `mypy` type checks from the dev dependency set.
- Naming: `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Frontend: Vue components in `PascalCase` (for example `TaskDetail.vue`), API/store modules with suffix patterns like `*Api.ts` and `*Store.ts`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` (`asyncio_mode = auto`).
- Name tests `test_<feature>.py`; keep parser/service regressions close to existing suites (for example `tests/test_parser_registry_dispatch.py`).
- Mark external-integration tests with `@pytest.mark.live`.
- No fixed coverage threshold is enforced; new features should include happy-path and error-path tests.

## Commit & Pull Request Guidelines
- Follow Conventional Commit style seen in history, e.g. `feat(parsers): ...`, `refactor(env): ...`, `chore(dependencies): ...`.
- Keep commit messages imperative, scoped, and single-purpose.
- PRs should include: concise summary, linked issue/design doc, test commands run, and config/env changes.
- Include screenshots for `frontend/` UI updates and request/response examples for API behavior changes.
