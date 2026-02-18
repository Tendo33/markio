from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from time import perf_counter

from markio.schemas.task_schemas import (
    QueueHealth,
    SubmitTaskRequest,
    TaskListPage,
    TaskRecord,
    TaskStats,
    TaskStatus,
)
from markio.services.redis_task_store import RedisTaskStore
from markio.services.task_manager_base import (
    BaseTaskManager,
    CacheGetter,
    CacheSetter,
    ParserFunc,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


class RedisTaskManager(BaseTaskManager):
    def __init__(
        self,
        *,
        worker_count: int = 1,
        parser_func: ParserFunc | None = None,
        cache_getter: CacheGetter | None = None,
        cache_setter: CacheSetter | None = None,
        store: RedisTaskStore | None = None,
        max_auto_retries: int = 0,
        retry_delay_seconds: float = 0.0,
        processing_timeout_seconds: float = 0.0,
    ) -> None:
        super().__init__(
            parser_func=parser_func,
            cache_getter=cache_getter,
            cache_setter=cache_setter,
        )

        self.worker_count = max(1, worker_count)
        self.store = store or RedisTaskStore()
        self.max_auto_retries = max(0, max_auto_retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        self.processing_timeout_seconds = max(0.0, processing_timeout_seconds)

        self._workers: list[asyncio.Task[None]] = []
        self._started = False
        self._paused = False
        self._resume_event = asyncio.Event()
        self._resume_event.set()
        self._stop_event = asyncio.Event()
        self._timeout_check_lock = asyncio.Lock()
        self._last_timeout_check: float = 0.0

    async def start(self) -> None:
        if self._started:
            return
        self.store._ensure_redis()
        self._stop_event.clear()
        self._workers = [
            asyncio.create_task(self._worker_loop(index), name=f"redis-task-worker-{index}")
            for index in range(self.worker_count)
        ]
        self._started = True
        logger.info("Redis task manager started")

    async def stop(self) -> None:
        if not self._started:
            return
        self._stop_event.set()
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._started = False
        logger.info("Redis task manager stopped")

    async def pause_queue(self) -> None:
        self._paused = True
        self._resume_event.clear()

    async def resume_queue(self) -> None:
        self._paused = False
        self._resume_event.set()

    async def submit(self, request: SubmitTaskRequest) -> TaskRecord:
        if not self._started:
            raise RuntimeError("Task manager is not started")

        cache_key = self._build_cache_key(request)
        cache_allowed = not (
            request.save_parsed_content or request.save_middle_content
        )
        if cache_allowed and self.cache_getter and cache_key:
            cached_value = await self._safe_cache_get(cache_key)
            if cached_value:
                record = await self.store.submit_task(
                    request,
                    status=TaskStatus.completed,
                    result=cached_value,
                    cache_hit=True,
                    cache_key=cache_key,
                )
                self._cleanup_temp_file(request.file_path)
                return record

        return await self.store.submit_task(
            request,
            status=TaskStatus.pending,
            cache_key=cache_key,
        )

    async def get_task(self, task_id: str) -> TaskRecord | None:
        return await self.store.get_task(task_id)

    async def list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        status: TaskStatus | str | None = None,
    ) -> TaskListPage:
        status_filter = self._normalize_status_filter(status)
        return await self.store.list_tasks(status=status_filter, page=page, page_size=page_size)

    async def get_stats(self) -> TaskStats:
        return await self.store.get_stats()

    async def get_queue_health(self) -> QueueHealth:
        return await self.store.get_queue_health(self.worker_count, self._paused)

    async def get_dashboard(self, recent_limit: int = 10) -> dict:
        stats = await self.get_stats()
        queue_health = await self.get_queue_health()
        recent = await self.list_tasks(page=1, page_size=max(1, recent_limit))

        finished = stats.completed + stats.failed
        success_rate = 0.0
        if finished > 0:
            success_rate = round(stats.completed / finished, 4)

        return {
            "stats": {
                "pending": stats.pending,
                "processing": stats.processing,
                "completed": stats.completed,
                "failed": stats.failed,
            },
            "queue": {
                "queued": queue_health.queued,
                "processing": queue_health.processing,
                "workers": queue_health.workers,
                "paused": queue_health.paused,
            },
            "success_rate": success_rate,
            "recent_tasks": [self._record_to_dict(item) for item in recent.items],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def cancel_task(self, task_id: str) -> bool:
        return await self.store.cancel_task(task_id)

    async def retry_task(self, task_id: str) -> bool:
        request = await self.store.get_request(task_id)
        if request is None or not os.path.exists(request.file_path):
            return False
        return await self.store.mark_pending_for_retry(task_id)

    async def _worker_loop(self, worker_index: int) -> None:
        try:
            while not self._stop_event.is_set():
                await self._resume_event.wait()
                if self._stop_event.is_set():
                    break

                await self._maybe_requeue_timeouts()

                task = await self.store.claim_next_task()
                if task is None:
                    await asyncio.sleep(0.1)
                    continue

                request = await self.store.get_request(task.task_id)
                if request is None:
                    await self.store.mark_failed(task.task_id, "Missing task request")
                    continue

                cache_key = await self.store.get_cache_key(task.task_id)
                started_at_perf = perf_counter()
                try:
                    result = await self.parser_func(request.file_path, request)
                    await self.store.mark_completed(task.task_id, result)
                    await self._safe_cache_set(cache_key, result)
                    self._cleanup_temp_file(request.file_path)
                    elapsed_ms = max(0, int((perf_counter() - started_at_perf) * 1000))
                    logger.info(
                        "Task %s completed in %d ms (filename=%s)",
                        task.task_id,
                        elapsed_ms,
                        request.filename,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Task %s failed: %s", task.task_id, exc)
                    await self._handle_failure(task.task_id, str(exc), request)
        except asyncio.CancelledError:
            logger.info("Redis task worker %s cancelled", worker_index)

    async def _handle_failure(
        self,
        task_id: str,
        message: str,
        request: SubmitTaskRequest | None,
    ) -> None:
        task = await self.store.get_task(task_id, include_result=False)
        if task is None:
            return

        can_retry = (
            request is not None
            and task.retry_count < self.max_auto_retries
            and os.path.exists(request.file_path)
        )
        if can_retry:
            await self.store.mark_pending_for_retry(task_id, error_message=message)
            if self.retry_delay_seconds > 0:
                await asyncio.sleep(self.retry_delay_seconds)
        else:
            await self.store.mark_failed(task_id, message)

    async def _maybe_requeue_timeouts(self) -> None:
        if self.processing_timeout_seconds <= 0:
            return
        now = asyncio.get_event_loop().time()
        if now - self._last_timeout_check < max(1.0, self.processing_timeout_seconds / 2):
            return
        async with self._timeout_check_lock:
            now = asyncio.get_event_loop().time()
            if now - self._last_timeout_check < max(1.0, self.processing_timeout_seconds / 2):
                return
            self._last_timeout_check = now
            await self.store.requeue_timeouts(
                self.processing_timeout_seconds,
                self.max_auto_retries,
            )

    @staticmethod
    def _record_to_dict(record: TaskRecord) -> dict:
        return {
            "task_id": record.task_id,
            "filename": record.filename,
            "status": record.status.value,
            "parse_method": record.parse_method,
            "lang": record.lang,
            "created_at": record.created_at.isoformat(),
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat()
            if record.completed_at
            else None,
            "result": record.result,
            "error_message": record.error_message,
            "cache_hit": record.cache_hit,
            "priority": record.priority,
            "retry_count": record.retry_count,
            "processing_duration_ms": record.processing_duration_ms,
        }
