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

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.docx_parser import docx_parse_main
from markio.schemas.parsers_schemas import DOCXParserConfig
from markio.settings import settings
from markio.utils.file_utils import calculate_file_size, ensure_output_directory
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

    # Ensure output directory exists
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)
    logger.debug(f"Output directory ensured: {output_dir}")

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )

    try:
        # Create temporary file with original filename to preserve the name
        temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
        original_filename = os.path.basename(file.filename)
        temp_docx_path = os.path.join(temp_dir, original_filename)

        # Write the uploaded file content to the temporary file
        with open(temp_docx_path, "wb") as temp_docx:
            temp_docx.write(await file.read())

        logger.debug(
            f"Temporary DOCX file created with original name: {temp_docx_path}"
        )

        logger.debug(f"Processing DOCX file: {file.filename}")

        # Parse the DOCX file
        parsed_content = await docx_parse_main(
            resource_path=temp_docx_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"DOCX {file.filename} parsed successfully")

        return JSONResponse({"markdown_content": parsed_content}, status_code=200)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up the temporary DOCX file
        if temp_docx_path and os.path.exists(temp_docx_path):
            os.unlink(temp_docx_path)
            logger.debug(f"Temporary DOCX file deleted: {temp_docx_path}")


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
    file_extension = os.path.splitext(file.filename)[1].lower()

    if (
        file.content_type
        != "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        and file_extension != ".docx"
    ):
        error_msg = f"Invalid file format: {file.filename}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a DOCX file"
        )
