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

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.epub_parser import epub_parse_main
from markio.schemas.parsers_schemas import EPUBParserConfig
from markio.settings import settings
from markio.utils.file_utils import ensure_output_directory
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

    # Ensure output directory
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)

    logger.info(f"Starting to parse file: {file.filename}")

    # Create temporary file with original filename to preserve the name
    temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
    original_filename = os.path.basename(file.filename)
    temp_epub_path = os.path.join(temp_dir, original_filename)

    # Write the uploaded file content to the temporary file
    with open(temp_epub_path, "wb") as temp_epub:
        temp_epub.write(await file.read())

    logger.debug(f"Temporary EPUB file created with original name: {temp_epub_path}")

    logger.debug(f"Processing EPUB file: {file.filename}")

    # Parse the EPUB file
    try:
        parsed_content = await epub_parse_main(
            resource_path=temp_epub_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        logger.info(f"EPUB file {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"EPUB parsing error: {str(e)}")

    finally:
        if temp_epub_path and os.path.exists(temp_epub_path):
            os.unlink(temp_epub_path)
            logger.debug(f"Temporary EPUB file deleted: {temp_epub_path}")


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
    file_extension = os.path.splitext(file.filename)[1].lower()

    if (
        file.content_type not in ["application/epub+zip", "application/zip"]
        and file_extension != ".epub"
    ):
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload an EPUB file"
        )
