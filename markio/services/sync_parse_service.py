from __future__ import annotations

import os
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from markio.middlewares.trace_middleware.ctx import TraceCtx
from markio.routers._request_guards import enforce_upload_size
from markio.schemas.api_schemas import ParseResponse
from markio.settings import settings
from markio.utils.file_utils import create_unique_temp_file

_UPLOAD_CHUNK_SIZE = 1024 * 1024


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
        temp_dir = os.path.dirname(NamedTemporaryFile().name)
        original_filename = os.path.basename(file.filename)
        temp_file_path, _ = create_unique_temp_file(original_filename, temp_dir)
        max_upload_size = int(settings.task_max_upload_size_bytes)
        bytes_written = 0

        with open(temp_file_path, "wb") as temp_file:
            while True:
                chunk = await file.read(_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                bytes_written += len(chunk)
                enforce_upload_size(
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
