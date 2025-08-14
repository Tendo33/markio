"""
DOC Router Module

This module provides FastAPI endpoints for parsing and converting DOC files to Markdown format.
It handles file uploads, validation, and processing of DOC content using the Docling library.

The main functionality includes:
- DOC file upload and validation
- Conversion of DOC to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.doc_parser import doc_parse_main
from markio.schemas.parsers_schemas import DOCXParserConfig
from markio.settings import settings
from markio.utils.file_utils import (
    calculate_file_size,
    create_unique_temp_file,
    ensure_output_directory,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


@router.post(
    "/parse_doc_file",
    tags=["DOC Parser"],
    summary="Parse and convert DOC file to Markdown format",
    description="""
    This endpoint accepts a DOC file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The DOC file to be processed
        - config (DOC_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid DOC file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_doc_file_endpoint(
    file: UploadFile = File(...),
    config: DOCXParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing DOC files to Markdown format.
    """
    logger.info(f"Received DOC parsing request for file: {file.filename}")

    # Validate file type
    _validate_doc_file(file=file)

    # Ensure output directory exists
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)
    logger.debug(f"Output directory ensured: {output_dir}")

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )

    try:
        # Create temporary file with unique filename to avoid conflicts
        temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
        original_filename = os.path.basename(file.filename)

        # Use utility function to create unique temp file
        temp_doc_path, unique_filename = create_unique_temp_file(
            original_filename, temp_dir
        )

        # Write the uploaded file content to the temporary file
        with open(temp_doc_path, "wb") as temp_doc:
            temp_doc.write(await file.read())

        logger.debug(f"Temporary DOC file created with unique name: {temp_doc_path}")

        logger.debug(f"Processing DOC file: {file.filename}")

        # Parse the DOC file
        parsed_content = await doc_parse_main(
            resource_path=temp_doc_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"DOC {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up the temporary DOC file
        if temp_doc_path and os.path.exists(temp_doc_path):
            os.unlink(temp_doc_path)
            logger.debug(f"Temporary DOC file deleted: {temp_doc_path}")


def _validate_doc_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid DOC file.

    Args:
        file (UploadFile): The DOC file to validate

    Raises:
        HTTPException (400): If the file is not a valid DOC file
            - Invalid content type
            - Invalid file extension
    """
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file.content_type != "application/msword" and file_extension != ".doc":
        error_msg = f"Invalid file format: {file.filename}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a DOC file"
        )
