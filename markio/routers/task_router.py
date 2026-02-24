from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder

from markio.schemas.parsers_schemas import PDF_PARSE_LANG, PDF_PARSE_TYPE
from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services import parser_registry
from markio.services.runtime import get_task_manager
from markio.settings import settings
from markio.utils.file_utils import create_unique_temp_file, ensure_output_directory

router = APIRouter()
logger = logging.getLogger(__name__)

TASK_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
PDF_PARSE_METHODS = {item.value for item in PDF_PARSE_TYPE}
PDF_LANGS = {item.value for item in PDF_PARSE_LANG}


def _cleanup_temp_upload(file_path: str) -> None:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        logger.warning("Failed to clean temporary upload file: %s", file_path)


def _validate_task_id(task_id: str) -> None:
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task_id format: expected 32 lowercase hex chars",
        )


def _resolve_task_output_dir(output_dir: str) -> str:
    base_dir = Path(settings.output_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    requested = Path(output_dir or settings.output_dir).expanduser()
    if requested.is_absolute():
        resolved = requested.resolve()
    else:
        resolved = (Path.cwd() / requested).resolve()

    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output_dir: must be within {base_dir}",
        ) from exc

    resolved.mkdir(parents=True, exist_ok=True)
    return str(resolved)


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
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_extension = Path(file.filename).suffix.lower()
    if not parser_registry.get_parser_for_extension(file_extension):
        supported_types = ", ".join(parser_registry.get_supported_extensions())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types are: {supported_types}",
        )

    if not parser_registry.is_expected_mime_type(file_extension, file.content_type):
        expected = (
            ", ".join(parser_registry.get_expected_mime_types(file_extension))
            or "unknown"
        )
        logger.warning(
            "Task upload MIME mismatch: filename=%s extension=%s content_type=%s expected=%s",
            file.filename,
            file_extension,
            file.content_type,
            expected,
        )

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

    safe_output_dir = _resolve_task_output_dir(output_dir)
    max_upload_size = int(settings.task_max_upload_size_bytes)

    temp_dir = ensure_output_directory(settings.task_upload_dir)
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    temp_file_path, _ = create_unique_temp_file(
        original_filename=os.path.basename(file.filename),
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
                if bytes_written > max_upload_size:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Uploaded file is too large. "
                            f"Maximum allowed size is {max_upload_size} bytes."
                        ),
                    )
                target.write(chunk)
    except Exception:
        _cleanup_temp_upload(temp_file_path)
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
        _cleanup_temp_upload(temp_file_path)
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
async def get_task(task_id: str):
    _validate_task_id(task_id)
    task = await get_task_manager().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return jsonable_encoder(task)


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
