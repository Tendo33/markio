"""
DOCX Router Module

This module provides FastAPI endpoints for parsing and converting DOCX files to Markdown format.
It handles file uploads, validation, and processing of DOCX content using the Docling library.

The main functionality includes:
- DOCX file upload and validation
- Conversion of DOCX to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

from time import perf_counter

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.docx_parser import docx_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import DOCXParserConfig
from markio.services.sync_parse_service import (
    execute_parse_request,
    run_uploaded_file_parser,
)
from markio.settings import settings
from markio.utils.file_utils import (
    calculate_file_size,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


@router.post(
    "/parse_docx_file",
    tags=["DOCX Parser"],
    summary="Parse and convert DOCX file to Markdown format",
    description="""
    This endpoint accepts a DOCX file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The DOCX file to be processed
        - config (DOCX_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - markdown_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid DOCX file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_docx_endpoint(
    file: UploadFile = File(...),
    config: DOCXParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing DOCX files to Markdown format.
    """
    logger.info(f"Received DOCX parsing request for file: {file.filename}")

    # Validate file type
    _validate_docx_file(file=file)

    # Ensure output directory is strict and controlled
    output_dir = resolve_parser_output_dir(
        requested_output_dir=config.output_dir or DEFAULT_OUTPUT_DIR,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        save_parsed_content=config.save_parsed_content,
    )
    logger.debug(f"Output directory ensured: {output_dir}")

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )
    started_at = perf_counter()
    return await execute_parse_request(
        parse_fn=lambda: run_uploaded_file_parser(
            file=file,
            parser=docx_parse_main,
            parser_kwargs={
                "save_parsed_content": config.save_parsed_content,
                "output_dir": output_dir,
            },
        ),
        parser="docx",
        source_type="file",
        source_name=file.filename or "docx_upload",
        started_at=started_at,
        logger=logger,
    )


def _validate_docx_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid DOCX file.

    This function performs two types of validation:
    1. Content-Type validation: Checks if the file's MIME type is 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    2. File extension validation: Verifies the file has a .docx extension

    Args:
        file (UploadFile): The DOCX file to validate

    Raises:
        HTTPException (400): If the file is not a valid DOCX file
            - Invalid content type
            - Invalid file extension
    """
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={".docx"},
    )
