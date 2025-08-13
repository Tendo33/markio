"""
PPT Router Module

This module provides FastAPI endpoints for parsing and converting PPT files to Markdown format.
It handles file uploads, validation, and processing of PPT content using the Docling library.

The main functionality includes:
- PPT file upload and validation
- Conversion of PPT to Markdown format
- Optional image extraction and content saving
- Temporary file management and cleanup
"""

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.ppt_parser import ppt_parse_main
from markio.schemas.parsers_schemas import PPTParserConfig
from markio.settings import settings
from markio.utils.file_utils import ensure_output_directory
from markio.utils.logger_config import get_logger

router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir

logger = get_logger(__name__)


@router.post(
    "/parse_ppt_file",
    tags=["PPT Parser"],
    summary="Parse and convert PPT file to Markdown format",
    description="""
    This endpoint accepts a PPT file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The PPT file to be processed
        - config (PPT_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid PPT file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_ppt_file_endpoint(
    file: UploadFile = File(...),
    config: PPTParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing PPT files to Markdown format.
    """
    # Validate file type
    _validate_ppt_file(file=file)

    # Ensure output directory exists
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {file.size} bytes"
    )

    # Create temporary file with original filename to preserve the name
    temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
    original_filename = os.path.basename(file.filename)
    temp_ppt_path = os.path.join(temp_dir, original_filename)

    # Write the uploaded file content to the temporary file
    with open(temp_ppt_path, "wb") as temp_ppt:
        temp_ppt.write(await file.read())

    logger.debug(f"Temporary PPT file created with original name: {temp_ppt_path}")

    logger.debug(f"Processing PPT file: {file.filename}")

    # Parse the PPT file
    try:
        parsed_content = await ppt_parse_main(
            resource_path=temp_ppt_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"PPT {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"PPT parsing error: {str(e)}")

    finally:
        # Clean up temporary PPT file
        if temp_ppt_path and os.path.exists(temp_ppt_path):
            os.unlink(temp_ppt_path)
            logger.debug(f"Temporary PPT file deleted: {temp_ppt_path}")


def _validate_ppt_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid PPT file.

    This function performs two types of validation:
    1. Content-Type validation: Checks if the file's MIME type is either:
       - 'application/vnd.ms-powerpoint' or
       - 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    2. File extension validation: Verifies the file has a .ppt extension

    Args:
        file (UploadFile): The PPT file to validate

    Raises:
        HTTPException (400): If the file is not a valid PPT file
            - Invalid content type
            - Invalid file extension
    """
    file_extension = os.path.splitext(file.filename)[1].lower()

    if (
        file.content_type
        not in [
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]
        and file_extension != ".ppt"
    ):
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a PPT file"
        )
