"""
HTML Router Module

This module provides FastAPI endpoints for parsing and converting HTML files to Markdown format.
It handles file uploads, validation, and processing of HTML content using the Docling library.

The main functionality includes:
- HTML file upload and validation
- Conversion of HTML to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.html_parser import html_parse_main
from markio.schemas.parsers_schemas import HTMLParserConfig
from markio.settings import settings
from markio.utils.file_utils import calculate_file_size, ensure_output_directory
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


@router.post(
    "/parse_html_file",
    tags=["HTML Parser"],
    summary="Parse and convert HTML file to Markdown format",
    description="""
    This endpoint accepts an HTML file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The HTML file to be processed
        - config (HTML_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid HTML file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_html_file_endpoint(
    file: UploadFile = File(...),
    config: HTMLParserConfig = Depends(),
) -> JSONResponse:
    """Endpoint for parsing HTML files to Markdown format"""
    _validate_html_file(file=file)

    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )

    temp_dir = os.path.dirname(NamedTemporaryFile().name)
    original_filename = os.path.basename(file.filename)
    temp_html_path = os.path.join(temp_dir, original_filename)

    with open(temp_html_path, "wb") as temp_html:
        temp_html.write(await file.read())

    logger.debug(f"Temporary HTML file created with original name: {temp_html_path}")
    logger.debug(f"Processing HTML file: {file.filename}")

    try:
        parsed_content = await html_parse_main(
            resource_path=temp_html_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"HTML file {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        # Log detailed error with traceback
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"HTML parsing error: {e}")

    finally:
        # Clean up the temporary HTML file
        if temp_html_path and os.path.exists(temp_html_path):
            os.unlink(temp_html_path)
            logger.debug(f"Temporary HTML file deleted: {temp_html_path}")


def _validate_html_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid HTML file.

    Args:
        file (UploadFile): The HTML file to validate

    Raises:
        HTTPException (400): If the file is not a valid HTML file
            - Invalid content type
            - Invalid file extension
    """
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Validate file content type and extension
    if file.content_type != "text/html" and file_extension != ".html":
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload an HTML file"
        )
