from __future__ import annotations

import os
from tempfile import gettempdir
from time import perf_counter
from typing import Any, Awaitable, Callable, Mapping
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.middlewares.trace_middleware.ctx import TraceCtx
from markio.schemas.api_schemas import ParseResponse
from markio.settings import settings
from markio.utils.file_utils import (
    create_unique_temp_file,
    resolve_path_within_base,
    sanitize_filename,
)

_UPLOAD_CHUNK_SIZE = 1024 * 1024
ParseErrorHandler = Callable[[Exception], HTTPException]


def _enforce_upload_size(*, bytes_written: int, max_bytes: int) -> None:
    if bytes_written <= max_bytes:
        return
    raise HTTPException(
        status_code=413,
        detail=(
            "Uploaded file is too large. "
            f"Maximum allowed size is {max_bytes} bytes."
        ),
    )


async def run_uploaded_file_parser(
    *,
    file: UploadFile,
    parser,
    parser_args: tuple[Any, ...] = (),
    parser_kwargs: dict[str, Any] | None = None,
) -> str:
    temp_file_path = ""
    parser_kwargs = parser_kwargs or {}

    try:
        temp_dir = gettempdir()
        original_filename = sanitize_filename(file.filename)
        temp_file_path, _ = create_unique_temp_file(original_filename, temp_dir)
        try:
            resolve_path_within_base(temp_dir, temp_file_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid upload filename path",
            ) from exc
        max_upload_size = int(settings.task_max_upload_size_bytes)
        bytes_written = 0

        with open(temp_file_path, "wb") as temp_file:
            while True:
                chunk = await file.read(_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                bytes_written += len(chunk)
                _enforce_upload_size(
                    bytes_written=bytes_written,
                    max_bytes=max_upload_size,
                )
                temp_file.write(chunk)

        return await parser(temp_file_path, *parser_args, **parser_kwargs)
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def build_parse_response(
    *,
    parsed_content: str,
    parser: str,
    source_type: str,
    started_at: float,
) -> JSONResponse:
    request_id = TraceCtx.get_id() or uuid4().hex
    duration_ms = max(0, int((perf_counter() - started_at) * 1000))

    payload = ParseResponse(
        parsed_content=parsed_content,
        parser=parser,
        source_type=source_type,
        request_id=request_id,
        duration_ms=duration_ms,
    )
    return JSONResponse(payload.model_dump(), status_code=200)


async def execute_parse_request(
    *,
    parse_fn: Callable[[], Awaitable[str]],
    parser: str,
    source_type: str,
    source_name: str,
    started_at: float,
    logger,
    handled_errors: Mapping[type[Exception], ParseErrorHandler] | None = None,
) -> JSONResponse:
    try:
        parsed_content = await parse_fn()
        logger.info(f"{parser} parsed successfully: {source_name}")
        return build_parse_response(
            parsed_content=parsed_content,
            parser=parser,
            source_type=source_type,
            started_at=started_at,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - branches covered via routers
        for exception_type, handler in (handled_errors or {}).items():
            if isinstance(exc, exception_type):
                raise handler(exc) from exc
        logger.exception(f"Error occurred while parsing {source_name}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
