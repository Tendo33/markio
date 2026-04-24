from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from time import perf_counter

from markio.schemas.task_schemas import (
    QueueHealth,
    SubmitTaskRequest,
    TaskListPage,
    TaskRecord,
    TaskStats,
    TaskStatus,
)
from markio.services.task_manager_base import (
    BaseTaskManager,
    CacheGetter,
    CacheSetter,
    ParserFunc,
)

logger = logging.getLogger(__name__)


@dataclass
class QueueItem:
    task_id: str
    cache_key: str | None = None


class AsyncTaskManager(BaseTaskManager):
    def __init__(
        self,
        worker_count: int = 1,
        parser_func: ParserFunc | None = None,
        cache_getter: CacheGetter | None = None,
        cache_setter: CacheSetter | None = None,
        max_history: int = 500,
        state_file_path: str | None = None,
        state_result_max_chars: int = 0,
        max_auto_retries: int = 0,
        retry_delay_seconds: float = 0.0,
    ) -> None:
        super().__init__(
            parser_func=parser_func,
            cache_getter=cache_getter,
            cache_setter=cache_setter,
        )

        self.worker_count = max(1, worker_count)
        self.max_history = max(20, max_history)
        self.state_file_path = state_file_path
        self.state_result_max_chars = max(0, int(state_result_max_chars))
        self.max_auto_retries = max(0, max_auto_retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)

        self._queue: asyncio.PriorityQueue[tuple[int, int, str | None]] = (
            asyncio.PriorityQueue()
        )
        self._enqueue_seq = 0

        self._records: dict[str, TaskRecord] = {}
        self._requests: dict[str, SubmitTaskRequest] = {}
        self._pending_items: dict[str, QueueItem] = {}
        self._workers: list[asyncio.Task[None]] = []

        self._lock = asyncio.Lock()
        self._started = False
        self._paused = False
        self._resume_event = asyncio.Event()
        self._resume_event.set()

    async def start(self) -> None:
        if self._started:
            return

        async with self._lock:
            self._load_state_locked()
            pending_ids = list(self._pending_items.keys())
            if self._paused:
                self._resume_event.clear()
            else:
                self._resume_event.set()

        for task_id in pending_ids:
            await self._enqueue_task(task_id)

        self._workers = [
            asyncio.create_task(self._worker_loop(index), name=f"task-worker-{index}")
            for index in range(self.worker_count)
        ]
        self._started = True
        logger.info("Async task manager started")

    async def stop(self) -> None:
        if not self._started:
            return

        async with self._lock:
            self._paused = False
            self._resume_event.set()

        for _ in self._workers:
            self._enqueue_seq += 1
            await self._queue.put((10**12, self._enqueue_seq, None))

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        async with self._lock:
            self._persist_state_locked()

        self._started = False
        logger.info("Async task manager stopped")

    async def pause_queue(self) -> None:
        async with self._lock:
            self._paused = True
            self._resume_event.clear()
            self._persist_state_locked()

    async def resume_queue(self) -> None:
        async with self._lock:
            self._paused = False
            self._resume_event.set()
            self._persist_state_locked()

    async def submit(self, request: SubmitTaskRequest) -> TaskRecord:
        if not self._started:
            raise RuntimeError("Task manager is not started")

        owner_id = (request.owner_id or "").strip() or "anonymous"
        request.owner_id = owner_id
        task_id = uuid.uuid4().hex
        cache_key = self._build_cache_key(request)

        cache_allowed = not (
            request.save_parsed_content or request.save_middle_content
        )
        if cache_allowed and self.cache_getter and cache_key:
            cached_value = await self._safe_cache_get(cache_key)
            if cached_value:
                now = _utc_now()
                record = TaskRecord(
                    task_id=task_id,
                    filename=request.filename,
                    owner_id=owner_id,
                    status=TaskStatus.completed,
                    parse_method=request.parse_method,
                    lang=request.lang,
                    created_at=now,
                    started_at=now,
                    completed_at=now,
                    result=cached_value,
                    cache_hit=True,
                    priority=request.priority,
                    processing_duration_ms=0,
                )
                async with self._lock:
                    self._records[task_id] = record
                    self._prune_records_locked()
                    self._persist_state_locked()
                self._cleanup_temp_file(request.file_path)
                return copy.deepcopy(record)

        record = TaskRecord(
            task_id=task_id,
            filename=request.filename,
            owner_id=owner_id,
            status=TaskStatus.pending,
            parse_method=request.parse_method,
            lang=request.lang,
            created_at=_utc_now(),
            priority=request.priority,
        )

        async with self._lock:
            self._records[task_id] = record
            self._requests[task_id] = request
            self._pending_items[task_id] = QueueItem(task_id=task_id, cache_key=cache_key)
            self._prune_records_locked()
            self._persist_state_locked()

        await self._enqueue_task(task_id)
        return copy.deepcopy(record)

    async def get_task(
        self,
        task_id: str,
        owner_id: str | None = None,
        include_result: bool = True,
    ) -> TaskRecord | None:
        async with self._lock:
            record = self._records.get(task_id)
            if record is None:
                return None
            if owner_id and record.owner_id != owner_id:
                return None
            copied = copy.deepcopy(record)
            if not include_result:
                copied.result = None
            return copied

    async def list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        status: TaskStatus | str | None = None,
        owner_id: str | None = None,
        include_result: bool = True,
    ) -> TaskListPage:
        page = max(1, page)
        page_size = max(1, page_size)

        status_filter = self._normalize_status_filter(status)

        async with self._lock:
            records = list(self._records.values())

        records.sort(key=lambda row: row.created_at, reverse=True)
        if status_filter is not None:
            records = [row for row in records if row.status == status_filter]
        if owner_id:
            records = [row for row in records if row.owner_id == owner_id]

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size

        return TaskListPage(
            items=[
                self._copy_record(row, include_result=include_result)
                for row in records[start:end]
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stats(self, owner_id: str | None = None) -> TaskStats:
        async with self._lock:
            records = list(self._records.values())
        if owner_id:
            records = [row for row in records if row.owner_id == owner_id]

        stats = TaskStats()
        for record in records:
            if record.status == TaskStatus.pending:
                stats.pending += 1
            elif record.status == TaskStatus.processing:
                stats.processing += 1
            elif record.status == TaskStatus.completed:
                stats.completed += 1
            elif record.status == TaskStatus.failed:
                stats.failed += 1
        return stats

    async def get_queue_health(self, owner_id: str | None = None) -> QueueHealth:
        stats = await self.get_stats(owner_id=owner_id)
        async with self._lock:
            if owner_id:
                queued = sum(
                    1
                    for task_id in self._pending_items
                    if self._records.get(task_id) is not None
                    and self._records[task_id].owner_id == owner_id
                )
            else:
                queued = len(self._pending_items)
            paused = self._paused
        return QueueHealth(
            queued=queued,
            processing=stats.processing,
            workers=self.worker_count,
            paused=paused,
        )

    async def get_dashboard(self, recent_limit: int = 10, owner_id: str | None = None) -> dict:
        stats = await self.get_stats(owner_id=owner_id)
        queue_health = await self.get_queue_health(owner_id=owner_id)
        recent = await self.list_tasks(
            page=1,
            page_size=max(1, recent_limit),
            owner_id=owner_id,
            include_result=False,
        )
        async with self._lock:
            records = list(self._records.values())
        if owner_id:
            records = [row for row in records if row.owner_id == owner_id]

        finished = stats.completed + stats.failed
        success_rate = 0.0
        if finished > 0:
            success_rate = round(stats.completed / finished, 4)
        duration_values = [
            item.processing_duration_ms
            for item in records
            if item.processing_duration_ms is not None
            and item.status in {TaskStatus.completed, TaskStatus.failed}
        ]

        return {
            "stats": asdict(stats),
            "queue": asdict(queue_health),
            "success_rate": success_rate,
            "sla": self._duration_metrics(duration_values),
            "recent_tasks": [self._record_to_dict(item) for item in recent.items],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def cancel_task(self, task_id: str, owner_id: str | None = None) -> bool:
        async with self._lock:
            record = self._records.get(task_id)
            if record is None or record.status != TaskStatus.pending:
                return False
            if owner_id and record.owner_id != owner_id:
                return False

            record.status = TaskStatus.canceled
            record.completed_at = _utc_now()
            record.error_message = "Canceled by user"

            self._pending_items.pop(task_id, None)
            self._persist_state_locked()

        return True

    async def retry_task(self, task_id: str, owner_id: str | None = None) -> bool:
        async with self._lock:
            record = self._records.get(task_id)
            request = self._requests.get(task_id)
            if record is None or request is None:
                return False
            if owner_id and record.owner_id != owner_id:
                return False
            if record.status not in {TaskStatus.failed, TaskStatus.canceled}:
                return False
            if not os.path.exists(request.file_path):
                return False

            record.status = TaskStatus.pending
            record.error_message = None
            record.result = None
            record.started_at = None
            record.completed_at = None
            record.retry_count += 1
            record.processing_duration_ms = None

            cache_key = self._build_cache_key(request)
            self._pending_items[task_id] = QueueItem(task_id=task_id, cache_key=cache_key)
            self._persist_state_locked()

        await self._enqueue_task(task_id)
        return True

    async def _worker_loop(self, worker_index: int) -> None:
        while True:
            _, _, task_id = await self._queue.get()
            if task_id is None:
                self._queue.task_done()
                break

            await self._resume_event.wait()

            async with self._lock:
                record = self._records.get(task_id)
                queue_item = self._pending_items.pop(task_id, None)
                request = self._requests.get(task_id)

                if (
                    record is None
                    or request is None
                    or queue_item is None
                    or record.status == TaskStatus.canceled
                ):
                    self._persist_state_locked()
                    self._queue.task_done()
                    continue

                record.status = TaskStatus.processing
                record.started_at = _utc_now()
                record.processing_duration_ms = None
                self._persist_state_locked()

            started_at_perf = perf_counter()
            try:
                result = await self.parser_func(request.file_path, request)
                await self._mark_completed(task_id, result)
                await self._safe_cache_set(queue_item.cache_key, result)
                self._cleanup_temp_file(request.file_path)
                elapsed_ms = max(0, int((perf_counter() - started_at_perf) * 1000))
                logger.info(
                    "Task %s completed in %d ms (filename=%s)",
                    task_id,
                    elapsed_ms,
                    request.filename,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Task {task_id} failed: {exc}")
                await self._handle_failure(task_id, str(exc))
            finally:
                self._queue.task_done()

        logger.info(f"Task worker {worker_index} exited")

    async def _handle_failure(self, task_id: str, message: str) -> None:
        request: SubmitTaskRequest | None = None
        should_retry = False

        async with self._lock:
            record = self._records.get(task_id)
            request = self._requests.get(task_id)
            if record is None:
                return

            if (
                request is not None
                and record.retry_count < self.max_auto_retries
                and os.path.exists(request.file_path)
            ):
                record.retry_count += 1
                record.status = TaskStatus.pending
                record.error_message = message
                record.result = None
                record.started_at = None
                record.completed_at = None
                record.processing_duration_ms = None
                cache_key = self._build_cache_key(request)
                self._pending_items[task_id] = QueueItem(task_id=task_id, cache_key=cache_key)
                should_retry = True
            else:
                record.status = TaskStatus.failed
                record.error_message = message
                record.completed_at = _utc_now()
                record.processing_duration_ms = self._calculate_duration_ms(
                    record.started_at,
                    record.completed_at,
                )

            self._persist_state_locked()

        if should_retry and request is not None:
            if self.retry_delay_seconds > 0:
                await asyncio.sleep(self.retry_delay_seconds)
            await self._enqueue_task(task_id)

    async def _mark_completed(self, task_id: str, result: str) -> None:
        async with self._lock:
            record = self._records.get(task_id)
            if record is None:
                return
            record.status = TaskStatus.completed
            record.result = result
            record.error_message = None
            record.completed_at = _utc_now()
            record.processing_duration_ms = self._calculate_duration_ms(
                record.started_at,
                record.completed_at,
            )
            self._persist_state_locked()

    async def _enqueue_task(self, task_id: str) -> None:
        async with self._lock:
            request = self._requests.get(task_id)
            if request is None:
                return
            priority_value = -int(request.priority)
            self._enqueue_seq += 1
            enqueue_seq = self._enqueue_seq

        await self._queue.put((priority_value, enqueue_seq, task_id))

    def _prune_records_locked(self) -> None:
        if len(self._records) <= self.max_history:
            return

        active_statuses = {TaskStatus.pending, TaskStatus.processing}
        active_ids = {
            task_id
            for task_id, record in self._records.items()
            if record.status in active_statuses
        }
        finished_records = [
            record
            for record in self._records.values()
            if record.status not in active_statuses
        ]

        if len(active_ids) >= self.max_history and not finished_records:
            return

        finished_records.sort(key=lambda row: row.created_at, reverse=True)
        keep_finished = max(self.max_history - len(active_ids), 0)
        keep_ids = set(active_ids)
        keep_ids.update(record.task_id for record in finished_records[:keep_finished])

        for task_id in list(self._records.keys()):
            if task_id not in keep_ids:
                self._records.pop(task_id, None)
                self._requests.pop(task_id, None)
                self._pending_items.pop(task_id, None)

    def _persist_state_locked(self) -> None:
        if not self.state_file_path:
            return

        path = Path(self.state_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "paused": self._paused,
            "records": [
                self._record_to_persist_dict(item) for item in self._records.values()
            ],
            "requests": {
                task_id: asdict(request)
                for task_id, request in self._requests.items()
            },
            "pending": {
                task_id: asdict(item)
                for task_id, item in self._pending_items.items()
            },
        }

        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as target:
            json.dump(payload, target, ensure_ascii=False, indent=2)
        tmp_path.replace(path)

    def _load_state_locked(self) -> None:
        if not self.state_file_path:
            return

        path = Path(self.state_file_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as source:
                payload = json.load(source)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to load task state file: {exc}")
            return

        self._paused = bool(payload.get("paused", False))

        self._records.clear()
        for raw_record in payload.get("records", []):
            record = self._record_from_dict(raw_record)
            if record.status == TaskStatus.processing:
                record.status = TaskStatus.pending
            self._records[record.task_id] = record

        self._requests.clear()
        for task_id, raw_request in payload.get("requests", {}).items():
            self._requests[task_id] = SubmitTaskRequest(**raw_request)

        self._pending_items.clear()
        for task_id, raw_pending in payload.get("pending", {}).items():
            record = self._records.get(task_id)
            if record is None:
                continue
            if record.status in {TaskStatus.completed, TaskStatus.failed, TaskStatus.canceled}:
                continue
            if task_id not in self._requests:
                continue

            record.status = TaskStatus.pending
            self._pending_items[task_id] = QueueItem(
                task_id=raw_pending.get("task_id", task_id),
                cache_key=raw_pending.get("cache_key"),
            )

        self._prune_records_locked()

    @staticmethod
    def _record_to_dict(record: TaskRecord) -> dict:
        payload = asdict(record)
        payload["status"] = record.status.value
        payload["owner_id"] = record.owner_id
        payload["created_at"] = record.created_at.isoformat()
        payload["started_at"] = (
            record.started_at.isoformat() if record.started_at else None
        )
        payload["completed_at"] = (
            record.completed_at.isoformat() if record.completed_at else None
        )
        return payload

    def _record_to_persist_dict(self, record: TaskRecord) -> dict:
        payload = self._record_to_dict(record)
        result = payload.get("result")
        if result is None:
            return payload

        max_chars = self.state_result_max_chars
        if max_chars <= 0:
            payload["result"] = None
        elif isinstance(result, str) and len(result) > max_chars:
            payload["result"] = result[:max_chars]
        return payload

    @staticmethod
    def _record_from_dict(payload: dict) -> TaskRecord:
        def _parse_dt(value: str | None) -> datetime | None:
            if not value:
                return None
            parsed = datetime.fromisoformat(value)
            return _ensure_utc(parsed)

        return TaskRecord(
            task_id=payload["task_id"],
            filename=payload["filename"],
            owner_id=payload.get("owner_id", "anonymous"),
            status=TaskStatus(payload["status"]),
            parse_method=payload["parse_method"],
            lang=payload["lang"],
            created_at=_parse_dt(payload["created_at"]),
            started_at=_parse_dt(payload.get("started_at")),
            completed_at=_parse_dt(payload.get("completed_at")),
            result=payload.get("result"),
            error_message=payload.get("error_message"),
            cache_hit=bool(payload.get("cache_hit", False)),
            priority=int(payload.get("priority", 0)),
            retry_count=int(payload.get("retry_count", 0)),
            processing_duration_ms=(
                int(payload["processing_duration_ms"])
                if payload.get("processing_duration_ms") not in (None, "")
                else None
            ),
        )

    @staticmethod
    def _copy_record(record: TaskRecord, *, include_result: bool) -> TaskRecord:
        copied = copy.deepcopy(record)
        if not include_result:
            copied.result = None
        return copied

    @staticmethod
    def _calculate_duration_ms(
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> int | None:
        if started_at is None or completed_at is None:
            return None
        duration = int((completed_at - started_at).total_seconds() * 1000)
        return max(duration, 0)

    @staticmethod
    def _duration_metrics(values: list[int]) -> dict[str, int | float]:
        if not values:
            return {
                "count": 0,
                "avg_ms": 0,
                "p95_ms": 0,
                "max_ms": 0,
            }
        sorted_values = sorted(values)
        p95_index = max(ceil(len(sorted_values) * 0.95) - 1, 0)
        avg_ms = int(sum(sorted_values) / len(sorted_values))
        return {
            "count": len(sorted_values),
            "avg_ms": avg_ms,
            "p95_ms": sorted_values[p95_index],
            "max_ms": sorted_values[-1],
        }


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
