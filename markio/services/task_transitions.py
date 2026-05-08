from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from markio.schemas.task_schemas import TaskStatus

from .task_time import calculate_duration_ms


@dataclass(frozen=True)
class TaskTransition:
    status: TaskStatus
    started_at: datetime | None
    completed_at: datetime | None
    result: str | None
    error_message: str | None
    retry_count: int
    processing_duration_ms: int | None


def processing_transition(
    *,
    current_retry_count: int,
    started_at: datetime,
) -> TaskTransition:
    return TaskTransition(
        status=TaskStatus.processing,
        started_at=started_at,
        completed_at=None,
        result=None,
        error_message=None,
        retry_count=current_retry_count,
        processing_duration_ms=None,
    )


def completion_transition(
    *,
    current_retry_count: int,
    started_at: datetime | None,
    completed_at: datetime,
    result: str,
) -> TaskTransition:
    return TaskTransition(
        status=TaskStatus.completed,
        started_at=started_at,
        completed_at=completed_at,
        result=result,
        error_message=None,
        retry_count=current_retry_count,
        processing_duration_ms=calculate_duration_ms(started_at, completed_at),
    )


def failure_transition(
    *,
    current_retry_count: int,
    started_at: datetime | None,
    completed_at: datetime,
    message: str,
) -> TaskTransition:
    return TaskTransition(
        status=TaskStatus.failed,
        started_at=started_at,
        completed_at=completed_at,
        result=None,
        error_message=message,
        retry_count=current_retry_count,
        processing_duration_ms=calculate_duration_ms(started_at, completed_at),
    )


def cancel_transition(
    *,
    current_retry_count: int,
    completed_at: datetime,
    message: str = "Canceled by user",
) -> TaskTransition:
    return TaskTransition(
        status=TaskStatus.canceled,
        started_at=None,
        completed_at=completed_at,
        result=None,
        error_message=message,
        retry_count=current_retry_count,
        processing_duration_ms=None,
    )


def retry_transition(
    *,
    current_retry_count: int,
    error_message: str | None = None,
) -> TaskTransition:
    return TaskTransition(
        status=TaskStatus.pending,
        started_at=None,
        completed_at=None,
        result=None,
        error_message=error_message,
        retry_count=current_retry_count + 1,
        processing_duration_ms=None,
    )


def transition_to_record_fields(transition: TaskTransition) -> dict[str, object]:
    return {
        "status": transition.status,
        "started_at": transition.started_at,
        "completed_at": transition.completed_at,
        "result": transition.result,
        "error_message": transition.error_message,
        "retry_count": transition.retry_count,
        "processing_duration_ms": transition.processing_duration_ms,
    }


def transition_to_storage_fields(transition: TaskTransition) -> dict[str, str]:
    return {
        "status": transition.status.value,
        "started_at": (
            transition.started_at.isoformat() if transition.started_at else ""
        ),
        "completed_at": (
            transition.completed_at.isoformat() if transition.completed_at else ""
        ),
        "error_message": transition.error_message or "",
        "retry_count": str(transition.retry_count),
        "processing_duration_ms": (
            ""
            if transition.processing_duration_ms is None
            else str(transition.processing_duration_ms)
        ),
    }
