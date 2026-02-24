"""
PPTX Router Module

This module provides FastAPI endpoints for parsing and converting PPTX files to Markdown format.
It handles file uploads, validation, and processing of PPTX content using the Docling library.

The main functionality includes:
- PPTX file upload and validation
- Conversion of PPTX to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

import traceback
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.pptx_parser import pptx_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import PPTXParserConfig
from markio.services.sync_parse_service import (
    build_parse_response,
    run_uploaded_file_parser,
)
from markio.settings import settings
from markio.utils.logger_config import get_logger

router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir

logger = get_logger(__name__)


@router.post(
    "/parse_pptx_file",
    tags=["PPTX Parser"],
    summary="Parse and convert PPTX file to Markdown format",
    description="""
    This endpoint accepts a PPTX file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The PPTX file to be processed
        - config (PPTX_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - markdown_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid PPTX file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_pptx_file_endpoint(
    file: UploadFile = File(...),
    config: PPTXParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing PPTX files to Markdown format.
    """

    # Validate file type
    _validate_pptx_file(file=file)

    # Ensure output directory
    output_dir = resolve_parser_output_dir(
        requested_output_dir=config.output_dir or DEFAULT_OUTPUT_DIR,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        save_parsed_content=config.save_parsed_content,
    )

    logger.info(f"Starting to parse file: {file.filename}")
    started_at = perf_counter()

    # Parse the PPTX file
    try:
        parsed_content = await run_uploaded_file_parser(
            file=file,
            parser=pptx_parse_main,
            parser_kwargs={
                "save_parsed_content": config.save_parsed_content,
                "output_dir": output_dir,
            },
        )

        logger.info(f"PPTX file {file.filename} parsed successfully")

        return build_parse_response(
            parsed_content=parsed_content,
            parser="pptx",
            source_type="file",
            started_at=started_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"PPTX parsing error: {str(e)}")


def _validate_pptx_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid PPTX file.

    This function performs two types of validation:
    1. Content-Type validation: Checks if the file's MIME type is 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    2. File extension validation: Verifies the file has a .pptx extension

    Args:
        file (UploadFile): The PPTX file to validate

    Raises:
        HTTPException (400): If the file is not a valid PPTX file
            - Invalid content type
            - Invalid file extension
    """
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={".pptx"},
    )
