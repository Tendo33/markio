# Markio Test Guide

## Overview

The repository uses `pytest` as the primary test runner and source of truth.

Default behavior:

- `pytest.ini` excludes `live` tests unless explicitly requested
- the suite covers sync parsers, task flows, auth boundaries, URL safety, Redis behavior, and console delivery

## Main Commands

### Default suite

```bash
uv run pytest
```

### Quiet mode

```bash
uv run pytest -q
```

### Live / external integration tests

```bash
uv run pytest -m live
```

### Targeted regression runs

```bash
uv run pytest tests/test_url_parser.py tests/test_console_frontend.py -q
uv run pytest tests/test_task_auth_and_idor.py tests/test_task_router.py -q
uv run pytest tests/test_redis.py tests/test_redis_task_store.py tests/test_redis_task_manager.py -q
uv run pytest tests/test_mcp_routes.py tests/test_observability_and_errors.py -q
```

### Console browser E2E

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

## Test Areas

### Core parser and API behavior

- `test_all_parsers.py`
- `test_parser_registry_dispatch.py`
- `test_sync_parse_service.py`
- `test_sync_response_contract.py`
- `test_pdf_parser_runtime.py`

### Security and safety

- `test_parser_route_security.py`
- `test_task_auth_and_idor.py`
- `test_url_parser.py`
- `test_observability_and_errors.py`
- `test_rate_limit_middleware.py`

### Console delivery

- `test_console_frontend.py`
- `test_main_routes.py`

This suite validates the `/console` delivery contract against real built frontend assets, not a fake placeholder route.

Browser-level regressions for the console now live under `frontend/e2e/` and run with Playwright against a local preview server plus mocked `/v1/*` responses.

### Async task system

- `test_task_manager.py`
- `test_task_manager_contract.py`
- `test_task_manager_base.py`
- `test_task_router.py`
- `test_task_settings.py`
- `test_runtime_backend.py`

### Redis

- `test_redis.py`
- `test_redis_cache_security.py`
- `test_redis_task_store.py`
- `test_redis_task_manager.py`

### Biological data parsing

- `test_biological_parsers.py`

## Test Utilities

The repository still contains helper scripts such as:

- `tests/run_tests.py`
- `tests/run_concurrent_tests.py`

They are legacy convenience wrappers. Prefer direct `pytest` commands for current development and CI work.

## Environment Expectations

Typical local setup:

- Python `3.11+`
- dependencies installed through `uv sync`
- editable install via `uv pip install -e .`

Some tests also assume:

- `AUTH_JWT_SECRET` is available through test fixtures or environment setup
- frontend dependencies are installable when console tests need a build
- Redis is optional; Redis-disabled paths are covered too

## Writing New Tests

- place new tests near the most relevant existing module
- prefer small targeted regression coverage over broad slow fixtures
- include both happy-path and failure-path coverage for new features
- use `@pytest.mark.live` only for tests that truly require external services

## Practical Notes

- console tests build frontend assets inside fixtures when needed
- security-sensitive changes should usually add tests in both route-level and lower-level parser/service modules
- the default suite already gives meaningful release confidence; use narrower commands during development for faster loops
