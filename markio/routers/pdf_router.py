"""
PDF Router Module

This module provides FastAPI endpoints for parsing and converting PDF files to Markdown format.
It handles file uploads, validation, and processing of PDF content using the Docling library.

The main functionality includes:
- PDF file upload and validation
- Conversion of PDF to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.pdf_parser import pdf_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import PDFParserConfig
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
    "/parse_pdf_file",
    tags=["PDF Parser"],
    summary="Parse and convert PDF file to Markdown format",
    description="""
    This endpoint accepts a PDF file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The PDF file to be processed
        - config (PDF_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid PDF file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_pdf_file_endpoint(
    file: UploadFile = File(...),
    config: PDFParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing PDF files to Markdown format.
    """
    logger.info(f"Received PDF parsing request for file: {file.filename}")

    # Validate file type
    _validate_pdf_file(file=file)

    # Ensure output directory exists and is constrained
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
    pdf_parse_engine = settings.pdf_parse_engine
    logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

    async def parse_pdf(temp_path: str) -> str:
        return await pdf_parse_main(
            resource_path=temp_path,
            parse_method=config.parse_method,
            lang=config.lang,
            save_parsed_content=config.save_parsed_content,
            save_middle_content=config.save_middle_content,
            output_dir=output_dir,
            start_page=config.start_page,
            end_page=config.end_page,
            backend=pdf_parse_engine,
            server_url=settings.vlm_server_url,
        )

    return await execute_parse_request(
        parse_fn=lambda: run_uploaded_file_parser(file=file, parser=parse_pdf),
        parser="pdf",
        source_type="file",
        source_name=file.filename or "pdf_upload",
        started_at=started_at,
        logger=logger,
        handled_errors={
            ValueError: lambda error: HTTPException(
                status_code=400,
                detail=f"Configuration error: {error}",
            )
        },
    )


def _validate_pdf_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid PDF file.

    This function performs two types of validation:
    1. Content-Type validation: Checks if the file's MIME type is 'application/pdf'
    2. File extension validation: Verifies the file has a .pdf extension

    Args:
        file (UploadFile): The PDF file to validate

    Raises:
        HTTPException (400): If the file is not a valid PDF file
            - Invalid content type
            - Invalid file extension
    """
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={".pdf"},
    )
