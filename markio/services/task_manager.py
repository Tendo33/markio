from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from markio.schemas.task_schemas import (
    QueueHealth,
    SubmitTaskRequest,
    TaskListPage,
    TaskRecord,
    TaskStats,
    TaskStatus,
)

logger = logging.getLogger(__name__)

ParserFunc = Callable[[str, SubmitTaskRequest], Awaitable[str]]
CacheGetter = Callable[[str], Awaitable[str | None]]
CacheSetter = Callable[[str, str], Awaitable[bool]]


@dataclass
class QueueItem:
    task_id: str
    cache_key: str | None = None


class AsyncTaskManager:
    def __init__(
        self,
        worker_count: int = 1,
        parser_func: ParserFunc | None = None,
        cache_getter: CacheGetter | None = None,
        cache_setter: CacheSetter | None = None,
        max_history: int = 500,
        state_file_path: str | None = None,
        max_auto_retries: int = 0,
        retry_delay_seconds: float = 0.0,
    ) -> None:
        if parser_func is None:
            from markio.services.document_service import parse_local_file

            parser_func = parse_local_file

        self.worker_count = max(1, worker_count)
        self.max_history = max(20, max_history)
        self.parser_func = parser_func
        self.cache_getter = cache_getter
        self.cache_setter = cache_setter
        self.state_file_path = state_file_path
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

        task_id = uuid.uuid4().hex
        cache_key = self._build_cache_key(request)

        cache_allowed = not (
            request.save_parsed_content or request.save_middle_content
        )
        if cache_allowed and self.cache_getter and cache_key:
            cached_value = await self._safe_cache_get(cache_key)
            if cached_value:
                now = datetime.utcnow()
                record = TaskRecord(
                    task_id=task_id,
                    filename=request.filename,
                    status=TaskStatus.completed,
                    parse_method=request.parse_method,
                    lang=request.lang,
                    created_at=now,
                    started_at=now,
                    completed_at=now,
                    result=cached_value,
                    cache_hit=True,
                    priority=request.priority,
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
            status=TaskStatus.pending,
            parse_method=request.parse_method,
            lang=request.lang,
            created_at=datetime.utcnow(),
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

    async def get_task(self, task_id: str) -> TaskRecord | None:
        async with self._lock:
            record = self._records.get(task_id)
            return None if record is None else copy.deepcopy(record)

    async def list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        status: TaskStatus | str | None = None,
    ) -> TaskListPage:
        page = max(1, page)
        page_size = max(1, page_size)

        status_filter = self._normalize_status_filter(status)

        async with self._lock:
            records = list(self._records.values())

        records.sort(key=lambda row: row.created_at, reverse=True)
        if status_filter is not None:
            records = [row for row in records if row.status == status_filter]

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size

        return TaskListPage(
            items=[copy.deepcopy(row) for row in records[start:end]],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stats(self) -> TaskStats:
        async with self._lock:
            records = list(self._records.values())

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

    async def get_queue_health(self) -> QueueHealth:
        stats = await self.get_stats()
        async with self._lock:
            queued = len(self._pending_items)
            paused = self._paused
        return QueueHealth(
            queued=queued,
            processing=stats.processing,
            workers=self.worker_count,
            paused=paused,
        )

    async def get_dashboard(self, recent_limit: int = 10) -> dict:
        stats = await self.get_stats()
        queue_health = await self.get_queue_health()
        recent = await self.list_tasks(page=1, page_size=max(1, recent_limit))

        finished = stats.completed + stats.failed
        success_rate = 0.0
        if finished > 0:
            success_rate = round(stats.completed / finished, 4)

        return {
            "stats": asdict(stats),
            "queue": asdict(queue_health),
            "success_rate": success_rate,
            "recent_tasks": [self._record_to_dict(item) for item in recent.items],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def cancel_task(self, task_id: str) -> bool:
        async with self._lock:
            record = self._records.get(task_id)
            if record is None or record.status != TaskStatus.pending:
                return False

            record.status = TaskStatus.canceled
            record.completed_at = datetime.utcnow()
            record.error_message = "Canceled by user"

            self._pending_items.pop(task_id, None)
            self._persist_state_locked()

        return True

    async def retry_task(self, task_id: str) -> bool:
        async with self._lock:
            record = self._records.get(task_id)
            request = self._requests.get(task_id)
            if record is None or request is None:
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
                record.started_at = datetime.utcnow()
                self._persist_state_locked()

            try:
                result = await self.parser_func(request.file_path, request)
                await self._mark_completed(task_id, result)
                await self._safe_cache_set(queue_item.cache_key, result)
                self._cleanup_temp_file(request.file_path)
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
                cache_key = self._build_cache_key(request)
                self._pending_items[task_id] = QueueItem(task_id=task_id, cache_key=cache_key)
                should_retry = True
            else:
                record.status = TaskStatus.failed
                record.error_message = message
                record.completed_at = datetime.utcnow()

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
            record.completed_at = datetime.utcnow()
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

    def _build_cache_key(self, request: SubmitTaskRequest) -> str:
        try:
            hasher = hashlib.sha256()
            with open(request.file_path, "rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    hasher.update(chunk)
        except FileNotFoundError:
            return ""

        options = {
            "filename": request.filename,
            "parse_method": request.parse_method,
            "lang": request.lang,
            "save_middle_content": request.save_middle_content,
            "start_page": request.start_page,
            "end_page": request.end_page,
            "engine": os.getenv("PDF_PARSE_ENGINE", "pipeline"),
        }
        options_digest = hashlib.sha256(
            json.dumps(options, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        return f"markio:result:{hasher.hexdigest()}:{options_digest}"

    async def _safe_cache_get(self, cache_key: str) -> str | None:
        try:
            result = await self.cache_getter(cache_key)  # type: ignore[misc]
            if isinstance(result, str) and result:
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache get failed for {cache_key}: {exc}")
        return None

    async def _safe_cache_set(self, cache_key: str | None, value: str) -> None:
        if not cache_key or not self.cache_setter:
            return
        try:
            await self.cache_setter(cache_key, value)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache set failed for {cache_key}: {exc}")

    def _persist_state_locked(self) -> None:
        if not self.state_file_path:
            return

        path = Path(self.state_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "paused": self._paused,
            "records": [self._record_to_dict(item) for item in self._records.values()],
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
        payload["created_at"] = record.created_at.isoformat()
        payload["started_at"] = (
            record.started_at.isoformat() if record.started_at else None
        )
        payload["completed_at"] = (
            record.completed_at.isoformat() if record.completed_at else None
        )
        return payload

    @staticmethod
    def _record_from_dict(payload: dict) -> TaskRecord:
        return TaskRecord(
            task_id=payload["task_id"],
            filename=payload["filename"],
            status=TaskStatus(payload["status"]),
            parse_method=payload["parse_method"],
            lang=payload["lang"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            started_at=(
                datetime.fromisoformat(payload["started_at"])
                if payload.get("started_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(payload["completed_at"])
                if payload.get("completed_at")
                else None
            ),
            result=payload.get("result"),
            error_message=payload.get("error_message"),
            cache_hit=bool(payload.get("cache_hit", False)),
            priority=int(payload.get("priority", 0)),
            retry_count=int(payload.get("retry_count", 0)),
        )

    @staticmethod
    def _normalize_status_filter(status: TaskStatus | str | None) -> TaskStatus | None:
        if status is None:
            return None
        if isinstance(status, TaskStatus):
            return status
        return TaskStatus(status)

    @staticmethod
    def _cleanup_temp_file(file_path: str) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to clean up temp file {file_path}: {exc}")
