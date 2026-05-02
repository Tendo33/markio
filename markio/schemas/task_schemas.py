from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


@dataclass
class SubmitTaskRequest:
    filename: str
    file_path: str
    owner_id: str = ""
    parse_method: str = "auto"
    lang: str = "ch"
    save_parsed_content: bool = False
    save_middle_content: bool = False
    output_dir: str = "outputs"
    start_page: int = 0
    end_page: int | None = None
    priority: int = 0


@dataclass
class TaskRecord:
    task_id: str
    filename: str
    owner_id: str
    status: TaskStatus
    parse_method: str
    lang: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error_message: str | None = None
    cache_hit: bool = False
    priority: int = 0
    retry_count: int = 0
    processing_duration_ms: int | None = None


@dataclass
class TaskStats:
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    canceled: int = 0


@dataclass
class TaskListPage:
    items: list[TaskRecord] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


@dataclass
class QueueHealth:
    queued: int
    processing: int
    workers: int
    paused: bool = False
