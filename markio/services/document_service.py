from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from markio.parsers import (
    doc_parser,
    docx_parser,
    epub_parser,
    html_parser,
    image_parser,
    pdf_parser,
    ppt_parser,
    pptx_parser,
    xlsx_parser,
)
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.settings import settings


EXTENSION_PARSERS = {
    ".doc": doc_parser.doc_parse_main,
    ".docx": docx_parser.docx_parse_main,
    ".ppt": ppt_parser.ppt_parse_main,
    ".pptx": pptx_parser.pptx_parse_main,
    ".xlsx": xlsx_parser.xlsx_parse_main,
    ".html": html_parser.html_parse_main,
    ".htm": html_parser.html_parse_main,
    ".epub": epub_parser.epub_parse_main,
    ".png": image_parser.image_parse_main,
    ".jpg": image_parser.image_parse_main,
    ".jpeg": image_parser.image_parse_main,
}


async def parse_local_file(file_path: str, request: SubmitTaskRequest) -> str:
    extension = Path(request.filename).suffix.lower()

    if extension == ".pdf":
        return await _parse_pdf(file_path=file_path, request=request)

    parser = EXTENSION_PARSERS.get(extension)
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
