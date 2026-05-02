from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from redis.asyncio import Redis
from redis.exceptions import NoScriptError

from markio.schemas.task_schemas import (
    QueueHealth,
    SubmitTaskRequest,
    TaskListPage,
    TaskRecord,
    TaskStats,
    TaskStatus,
)
from markio.utils.redis_utils import redis_manager


class RedisTaskStore:
    def __init__(
        self,
        redis: Optional[Redis] = None,
        *,
        key_prefix: str = "",
        use_lua: bool = True,
    ) -> None:
        self.redis = redis
        self.key_prefix = key_prefix
        self.use_lua = use_lua
        self._claim_sha: Optional[str] = None
        self._cancel_sha: Optional[str] = None
        self._retry_sha: Optional[str] = None
        self._timeout_requeue_sha: Optional[str] = None

    async def set_queue_paused(
        self,
        paused: bool,
        *,
        updated_at: Optional[datetime] = None,
    ) -> None:
        redis = self._ensure_redis()
        now = updated_at or datetime.now(timezone.utc)
        await redis.hset(
            self._queue_state_key(),
            mapping={
                "paused": self._bool_value(paused),
                "updated_at": now.isoformat(),
            },
        )

    async def get_queue_paused(self) -> bool:
        redis = self._ensure_redis()
        payload = await redis.hgetall(self._queue_state_key())
        if not payload:
            return False
        decoded = self._decode_mapping(payload)
        return self._parse_bool(decoded.get("paused"))

    async def submit_task(
        self,
        request: SubmitTaskRequest,
        *,
        created_at: Optional[datetime] = None,
        status: TaskStatus = TaskStatus.pending,
        result: Optional[str] = None,
        cache_hit: bool = False,
        cache_key: str | None = None,
        task_id: Optional[str] = None,
    ) -> TaskRecord:
        redis = self._ensure_redis()
        now = created_at or datetime.now(timezone.utc)
        task_id = task_id or uuid.uuid4().hex
        result_key = self._result_key(task_id)
        owner_id = (request.owner_id or "").strip() or "anonymous"
        request.owner_id = owner_id

        payload = self._build_task_payload(
            task_id=task_id,
            request=request,
            status=status,
            created_at=now,
            started_at=None,
            completed_at=now if status == TaskStatus.completed else None,
            result_key=result_key,
            cache_hit=cache_hit,
            retry_count=0,
            error_message=None,
            cache_key=cache_key,
            processing_duration_ms=0 if status == TaskStatus.completed else None,
        )

        await redis.hset(self._task_key(task_id), mapping=payload)

        created_score = self._to_epoch(now)
        await redis.zadd(self._task_created_key(), {task_id: created_score})
        await redis.zadd(self._task_status_key(status), {task_id: created_score})
        await redis.zadd(self._owner_tasks_key(owner_id), {task_id: created_score})
        await redis.zadd(self._owner_status_key(owner_id, status), {task_id: created_score})

        if status == TaskStatus.pending:
            await self._enqueue_task(task_id, request.priority)
        elif status == TaskStatus.completed and result is not None:
            await redis.set(result_key, result)

        return await self.get_task(task_id, owner_id=owner_id)  # type: ignore[return-value]

    async def claim_next_task(self) -> Optional[TaskRecord]:
        redis = self._ensure_redis()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        now_epoch = self._to_epoch(now)

        if self.use_lua:
            task_id = await self._claim_with_lua(redis, now_iso, now_epoch)
        else:
            task_id = await self._claim_fallback(redis, now_iso, now_epoch)

        if not task_id:
            return None
        await self._sync_owner_indexes_from_task(task_id)
        return await self.get_task(task_id, include_result=False)

    async def mark_completed(self, task_id: str, result: str) -> None:
        redis = self._ensure_redis()
        now = datetime.now(timezone.utc)
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            return

        created_score = self._created_score_from_payload(payload)
        started_at = self._parse_datetime(self._decode(payload.get("started_at")))
        duration_ms = self._duration_ms(started_at, now)
        await redis.hset(
            task_key,
            mapping={
                "status": TaskStatus.completed.value,
                "completed_at": now.isoformat(),
                "error_message": "",
                "processing_duration_ms": (
                    "" if duration_ms is None else str(duration_ms)
                ),
            },
        )
        await redis.set(self._result_key(task_id), result)
        await self._move_status(task_id, payload, TaskStatus.completed, created_score)
        await redis.zrem(self._queue_processing_key(), task_id)

    async def mark_failed(self, task_id: str, message: str) -> None:
        redis = self._ensure_redis()
        now = datetime.now(timezone.utc)
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            return

        created_score = self._created_score_from_payload(payload)
        started_at = self._parse_datetime(self._decode(payload.get("started_at")))
        duration_ms = self._duration_ms(started_at, now)
        await redis.hset(
            task_key,
            mapping={
                "status": TaskStatus.failed.value,
                "completed_at": now.isoformat(),
                "error_message": message,
                "processing_duration_ms": (
                    "" if duration_ms is None else str(duration_ms)
                ),
            },
        )
        await redis.delete(self._result_key(task_id))
        await self._move_status(task_id, payload, TaskStatus.failed, created_score)
        await redis.zrem(self._queue_processing_key(), task_id)

    async def mark_pending_for_retry(
        self,
        task_id: str,
        error_message: str | None = None,
        owner_id: str | None = None,
    ) -> bool:
        redis = self._ensure_redis()
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            return False

        payload = self._decode_mapping(payload)
        if not self._owner_matches(payload, owner_id):
            return False
        status = payload.get("status", "")
        if status not in {TaskStatus.failed.value, TaskStatus.canceled.value}:
            return False

        if self.use_lua:
            retried = await self._retry_with_lua(
                task_id=task_id,
                owner_id=owner_id,
                error_message=error_message,
                created_score=self._created_score_from_payload(payload),
            )
            if retried:
                await self._sync_owner_indexes_from_task(task_id)
            return retried

        retry_count = int(payload.get("retry_count", "0")) + 1
        created_score = self._created_score_from_payload(payload)
        await redis.hset(
            task_key,
            mapping={
                "status": TaskStatus.pending.value,
                "error_message": error_message or "",
                "retry_count": str(retry_count),
                "started_at": "",
                "completed_at": "",
                "processing_duration_ms": "",
            },
        )
        await redis.delete(self._result_key(task_id))
        await self._move_status(task_id, payload, TaskStatus.pending, created_score)
        priority = int(payload.get("priority", "0"))
        await self._enqueue_task(task_id, priority)
        return True

    async def cancel_task(self, task_id: str, owner_id: str | None = None) -> bool:
        redis = self._ensure_redis()
        now = datetime.now(timezone.utc)
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            return False

        payload = self._decode_mapping(payload)
        if not self._owner_matches(payload, owner_id):
            return False
        status = payload.get("status", "")
        if status != TaskStatus.pending.value:
            return False

        if self.use_lua:
            canceled = await self._cancel_with_lua(
                task_id=task_id,
                now_iso=now.isoformat(),
                owner_id=owner_id,
                created_score=self._created_score_from_payload(payload),
            )
            if canceled:
                await self._sync_owner_indexes_from_task(task_id)
            return canceled

        created_score = self._created_score_from_payload(payload)
        await redis.hset(
            task_key,
            mapping={
                "status": TaskStatus.canceled.value,
                "completed_at": now.isoformat(),
                "error_message": "Canceled by user",
                "processing_duration_ms": "",
            },
        )
        await redis.zrem(self._queue_pending_key(), task_id)
        await self._move_status(task_id, payload, TaskStatus.canceled, created_score)
        return True

    async def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        page: int = 1,
        page_size: int = 20,
        owner_id: str | None = None,
        include_result: bool = True,
    ) -> TaskListPage:
        redis = self._ensure_redis()
        page = max(1, page)
        page_size = max(1, page_size)
        key = self._task_status_key(status) if status else self._task_created_key()
        start = (page - 1) * page_size
        end = start + page_size - 1

        if owner_id:
            if status is None:
                owner_key = self._owner_tasks_key(owner_id)
            else:
                owner_key = self._owner_status_key(owner_id, status)
            total = int(await redis.zcard(owner_key))

            if total == 0:
                owner_total = int(await redis.zcard(self._owner_tasks_key(owner_id)))
                if owner_total == 0:
                    owner_total = await self._rebuild_owner_index(owner_id)
                if status is None:
                    total = owner_total
                elif owner_total > 0:
                    total = await self._rebuild_owner_status_index(
                        owner_id,
                        status=status,
                    )

            if hasattr(redis, "zrevrange"):
                task_ids = await redis.zrevrange(owner_key, start, end)
            else:
                all_task_ids = await redis.zrange(owner_key, 0, -1)
                task_ids = list(reversed(all_task_ids))[start : end + 1]

            collected = await self._fetch_tasks_by_ids(
                [self._decode(raw_task_id) for raw_task_id in task_ids],
                owner_id=owner_id,
                include_result=include_result,
            )
        else:
            if hasattr(redis, "zrevrange"):
                task_ids = await redis.zrevrange(key, start, end)
            else:
                all_task_ids = await redis.zrange(key, 0, -1)
                task_ids = list(reversed(all_task_ids))[start : end + 1]

            total = int(await redis.zcard(key))
            collected = await self._fetch_tasks_by_ids(
                [self._decode(raw_task_id) for raw_task_id in task_ids],
                include_result=include_result,
            )

        return TaskListPage(
            items=collected,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_task(
        self,
        task_id: str,
        *,
        owner_id: str | None = None,
        include_result: bool = True,
    ) -> Optional[TaskRecord]:
        redis = self._ensure_redis()
        payload = await redis.hgetall(self._task_key(task_id))
        if not payload:
            return None
        payload = self._decode_mapping(payload)
        if not self._owner_matches(payload, owner_id):
            return None

        result: Optional[str] = None
        if include_result:
            stored = await redis.get(self._result_key(task_id))
            if stored is not None:
                result = self._decode(stored)

        return self._build_task_record(payload, result)

    async def get_request(self, task_id: str, owner_id: str | None = None) -> Optional[SubmitTaskRequest]:
        payload = await self._get_payload(task_id)
        if not payload:
            return None
        if not self._owner_matches(payload, owner_id):
            return None
        return self._build_request(payload)

    async def get_cache_key(self, task_id: str) -> Optional[str]:
        payload = await self._get_payload(task_id)
        if not payload:
            return None
        value = payload.get("cache_key")
        return value or None

    async def get_stats(self, owner_id: str | None = None) -> TaskStats:
        redis = self._ensure_redis()
        if not owner_id:
            return TaskStats(
                pending=int(await redis.zcard(self._task_status_key(TaskStatus.pending))),
                processing=int(await redis.zcard(self._task_status_key(TaskStatus.processing))),
                completed=int(await redis.zcard(self._task_status_key(TaskStatus.completed))),
                failed=int(await redis.zcard(self._task_status_key(TaskStatus.failed))),
                canceled=int(await redis.zcard(self._task_status_key(TaskStatus.canceled))),
            )

        owner_ids_raw = await redis.zrange(self._owner_tasks_key(owner_id), 0, -1)
        owner_total = len(owner_ids_raw)
        if owner_total == 0:
            owner_total = await self._rebuild_owner_index(owner_id)
        if owner_total == 0:
            return TaskStats()
        stats = TaskStats(
            pending=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.pending))),
            processing=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.processing))),
            completed=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.completed))),
            failed=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.failed))),
            canceled=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.canceled))),
        )
        if (
            stats.pending
            + stats.processing
            + stats.completed
            + stats.failed
            + stats.canceled
            == 0
        ):
            await self._rebuild_all_owner_status_indexes(owner_id)
            stats = TaskStats(
                pending=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.pending))),
                processing=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.processing))),
                completed=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.completed))),
                failed=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.failed))),
                canceled=int(await redis.zcard(self._owner_status_key(owner_id, TaskStatus.canceled))),
            )
        return stats

    async def get_queue_health(
        self,
        worker_count: int,
        paused: bool,
        *,
        owner_id: str | None = None,
    ) -> QueueHealth:
        redis = self._ensure_redis()
        if owner_id:
            queued = int(
                await redis.zcard(self._owner_status_key(owner_id, TaskStatus.pending))
            )
            processing = int(
                await redis.zcard(
                    self._owner_status_key(owner_id, TaskStatus.processing)
                )
            )
        else:
            queued = int(await redis.zcard(self._queue_pending_key()))
            processing = int(await redis.zcard(self._queue_processing_key()))
        return QueueHealth(
            queued=queued,
            processing=processing,
            workers=worker_count,
            paused=paused,
        )

    async def requeue_timeouts(self, timeout_seconds: float, max_auto_retries: int) -> None:
        if timeout_seconds <= 0:
            return
        redis = self._ensure_redis()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        cutoff = self._to_epoch(now) - float(timeout_seconds)
        task_ids = await redis.zrangebyscore(self._queue_processing_key(), 0, cutoff)
        for raw_task_id in task_ids:
            task_id = self._decode(raw_task_id)
            if self.use_lua:
                await self._requeue_timeout_with_lua(
                    task_id=task_id,
                    now_iso=now_iso,
                    cutoff_epoch=cutoff,
                    max_auto_retries=max_auto_retries,
                )
                await self._sync_owner_indexes_from_task(task_id)
                continue

            payload = await redis.hgetall(self._task_key(task_id))
            if not payload:
                await redis.zrem(self._queue_processing_key(), task_id)
                await redis.zrem(
                    self._task_status_key(TaskStatus.processing),
                    task_id,
                )
                continue

            payload = self._decode_mapping(payload)
            if payload.get("status") != TaskStatus.processing.value:
                await redis.zrem(self._queue_processing_key(), task_id)
                await redis.zrem(
                    self._task_status_key(TaskStatus.processing),
                    task_id,
                )
                continue

            retry_count = int(payload.get("retry_count", "0"))
            created_score = self._created_score_from_payload(payload)
            if retry_count < max_auto_retries:
                await redis.hset(
                    self._task_key(task_id),
                    mapping={
                        "status": TaskStatus.pending.value,
                        "error_message": "Processing timeout",
                        "retry_count": str(retry_count + 1),
                        "started_at": "",
                        "completed_at": "",
                        "processing_duration_ms": "",
                    },
                )
                await redis.zrem(self._queue_processing_key(), task_id)
                await redis.zrem(
                    self._task_status_key(TaskStatus.processing),
                    task_id,
                )
                await redis.zadd(
                    self._task_status_key(TaskStatus.pending),
                    {task_id: created_score},
                )
                priority = int(payload.get("priority", "0"))
                await self._enqueue_task(task_id, priority)
                await self._sync_owner_indexes_from_task(task_id)
            else:
                await redis.hset(
                    self._task_key(task_id),
                    mapping={
                        "status": TaskStatus.failed.value,
                        "completed_at": now_iso,
                        "error_message": "Processing timeout",
                        "processing_duration_ms": "",
                    },
                )
                await redis.delete(self._result_key(task_id))
                await redis.zrem(self._queue_processing_key(), task_id)
                await redis.zrem(
                    self._task_status_key(TaskStatus.processing),
                    task_id,
                )
                await redis.zadd(
                    self._task_status_key(TaskStatus.failed),
                    {task_id: created_score},
                )
                await self._sync_owner_indexes_from_task(task_id)

    async def clear_all(self) -> None:
        redis = self._ensure_redis()
        owner_keys: set[str] = set()
        task_keys: list[str] = []
        result_keys: list[str] = []
        task_ids_with_scores = await redis.zrange(self._task_created_key(), 0, -1, withscores=True)
        for raw_task_id, _ in task_ids_with_scores:
            task_id = self._decode(raw_task_id)
            task_keys.append(self._task_key(task_id))
            result_keys.append(self._result_key(task_id))
            payload = await self._get_payload(task_id)
            if payload:
                owner_keys.add(self._owner_tasks_key(payload.get("owner_id", "anonymous")))
                for status in TaskStatus:
                    owner_keys.add(
                        self._owner_status_key(
                            payload.get("owner_id", "anonymous"),
                            status,
                        )
                    )
        keys = [
            self._queue_pending_key(),
            self._queue_processing_key(),
            self._task_created_key(),
            self._queue_seq_key(),
            self._queue_state_key(),
        ]
        for status in TaskStatus:
            keys.append(self._task_status_key(status))
        keys.extend(owner_keys)
        keys.extend(task_keys)
        keys.extend(result_keys)
        if keys:
            await redis.delete(*keys)

    def _task_key(self, task_id: str) -> str:
        return f"{self.key_prefix}task:{task_id}"

    def _result_key(self, task_id: str) -> str:
        return f"{self.key_prefix}result:{task_id}"

    def _task_created_key(self) -> str:
        return f"{self.key_prefix}task:created"

    def _task_status_key(self, status: TaskStatus | None) -> str:
        if status is None:
            raise ValueError("status is required")
        return f"{self.key_prefix}task:status:{status.value}"

    def _owner_tasks_key(self, owner_id: str) -> str:
        normalized = owner_id.strip() or "anonymous"
        return f"{self.key_prefix}task:owner:{normalized}"

    def _owner_status_key(self, owner_id: str, status: TaskStatus | str) -> str:
        normalized = owner_id.strip() or "anonymous"
        value = status.value if isinstance(status, TaskStatus) else status
        return f"{self.key_prefix}task:owner:{normalized}:status:{value}"

    def _queue_pending_key(self) -> str:
        return f"{self.key_prefix}queue:pending"

    def _queue_processing_key(self) -> str:
        return f"{self.key_prefix}queue:processing"

    def _queue_seq_key(self) -> str:
        return f"{self.key_prefix}queue:seq"

    def _queue_state_key(self) -> str:
        return f"{self.key_prefix}queue:state"

    def _task_key_prefix(self) -> str:
        return f"{self.key_prefix}task:"

    def _task_status_key_for_value(self, value: str) -> str:
        return f"{self.key_prefix}task:status:{value}"

    def _ensure_redis(self) -> Redis:
        if self.redis is None:
            self.redis = redis_manager.client
        if self.redis is None:
            raise RuntimeError("Redis client is not available")
        return self.redis

    async def _enqueue_task(self, task_id: str, priority: int) -> None:
        redis = self._ensure_redis()
        seq = await redis.incr(self._queue_seq_key())
        score = self._priority_score(priority, seq)
        await redis.zadd(self._queue_pending_key(), {task_id: score})

    @staticmethod
    def _priority_score(priority: int, seq: int) -> float:
        return (-int(priority) * 1_000_000_000_000) + float(seq)

    @staticmethod
    def _to_epoch(dt: datetime) -> float:
        return dt.timestamp()

    def _build_task_payload(
        self,
        *,
        task_id: str,
        request: SubmitTaskRequest,
        status: TaskStatus,
        created_at: datetime,
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
        result_key: str,
        cache_hit: bool,
        retry_count: int,
        error_message: Optional[str],
        cache_key: str | None,
        processing_duration_ms: Optional[int],
    ) -> dict[str, str]:
        return {
            "task_id": task_id,
            "filename": request.filename,
            "owner_id": request.owner_id,
            "file_path": request.file_path,
            "parse_method": request.parse_method,
            "lang": request.lang,
            "save_parsed_content": self._bool_value(request.save_parsed_content),
            "save_middle_content": self._bool_value(request.save_middle_content),
            "output_dir": request.output_dir,
            "start_page": str(request.start_page),
            "end_page": "" if request.end_page is None else str(request.end_page),
            "priority": str(request.priority),
            "status": status.value,
            "created_at": created_at.isoformat(),
            "started_at": "" if started_at is None else started_at.isoformat(),
            "completed_at": "" if completed_at is None else completed_at.isoformat(),
            "result_key": result_key,
            "cache_hit": self._bool_value(cache_hit),
            "retry_count": str(retry_count),
            "error_message": error_message or "",
            "cache_key": cache_key or "",
            "processing_duration_ms": (
                "" if processing_duration_ms is None else str(processing_duration_ms)
            ),
        }

    def _build_task_record(self, payload: dict[str, str], result: Optional[str]) -> TaskRecord:
        created_at = self._parse_datetime(payload.get("created_at"))
        return TaskRecord(
            task_id=payload.get("task_id", ""),
            filename=payload.get("filename", ""),
            owner_id=payload.get("owner_id", "anonymous"),
            status=TaskStatus(payload.get("status", TaskStatus.pending.value)),
            parse_method=payload.get("parse_method", "auto"),
            lang=payload.get("lang", "ch"),
            created_at=created_at or datetime.now(timezone.utc),
            started_at=self._parse_datetime(payload.get("started_at")),
            completed_at=self._parse_datetime(payload.get("completed_at")),
            result=result,
            error_message=payload.get("error_message") or None,
            cache_hit=self._parse_bool(payload.get("cache_hit")),
            priority=int(payload.get("priority", "0")),
            retry_count=int(payload.get("retry_count", "0")),
            processing_duration_ms=(
                int(payload["processing_duration_ms"])
                if payload.get("processing_duration_ms")
                else None
            ),
        )

    @staticmethod
    def _build_request(payload: dict[str, str]) -> SubmitTaskRequest:
        return SubmitTaskRequest(
            filename=payload.get("filename", ""),
            file_path=payload.get("file_path", ""),
            owner_id=payload.get("owner_id", "anonymous"),
            parse_method=payload.get("parse_method", "auto"),
            lang=payload.get("lang", "ch"),
            save_parsed_content=payload.get("save_parsed_content", "0") == "1",
            save_middle_content=payload.get("save_middle_content", "0") == "1",
            output_dir=payload.get("output_dir", "outputs"),
            start_page=int(payload.get("start_page", "0")),
            end_page=int(payload["end_page"]) if payload.get("end_page") else None,
            priority=int(payload.get("priority", "0")),
        )

    async def _get_payload(self, task_id: str) -> Optional[dict[str, str]]:
        redis = self._ensure_redis()
        payload = await redis.hgetall(self._task_key(task_id))
        if not payload:
            return None
        return self._decode_mapping(payload)

    async def _fetch_payloads(self, task_ids: list[str]) -> dict[str, dict[str, str]]:
        redis = self._ensure_redis()
        if not task_ids:
            return {}

        payloads_raw: list[dict[Any, Any]]
        if hasattr(redis, "pipeline"):
            pipeline = redis.pipeline(transaction=False)
            for task_id in task_ids:
                pipeline.hgetall(self._task_key(task_id))
            payloads_raw = await pipeline.execute()
        else:
            payloads_raw = []
            for task_id in task_ids:
                payloads_raw.append(await redis.hgetall(self._task_key(task_id)))

        payloads: dict[str, dict[str, str]] = {}
        for task_id, payload in zip(task_ids, payloads_raw, strict=False):
            if not payload:
                continue
            payloads[task_id] = self._decode_mapping(payload)
        return payloads

    async def _fetch_tasks_by_ids(
        self,
        task_ids: list[str],
        *,
        owner_id: str | None = None,
        include_result: bool = True,
    ) -> list[TaskRecord]:
        redis = self._ensure_redis()
        if not task_ids:
            return []

        payload_map = await self._fetch_payloads(task_ids)
        filtered_ids = [
            task_id
            for task_id in task_ids
            if task_id in payload_map
            and self._owner_matches(payload_map[task_id], owner_id)
        ]
        if not filtered_ids:
            return []

        result_map: dict[str, str] = {}
        if include_result:
            result_keys = [self._result_key(task_id) for task_id in filtered_ids]
            if hasattr(redis, "mget"):
                raw_results = await redis.mget(result_keys)
                for task_id, raw in zip(filtered_ids, raw_results, strict=False):
                    if raw is not None:
                        result_map[task_id] = self._decode(raw)
            else:
                for task_id in filtered_ids:
                    raw = await redis.get(self._result_key(task_id))
                    if raw is not None:
                        result_map[task_id] = self._decode(raw)

        records: list[TaskRecord] = []
        for task_id in filtered_ids:
            payload = payload_map.get(task_id)
            if not payload:
                continue
            records.append(self._build_task_record(payload, result_map.get(task_id)))
        return records

    async def _claim_with_lua(self, redis: Redis, now_iso: str, now_epoch: float) -> Optional[str]:
        if self._claim_sha is None:
            self._claim_sha = await redis.script_load(self._claim_script())
        try:
            result = await redis.evalsha(
                self._claim_sha,
                4,
                self._queue_pending_key(),
                self._queue_processing_key(),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.processing),
                self._task_key_prefix(),
                now_iso,
                str(now_epoch),
            )
        except NoScriptError:
            self._claim_sha = await redis.script_load(self._claim_script())
            result = await redis.evalsha(
                self._claim_sha,
                4,
                self._queue_pending_key(),
                self._queue_processing_key(),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.processing),
                self._task_key_prefix(),
                now_iso,
                str(now_epoch),
            )
        if not result:
            return None
        if isinstance(result, (list, tuple)):
            return self._decode(result[0])
        return self._decode(result)

    async def _cancel_with_lua(
        self,
        *,
        task_id: str,
        now_iso: str,
        owner_id: str | None,
        created_score: float,
    ) -> bool:
        redis = self._ensure_redis()
        if self._cancel_sha is None:
            self._cancel_sha = await redis.script_load(self._cancel_script())
        try:
            result = await redis.evalsha(
                self._cancel_sha,
                4,
                self._task_key(task_id),
                self._queue_pending_key(),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.canceled),
                task_id,
                now_iso,
                owner_id or "",
                str(created_score),
            )
        except NoScriptError:
            self._cancel_sha = await redis.script_load(self._cancel_script())
            result = await redis.evalsha(
                self._cancel_sha,
                4,
                self._task_key(task_id),
                self._queue_pending_key(),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.canceled),
                task_id,
                now_iso,
                owner_id or "",
                str(created_score),
            )
        return bool(result == 1)

    async def _retry_with_lua(
        self,
        *,
        task_id: str,
        owner_id: str | None,
        error_message: str | None,
        created_score: float,
    ) -> bool:
        redis = self._ensure_redis()
        if self._retry_sha is None:
            self._retry_sha = await redis.script_load(self._retry_script())
        try:
            result = await redis.evalsha(
                self._retry_sha,
                8,
                self._task_key(task_id),
                self._queue_pending_key(),
                self._task_status_key(TaskStatus.failed),
                self._task_status_key(TaskStatus.canceled),
                self._task_status_key(TaskStatus.pending),
                self._result_key(task_id),
                self._queue_seq_key(),
                self._queue_processing_key(),
                task_id,
                owner_id or "",
                error_message or "",
                str(created_score),
            )
        except NoScriptError:
            self._retry_sha = await redis.script_load(self._retry_script())
            result = await redis.evalsha(
                self._retry_sha,
                8,
                self._task_key(task_id),
                self._queue_pending_key(),
                self._task_status_key(TaskStatus.failed),
                self._task_status_key(TaskStatus.canceled),
                self._task_status_key(TaskStatus.pending),
                self._result_key(task_id),
                self._queue_seq_key(),
                self._queue_processing_key(),
                task_id,
                owner_id or "",
                error_message or "",
                str(created_score),
            )
        return bool(result == 1)

    async def _requeue_timeout_with_lua(
        self,
        *,
        task_id: str,
        now_iso: str,
        cutoff_epoch: float,
        max_auto_retries: int,
    ) -> None:
        redis = self._ensure_redis()
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            await redis.zrem(self._queue_processing_key(), task_id)
            await redis.zrem(self._task_status_key(TaskStatus.processing), task_id)
            return
        decoded_payload = self._decode_mapping(payload)
        created_score = self._created_score_from_payload(decoded_payload)

        if self._timeout_requeue_sha is None:
            self._timeout_requeue_sha = await redis.script_load(
                self._timeout_requeue_script()
            )
        try:
            await redis.evalsha(
                self._timeout_requeue_sha,
                8,
                task_key,
                self._queue_processing_key(),
                self._task_status_key(TaskStatus.processing),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.failed),
                self._queue_pending_key(),
                self._queue_seq_key(),
                self._result_key(task_id),
                task_id,
                now_iso,
                str(cutoff_epoch),
                str(max_auto_retries),
                str(created_score),
            )
        except NoScriptError:
            self._timeout_requeue_sha = await redis.script_load(
                self._timeout_requeue_script()
            )
            await redis.evalsha(
                self._timeout_requeue_sha,
                8,
                task_key,
                self._queue_processing_key(),
                self._task_status_key(TaskStatus.processing),
                self._task_status_key(TaskStatus.pending),
                self._task_status_key(TaskStatus.failed),
                self._queue_pending_key(),
                self._queue_seq_key(),
                self._result_key(task_id),
                task_id,
                now_iso,
                str(cutoff_epoch),
                str(max_auto_retries),
                str(created_score),
            )

    async def _claim_fallback(self, redis: Redis, now_iso: str, now_epoch: float) -> Optional[str]:
        items = await redis.zpopmin(self._queue_pending_key(), 1)
        if not items:
            return None
        task_id = self._decode(items[0][0])
        task_key = self._task_key(task_id)
        payload = await redis.hgetall(task_key)
        if not payload:
            return None
        payload = self._decode_mapping(payload)
        created_score = self._created_score_from_payload(payload)
        await redis.hset(
            task_key,
            mapping={"status": TaskStatus.processing.value, "started_at": now_iso},
        )
        await redis.zadd(self._queue_processing_key(), {task_id: now_epoch})
        await redis.zrem(self._task_status_key_for_value(TaskStatus.pending.value), task_id)
        await redis.zadd(self._task_status_key(TaskStatus.processing), {task_id: created_score})
        await self._sync_owner_indexes_from_task(task_id)
        return task_id

    async def _move_status(
        self,
        task_id: str,
        payload: dict[str, Any],
        new_status: TaskStatus,
        created_score: float,
    ) -> None:
        redis = self._ensure_redis()
        old_status = self._decode(payload.get("status")) if payload else None
        if old_status:
            await redis.zrem(self._task_status_key_for_value(old_status), task_id)
        await redis.zadd(self._task_status_key(new_status), {task_id: created_score})
        owner_payload = dict(payload)
        owner_payload["status"] = new_status.value
        await self._ensure_owner_index(
            task_id=task_id,
            payload=owner_payload,
            created_score=created_score,
        )

    async def _ensure_owner_index(
        self,
        *,
        task_id: str,
        payload: dict[str, Any],
        created_score: float,
    ) -> None:
        redis = self._ensure_redis()
        owner_id = self._decode(payload.get("owner_id")) if payload else "anonymous"
        await redis.zadd(self._owner_tasks_key(owner_id), {task_id: created_score})
        for status in TaskStatus:
            await redis.zrem(self._owner_status_key(owner_id, status), task_id)
        status_value = self._decode(payload.get("status")) if payload else ""
        if status_value:
            await redis.zadd(
                self._owner_status_key(owner_id, status_value),
                {task_id: created_score},
            )

    async def _rebuild_owner_index(self, owner_id: str) -> int:
        redis = self._ensure_redis()
        owner_key = self._owner_tasks_key(owner_id)
        pairs = await redis.zrange(self._task_created_key(), 0, -1, withscores=True)
        for status in TaskStatus:
            await redis.delete(self._owner_status_key(owner_id, status))
        for raw_task_id, score in pairs:
            task_id = self._decode(raw_task_id)
            payload = await self._get_payload(task_id)
            if payload and self._owner_matches(payload, owner_id):
                await redis.zadd(owner_key, {task_id: float(score)})
                status_value = payload.get("status")
                if status_value:
                    await redis.zadd(
                        self._owner_status_key(owner_id, status_value),
                        {task_id: float(score)},
                    )
        return int(await redis.zcard(owner_key))

    async def _rebuild_owner_status_index(
        self,
        owner_id: str,
        *,
        status: TaskStatus,
    ) -> int:
        redis = self._ensure_redis()
        owner_key = self._owner_tasks_key(owner_id)
        owner_status_key = self._owner_status_key(owner_id, status)
        await redis.delete(owner_status_key)
        pairs = await redis.zrange(owner_key, 0, -1, withscores=True)
        for raw_task_id, score in pairs:
            task_id = self._decode(raw_task_id)
            payload = await self._get_payload(task_id)
            if (
                payload
                and self._owner_matches(payload, owner_id)
                and payload.get("status") == status.value
            ):
                await redis.zadd(owner_status_key, {task_id: float(score)})
        return int(await redis.zcard(owner_status_key))

    async def _rebuild_all_owner_status_indexes(self, owner_id: str) -> None:
        redis = self._ensure_redis()
        owner_key = self._owner_tasks_key(owner_id)
        for status in TaskStatus:
            await redis.delete(self._owner_status_key(owner_id, status))
        pairs = await redis.zrange(owner_key, 0, -1, withscores=True)
        for raw_task_id, score in pairs:
            task_id = self._decode(raw_task_id)
            payload = await self._get_payload(task_id)
            if not payload or not self._owner_matches(payload, owner_id):
                continue
            status_value = payload.get("status")
            if not status_value:
                continue
            await redis.zadd(
                self._owner_status_key(owner_id, status_value),
                {task_id: float(score)},
            )

    async def _sync_owner_indexes_from_task(self, task_id: str) -> None:
        payload = await self._get_payload(task_id)
        if not payload:
            return
        await self._ensure_owner_index(
            task_id=task_id,
            payload=payload,
            created_score=self._created_score_from_payload(payload),
        )

    @staticmethod
    def _decode(value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if value is None:
            return ""
        return str(value)

    def _decode_mapping(self, payload: dict[Any, Any]) -> dict[str, str]:
        return {self._decode(key): self._decode(value) for key, value in payload.items()}

    @staticmethod
    def _owner_matches(payload: dict[str, str], owner_id: str | None) -> bool:
        if not owner_id:
            return True
        return payload.get("owner_id", "anonymous") == owner_id

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _bool_value(value: bool) -> str:
        return "1" if value else "0"

    @staticmethod
    def _parse_bool(value: Optional[str]) -> bool:
        if value is None:
            return False
        return str(value) == "1"

    @staticmethod
    def _duration_ms(
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
    ) -> Optional[int]:
        if started_at is None or completed_at is None:
            return None
        duration = int((completed_at - started_at).total_seconds() * 1000)
        return max(duration, 0)

    def _created_score_from_payload(self, payload: dict[str, Any]) -> float:
        created_at = self._parse_datetime(self._decode(payload.get("created_at")))
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        return self._to_epoch(created_at)

    @staticmethod
    def _claim_script() -> str:
        return """
local pending = KEYS[1]
local processing = KEYS[2]
local status_pending = KEYS[3]
local status_processing = KEYS[4]
local task_prefix = ARGV[1]
local now_iso = ARGV[2]
local now_epoch = tonumber(ARGV[3])

local popped = redis.call('ZPOPMIN', pending, 1)
if (#popped == 0) then
  return nil
end
local task_id = popped[1]
local task_key = task_prefix .. task_id

redis.call('HSET', task_key, 'status', 'processing', 'started_at', now_iso)
redis.call('ZREM', status_pending, task_id)
redis.call('ZADD', status_processing, now_epoch, task_id)
redis.call('ZADD', processing, now_epoch, task_id)
return {task_id}
"""

    @staticmethod
    def _cancel_script() -> str:
        return """
local task_key = KEYS[1]
local queue_pending = KEYS[2]
local status_pending = KEYS[3]
local status_canceled = KEYS[4]

local task_id = ARGV[1]
local now_iso = ARGV[2]
local owner_id = ARGV[3]
local created_score = tonumber(ARGV[4])

if redis.call('EXISTS', task_key) == 0 then
  return 0
end

local task_owner = redis.call('HGET', task_key, 'owner_id') or 'anonymous'
if owner_id ~= '' and task_owner ~= owner_id then
  return 0
end

local status = redis.call('HGET', task_key, 'status')
if status ~= 'pending' then
  return 0
end

redis.call('HSET', task_key,
  'status', 'canceled',
  'completed_at', now_iso,
  'error_message', 'Canceled by user',
  'processing_duration_ms', ''
)
redis.call('ZREM', queue_pending, task_id)
redis.call('ZREM', status_pending, task_id)
redis.call('ZADD', status_canceled, created_score, task_id)
return 1
"""

    @staticmethod
    def _retry_script() -> str:
        return """
local task_key = KEYS[1]
local queue_pending = KEYS[2]
local status_failed = KEYS[3]
local status_canceled = KEYS[4]
local status_pending = KEYS[5]
local result_key = KEYS[6]
local queue_seq = KEYS[7]
local queue_processing = KEYS[8]

local task_id = ARGV[1]
local owner_id = ARGV[2]
local error_message = ARGV[3]
local created_score = tonumber(ARGV[4])

if redis.call('EXISTS', task_key) == 0 then
  return 0
end

local task_owner = redis.call('HGET', task_key, 'owner_id') or 'anonymous'
if owner_id ~= '' and task_owner ~= owner_id then
  return 0
end

local status = redis.call('HGET', task_key, 'status')
if status ~= 'failed' and status ~= 'canceled' then
  return 0
end

local retry_count = tonumber(redis.call('HGET', task_key, 'retry_count') or '0') + 1
local priority = tonumber(redis.call('HGET', task_key, 'priority') or '0')
local seq = tonumber(redis.call('INCR', queue_seq))
local score = (0 - priority * 1000000000000) + seq

redis.call('HSET', task_key,
  'status', 'pending',
  'error_message', error_message,
  'retry_count', tostring(retry_count),
  'started_at', '',
  'completed_at', '',
  'processing_duration_ms', ''
)
redis.call('DEL', result_key)
redis.call('ZREM', status_failed, task_id)
redis.call('ZREM', status_canceled, task_id)
redis.call('ZREM', queue_processing, task_id)
redis.call('ZADD', status_pending, created_score, task_id)
redis.call('ZADD', queue_pending, score, task_id)
return 1
"""

    @staticmethod
    def _timeout_requeue_script() -> str:
        return """
local task_key = KEYS[1]
local queue_processing = KEYS[2]
local status_processing = KEYS[3]
local status_pending = KEYS[4]
local status_failed = KEYS[5]
local queue_pending = KEYS[6]
local queue_seq = KEYS[7]
local result_key = KEYS[8]

local task_id = ARGV[1]
local now_iso = ARGV[2]
local cutoff_epoch = tonumber(ARGV[3])
local max_auto_retries = tonumber(ARGV[4])
local created_score = tonumber(ARGV[5])

local processing_score = redis.call('ZSCORE', queue_processing, task_id)
if not processing_score then
  redis.call('ZREM', status_processing, task_id)
  return 0
end
if tonumber(processing_score) > cutoff_epoch then
  return 0
end

if redis.call('EXISTS', task_key) == 0 then
  redis.call('ZREM', queue_processing, task_id)
  redis.call('ZREM', status_processing, task_id)
  return 0
end

local status = redis.call('HGET', task_key, 'status')
if status ~= 'processing' then
  redis.call('ZREM', queue_processing, task_id)
  redis.call('ZREM', status_processing, task_id)
  return 0
end

local retry_count = tonumber(redis.call('HGET', task_key, 'retry_count') or '0')
if retry_count < max_auto_retries then
  local priority = tonumber(redis.call('HGET', task_key, 'priority') or '0')
  local seq = tonumber(redis.call('INCR', queue_seq))
  local score = (0 - priority * 1000000000000) + seq

  redis.call('HSET', task_key,
    'status', 'pending',
    'error_message', 'Processing timeout',
    'retry_count', tostring(retry_count + 1),
    'started_at', '',
    'completed_at', '',
    'processing_duration_ms', ''
  )
  redis.call('ZREM', queue_processing, task_id)
  redis.call('ZREM', status_processing, task_id)
  redis.call('ZADD', status_pending, created_score, task_id)
  redis.call('ZADD', queue_pending, score, task_id)
  return 1
end

redis.call('HSET', task_key,
  'status', 'failed',
  'completed_at', now_iso,
  'error_message', 'Processing timeout',
  'processing_duration_ms', ''
)
redis.call('DEL', result_key)
redis.call('ZREM', queue_processing, task_id)
redis.call('ZREM', status_processing, task_id)
redis.call('ZADD', status_failed, created_score, task_id)
return 2
"""
