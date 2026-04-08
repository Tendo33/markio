# Redis Integration

[Back to README](../README.md)

## Role of Redis in Markio

Redis is optional. The application runs without it by default.

When enabled, Redis is used for:

- cache storage
- task-state persistence
- Redis-backed async task backend

Relevant modules:

- `markio/utils/redis_utils.py`
- `markio/services/redis_task_store.py`
- `markio/services/redis_task_manager.py`

## Enable Redis

Redis-backed task execution requires both:

- `REDIS_ENABLED=true`
- `TASK_QUEUE_BACKEND=redis`

If `TASK_QUEUE_BACKEND=redis` is configured while `REDIS_ENABLED=false`, the runtime falls back to the in-memory backend and logs a warning.

## Compose Security Baseline

The current compose posture assumes Redis is internal infrastructure:

- Redis is not published to the host by default
- Redis auth is expected through `REDIS_PASSWORD`
- application and Redis service must use the same password

Example:

```bash
export AUTH_JWT_SECRET="<strong-random-secret>"
export REDIS_PASSWORD="<redis-password>"
docker compose up -d
```

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `REDIS_ENABLED` | Master on/off switch |
| `TASK_QUEUE_BACKEND` | `memory` or `redis` |
| `REDIS_HOST` | Redis host |
| `REDIS_PORT` | Redis port |
| `REDIS_DB` | Database index |
| `REDIS_PASSWORD` | Password for secured deployments |
| `REDIS_MAX_CONNECTIONS` | Pool size |
| `REDIS_SOCKET_TIMEOUT` | Command timeout |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | Connect timeout |
| `REDIS_DEFAULT_TTL` | Default cache TTL |

## Task Store Indexing

`RedisTaskStore` maintains:

- `task:created`
- `task:status:<status>`
- `task:owner:<owner_id>`
- `task:owner:<owner_id>:status:<status>`

Owner and owner+status indexes are updated on status changes. Legacy owner indexes can be rebuilt lazily during query flows.

## Operational Notes

- Redis startup failures are logged; readiness should be observed through `/readyz`
- the app can still run in memory mode even if Redis is unavailable
- Redis is an optional acceleration and persistence layer, not a startup hard requirement in the default configuration

## Verification

```bash
uv run pytest tests/test_redis.py tests/test_redis_task_store.py tests/test_redis_task_manager.py -q
```

Additional coverage:

- `tests/test_redis_cache_security.py`
- `tests/test_runtime_backend.py`

## When Not to Use Redis

Staging or small local setups can stay on:

- `REDIS_ENABLED=false`
- `TASK_QUEUE_BACKEND=memory`

That remains the simplest default for local development.
