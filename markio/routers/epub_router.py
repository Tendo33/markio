"""
EPUB Router Module

This module provides FastAPI endpoints for parsing and converting EPUB files to Markdown format.
It handles file uploads, validation, and processing of EPUB content using the Docling library.

The main functionality includes:
- EPUB file upload and validation
- Conversion of EPUB to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

import traceback
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.epub_parser import epub_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import EPUBParserConfig
from markio.services.sync_parse_service import (
    build_parse_response,
    run_uploaded_file_parser,
)
from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


@router.post(
    "/parse_epub_file",
    tags=["EPUB Parser"],
    summary="Parse and convert EPUB file to Markdown format",
    description="""
    This endpoint accepts an EPUB file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The EPUB file to be processed
        - config (EPUB_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid EPUB file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_epub_file_endpoint(
    file: UploadFile = File(...),
    config: EPUBParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing EPUB files to Markdown format.
    """
    # Validate file type
    _validate_epub_file(file=file)

    # Ensure output directory is strict and controlled
    output_dir = resolve_parser_output_dir(
        requested_output_dir=config.output_dir or DEFAULT_OUTPUT_DIR,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        save_parsed_content=config.save_parsed_content,
    )

    logger.info(f"Starting to parse file: {file.filename}")
    started_at = perf_counter()

    # Parse the EPUB file
    try:
        parsed_content = await run_uploaded_file_parser(
            file=file,
            parser=epub_parse_main,
            parser_kwargs={
                "save_parsed_content": config.save_parsed_content,
                "output_dir": output_dir,
            },
        )

        logger.info(f"EPUB file {file.filename} parsed successfully")

        return build_parse_response(
            parsed_content=parsed_content,
            parser="epub",
            source_type="file",
            started_at=started_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"EPUB parsing error: {str(e)}")


def _validate_epub_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid EPUB file.

    This function performs two types of validation:
    1. Content-Type validation: Checks if the file's MIME type is either 'application/epub+zip' or 'application/zip'
    2. File extension validation: Verifies the file has a .epub extension

    Args:
        file (UploadFile): The EPUB file to validate

    Raises:
        HTTPException (400): If the file is not a valid EPUB file
            - Invalid content type
            - Invalid file extension
    """
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={".epub"},
    )
