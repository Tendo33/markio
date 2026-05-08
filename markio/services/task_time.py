from __future__ import annotations

from datetime import datetime, timezone
from math import ceil


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_task_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(datetime.fromisoformat(str(value)))
    except ValueError:
        return None


def calculate_duration_ms(
    started_at: datetime | None,
    completed_at: datetime | None,
) -> int | None:
    if started_at is None or completed_at is None:
        return None
    duration = int((completed_at - started_at).total_seconds() * 1000)
    return max(duration, 0)


def duration_metrics(values: list[int]) -> dict[str, int | float]:
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
