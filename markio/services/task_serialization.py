from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from markio.schemas.task_schemas import SubmitTaskRequest, TaskRecord, TaskStatus

from .task_time import parse_task_datetime, utc_now


def _parse_boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes"}


def task_record_to_dict(record: TaskRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["status"] = record.status.value
    payload["created_at"] = record.created_at.isoformat()
    payload["started_at"] = record.started_at.isoformat() if record.started_at else None
    payload["completed_at"] = (
        record.completed_at.isoformat() if record.completed_at else None
    )
    return payload


def task_record_from_dict(payload: Mapping[str, Any]) -> TaskRecord:
    return TaskRecord(
        task_id=str(payload["task_id"]),
        filename=str(payload["filename"]),
        owner_id=str(payload.get("owner_id", "anonymous") or "anonymous"),
        status=TaskStatus(str(payload["status"])),
        parse_method=str(payload["parse_method"]),
        lang=str(payload["lang"]),
        created_at=parse_task_datetime(payload.get("created_at")) or utc_now(),
        started_at=parse_task_datetime(payload.get("started_at")),
        completed_at=parse_task_datetime(payload.get("completed_at")),
        result=payload.get("result"),
        error_message=payload.get("error_message"),
        cache_hit=_parse_boolish(payload.get("cache_hit", False)),
        priority=int(payload.get("priority", 0)),
        retry_count=int(payload.get("retry_count", 0)),
        processing_duration_ms=(
            int(payload["processing_duration_ms"])
            if payload.get("processing_duration_ms") not in (None, "")
            else None
        ),
    )


def submit_task_request_to_dict(request: SubmitTaskRequest) -> dict[str, Any]:
    return asdict(request)


def submit_task_request_from_dict(payload: Mapping[str, Any]) -> SubmitTaskRequest:
    return SubmitTaskRequest(
        filename=str(payload.get("filename", "")),
        file_path=str(payload.get("file_path", "")),
        owner_id=str(payload.get("owner_id", "anonymous") or "anonymous"),
        parse_method=str(payload.get("parse_method", "auto")),
        lang=str(payload.get("lang", "ch")),
        save_parsed_content=_parse_boolish(payload.get("save_parsed_content", False)),
        save_middle_content=_parse_boolish(payload.get("save_middle_content", False)),
        output_dir=str(payload.get("output_dir", "outputs")),
        start_page=int(payload.get("start_page", 0)),
        end_page=(
            int(payload["end_page"])
            if payload.get("end_page") not in (None, "")
            else None
        ),
        priority=int(payload.get("priority", 0)),
    )
