from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.runtime import get_task_manager
from markio.settings import settings
from markio.utils.file_utils import create_unique_temp_file, ensure_output_directory

router = APIRouter()


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
    if end_page is not None and end_page < start_page:
        raise HTTPException(
            status_code=400,
            detail="end_page must be greater than or equal to start_page",
        )

    temp_dir = ensure_output_directory(settings.task_upload_dir)
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    temp_file_path, _ = create_unique_temp_file(
        original_filename=os.path.basename(file.filename),
        temp_dir=temp_dir,
    )

    with open(temp_file_path, "wb") as target:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)

    request = SubmitTaskRequest(
        filename=file.filename,
        file_path=temp_file_path,
        parse_method=parse_method,
        lang=lang,
        save_parsed_content=save_parsed_content,
        save_middle_content=save_middle_content,
        output_dir=ensure_output_directory(output_dir),
        start_page=start_page,
        end_page=end_page,
        priority=priority,
    )

    task = await get_task_manager().submit(request)
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
    return jsonable_encoder(result)


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
    return jsonable_encoder(dashboard)


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
    task = await get_task_manager().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return jsonable_encoder(task)


@router.post("/tasks/{task_id}/cancel", tags=["Async Tasks"])
async def cancel_task(task_id: str):
    canceled = await get_task_manager().cancel_task(task_id)
    return jsonable_encoder({"task_id": task_id, "canceled": canceled})


@router.post("/tasks/{task_id}/retry", tags=["Async Tasks"])
async def retry_task(task_id: str):
    retried = await get_task_manager().retry_task(task_id)
    return jsonable_encoder({"task_id": task_id, "retried": retried})
