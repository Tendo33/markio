# Redis Integration

This document reflects the current Redis integration in Markio.

## What Redis Is Used For

- Cache layer (`markio/utils/redis_utils.py`)
- Async task backend when:
  - `TASK_QUEUE_BACKEND=redis`
  - `REDIS_ENABLED=true`
- Task state/index storage via `markio/services/redis_task_store.py`

## Current Security Baseline

- Redis is internal-only in Compose (`expose: 6379`, no host `ports` mapping).
- Redis auth is enabled by default in Compose (`--requirepass`).
- `REDIS_PASSWORD` must be set and shared by `markio` and `redis` services.

## Compose Example

```bash
export AUTH_JWT_SECRET="<strong-random-secret>"
export REDIS_PASSWORD="<redis-password>"
docker compose up -d
```

## Required/Important Environment Variables

- `REDIS_ENABLED` (`true|false`)
- `TASK_QUEUE_BACKEND` (`memory|redis`)
- `REDIS_HOST` (Compose default: `redis`)
- `REDIS_PORT` (default: `6379`)
- `REDIS_DB` (default: `0`)
- `REDIS_PASSWORD` (required for secured Redis deployment)
- `REDIS_MAX_CONNECTIONS`
- `REDIS_SOCKET_TIMEOUT`
- `REDIS_SOCKET_CONNECT_TIMEOUT`
- `REDIS_DEFAULT_TTL`

## Task Store Indexes

`RedisTaskStore` maintains:

- Global timeline index: `task:created`
- Global status indexes: `task:status:<status>`
- Owner index: `task:owner:<owner_id>`
- Owner+status indexes: `task:owner:<owner_id>:status:<status>`

On status transitions, owner+status indexes are updated synchronously.
For legacy records, owner/owner+status indexes can be lazily rebuilt during list/stats queries.

## Runtime Notes

- If `TASK_QUEUE_BACKEND=redis` but `REDIS_ENABLED=false`, runtime falls back to memory backend with a warning.
- Redis failures during app startup are logged; health/readiness should be monitored via `/readyz`.

## Verification

```bash
uv run pytest tests/test_redis.py tests/test_redis_task_store.py tests/test_redis_task_manager.py
```
