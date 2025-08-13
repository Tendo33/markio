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

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.pptx_parser import pptx_parse_main
from markio.schemas.parsers_schemas import PPTXParserConfig
from markio.settings import settings
from markio.utils.file_utils import ensure_output_directory
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
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)

    logger.info(f"Starting to parse file: {file.filename}")

    # Create temporary file with original filename to preserve the name
    temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
    original_filename = os.path.basename(file.filename)
    temp_pptx_path = os.path.join(temp_dir, original_filename)

    # Write the uploaded file content to the temporary file
    with open(temp_pptx_path, "wb") as temp_pptx:
        temp_pptx.write(await file.read())

    logger.debug(f"Temporary PPTX file created with original name: {temp_pptx_path}")

    logger.debug(f"Processing PPTX file: {file.filename}")

    # Parse the PPTX file
    try:
        parsed_content = await pptx_parse_main(
            resource_path=temp_pptx_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"PPTX file {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"PPTX parsing error: {str(e)}")

    finally:
        if temp_pptx_path and os.path.exists(temp_pptx_path):
            os.unlink(temp_pptx_path)
            logger.debug(f"Temporary PPTX file deleted: {temp_pptx_path}")


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
    file_extension = os.path.splitext(file.filename)[1].lower()

    if (
        file.content_type
        != "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        and file_extension != ".pptx"
    ):
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a PPTX file"
        )
