from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder

from markio.routers._request_guards import (
    cleanup_file_safely,
    enforce_upload_size,
    resolve_strict_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import PDF_PARSE_LANG, PDF_PARSE_TYPE
from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.runtime import get_task_manager
from markio.settings import settings
from markio.utils.file_utils import create_unique_temp_file, ensure_output_directory

router = APIRouter()
logger = logging.getLogger(__name__)

TASK_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
PDF_PARSE_METHODS = {item.value for item in PDF_PARSE_TYPE}
PDF_LANGS = {item.value for item in PDF_PARSE_LANG}


def _validate_task_id(task_id: str) -> None:
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task_id format: expected 32 lowercase hex chars",
        )


def _sanitize_task_list_payload(items: list[dict]) -> list[dict]:
    for item in items:
        item.pop("result", None)
    return items


@router.post("/tasks/submit", tags=["Async Tasks"])
async def submit_task(
    file: UploadFile = File(...),
    parse_method: str = Form("auto"),
    lang: str = Form("ch"),
    priority: int = Form(0, ge=-10, le=100),
    save_parsed_content: bool = Form(False),
    save_middle_content: bool = Form(False),
    output_dir: str = Form(settings.output_dir),
    start_page: int = Form(0, ge=0),
    end_page: int | None = Form(None, ge=0),
):
    file_extension = validate_upload_file(file, logger=logger)

    if file_extension == ".pdf":
        if parse_method not in PDF_PARSE_METHODS:
            allowed_methods = ", ".join(sorted(PDF_PARSE_METHODS))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_method: {parse_method}. Allowed: {allowed_methods}",
            )
        if lang not in PDF_LANGS:
            allowed_langs = ", ".join(sorted(PDF_LANGS))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid lang: {lang}. Allowed: {allowed_langs}",
            )

    if end_page is not None and end_page < start_page:
        raise HTTPException(
            status_code=400,
            detail="end_page must be greater than or equal to start_page",
        )

    safe_output_dir = resolve_strict_output_dir(output_dir, settings.output_dir)
    max_upload_size = int(settings.task_max_upload_size_bytes)

    temp_dir = ensure_output_directory(settings.task_upload_dir)
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    temp_file_path, _ = create_unique_temp_file(
        original_filename=file.filename,
        temp_dir=temp_dir,
    )

    bytes_written = 0
    try:
        with open(temp_file_path, "wb") as target:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                enforce_upload_size(
                    bytes_written=bytes_written,
                    max_bytes=max_upload_size,
                )
                target.write(chunk)
    except Exception:
        cleanup_file_safely(temp_file_path, logger=logger)
        raise

    request = SubmitTaskRequest(
        filename=file.filename,
        file_path=temp_file_path,
        parse_method=parse_method,
        lang=lang,
        save_parsed_content=save_parsed_content,
        save_middle_content=save_middle_content,
        output_dir=safe_output_dir,
        start_page=start_page,
        end_page=end_page,
        priority=priority,
    )

    try:
        task = await get_task_manager().submit(request)
    except Exception:
        cleanup_file_safely(temp_file_path, logger=logger)
        raise

    return jsonable_encoder(task)


@router.get("/tasks", tags=["Async Tasks"])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: TaskStatus | None = Query(None),
):
    result = await get_task_manager().list_tasks(
        page=page,
        page_size=page_size,
        status=status,
    )
    payload = jsonable_encoder(result)
    payload["items"] = _sanitize_task_list_payload(payload.get("items", []))
    return payload


@router.get("/tasks/stats", tags=["Async Tasks"])
async def get_task_stats():
    stats = await get_task_manager().get_stats()
    return jsonable_encoder(stats)


@router.get("/tasks/queue", tags=["Async Tasks"])
async def get_queue_health():
    health = await get_task_manager().get_queue_health()
    return jsonable_encoder(health)


@router.get("/tasks/dashboard", tags=["Async Tasks"])
async def get_dashboard(recent_limit: int = Query(10, ge=1, le=100)):
    dashboard = await get_task_manager().get_dashboard(recent_limit=recent_limit)
    payload = jsonable_encoder(dashboard)
    payload["recent_tasks"] = _sanitize_task_list_payload(
        payload.get("recent_tasks", [])
    )
    return payload


@router.post("/tasks/queue/pause", tags=["Async Tasks"])
async def pause_queue():
    await get_task_manager().pause_queue()
    health = await get_task_manager().get_queue_health()
    return jsonable_encoder({"paused": health.paused})


@router.post("/tasks/queue/resume", tags=["Async Tasks"])
async def resume_queue():
    await get_task_manager().resume_queue()
    health = await get_task_manager().get_queue_health()
    return jsonable_encoder({"paused": health.paused})


@router.get("/tasks/{task_id}", tags=["Async Tasks"])
async def get_task(
    task_id: str,
    include_result: bool = Query(True),
    max_result_chars: int | None = Query(None, ge=1),
):
    _validate_task_id(task_id)
    task = await get_task_manager().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    payload = jsonable_encoder(task)

    result_truncated = False
    if not include_result:
        payload.pop("result", None)
    elif (
        max_result_chars is not None
        and isinstance(payload.get("result"), str)
        and len(payload["result"]) > max_result_chars
    ):
        payload["result"] = payload["result"][:max_result_chars]
        result_truncated = True

    payload["result_truncated"] = result_truncated
    return payload


@router.post("/tasks/{task_id}/cancel", tags=["Async Tasks"])
async def cancel_task(task_id: str):
    _validate_task_id(task_id)
    task = await get_task_manager().get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    canceled = await get_task_manager().cancel_task(task_id)
    if not canceled:
        raise HTTPException(
            status_code=409,
            detail="Task cannot be canceled in current status",
        )

    return jsonable_encoder({"task_id": task_id, "canceled": canceled})


@router.post("/tasks/{task_id}/retry", tags=["Async Tasks"])
async def retry_task(task_id: str):
    _validate_task_id(task_id)
    task = await get_task_manager().get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    retried = await get_task_manager().retry_task(task_id)
    if not retried:
        raise HTTPException(
            status_code=409,
            detail="Task cannot be retried in current status",
        )

    return jsonable_encoder({"task_id": task_id, "retried": retried})
