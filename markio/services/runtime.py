from __future__ import annotations

from markio.services.redis_task_manager import RedisTaskManager
from markio.services.redis_task_store import RedisTaskStore
from markio.services.task_manager import AsyncTaskManager
from markio.settings import settings
from markio.utils.logger_config import get_logger
from markio.utils.redis_utils import RedisCache

logger = get_logger(__name__)


async def _cache_setter(key: str, value: str) -> bool:
    return await RedisCache.set(key, value, ttl=settings.redis_default_ttl)


task_backend = getattr(settings, "task_queue_backend", "memory").lower()
use_redis_backend = task_backend == "redis" and settings.redis_enabled

if task_backend == "redis" and not settings.redis_enabled:
    logger.warning(
        "TASK_QUEUE_BACKEND=redis requires REDIS_ENABLED=true. Falling back to memory backend."
    )

if use_redis_backend:
    _task_manager = RedisTaskManager(
        worker_count=getattr(settings, "task_worker_count", 2),
        cache_getter=RedisCache.get if settings.redis_enabled else None,
        cache_setter=_cache_setter if settings.redis_enabled else None,
        store=RedisTaskStore(),
        max_auto_retries=getattr(settings, "task_max_auto_retries", 0),
        retry_delay_seconds=getattr(settings, "task_retry_delay_seconds", 0.0),
        processing_timeout_seconds=getattr(
            settings,
            "task_processing_timeout_seconds",
            0.0,
        ),
    )
else:
    _task_manager = AsyncTaskManager(
        worker_count=getattr(settings, "task_worker_count", 2),
        cache_getter=RedisCache.get if settings.redis_enabled else None,
        cache_setter=_cache_setter if settings.redis_enabled else None,
        max_history=getattr(settings, "task_history_limit", 500),
        state_file_path=getattr(settings, "task_state_file", "data/task_state.json"),
        max_auto_retries=getattr(settings, "task_max_auto_retries", 0),
        retry_delay_seconds=getattr(settings, "task_retry_delay_seconds", 0.0),
    )


def get_task_manager() -> AsyncTaskManager | RedisTaskManager:
    return _task_manager
