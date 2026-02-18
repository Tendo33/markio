from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

import markio.services.parser_registry as parser_registry
from markio.parsers import pdf_parser
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.settings import settings


async def parse_local_file(file_path: str, request: SubmitTaskRequest) -> str:
    extension = Path(request.filename).suffix.lower()

    if extension == ".pdf":
        return await _parse_pdf(file_path=file_path, request=request)

    parser = parser_registry.get_parser_for_extension(extension)
    if parser is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {extension}",
        )

    return await parser(
        resource_path=file_path,
        save_parsed_content=request.save_parsed_content,
        output_dir=request.output_dir,
    )


async def _parse_pdf(file_path: str, request: SubmitTaskRequest) -> str:
    return await pdf_parser.pdf_parse_main(
        resource_path=file_path,
        parse_method=request.parse_method,
        lang=request.lang,
        save_parsed_content=request.save_parsed_content,
        save_middle_content=request.save_middle_content,
        output_dir=request.output_dir,
        start_page=request.start_page,
        end_page=request.end_page,
        backend=settings.pdf_parse_engine,
        server_url=settings.vlm_server_url,
    )
