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

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.pdf_parser import pdf_parse_main
from markio.parsers.pdf_parser_vlm import pdf_parse_vlm_main
from markio.schemas.parsers_schemas import PDFParserConfig
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
        temp_pdf_path, unique_filename = create_unique_temp_file(
            original_filename, temp_dir
        )

        # Write the uploaded file content to the temporary file
        with open(temp_pdf_path, "wb") as temp_pdf:
            temp_pdf.write(await file.read())

        logger.debug(f"Temporary PDF file created with unique name: {temp_pdf_path}")

        logger.debug(f"Processing PDF file: {file.filename}")

        # Choose parser based on PDF_PARSE_ENGINE environment variable
        pdf_parse_engine = settings.pdf_parse_engine
        logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

        if pdf_parse_engine == "pipeline":
            # Use pipeline parser
            parsed_content = await pdf_parse_main(
                resource_path=temp_pdf_path,
                save_parsed_content=config.save_parsed_content,
                output_dir=output_dir,
                lang=config.lang,
            )
        elif pdf_parse_engine == "vlm-sglang-engine":
            # Use VLM parser
            parsed_content = await pdf_parse_vlm_main(
                resource_path=temp_pdf_path,
                save_parsed_content=config.save_parsed_content,
                output_dir=output_dir,
            )
        else:
            error_msg = f"Invalid PDF_PARSE_ENGINE value: {pdf_parse_engine}. Must be 'pipeline' or 'vlm-sglang-engine'"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        logger.info(
            f"PDF {file.filename} parsed successfully using {pdf_parse_engine} engine"
        )

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up the temporary PDF file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
            logger.debug(f"Temporary PDF file deleted: {temp_pdf_path}")


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
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file.content_type != "application/pdf" and file_extension != ".pdf":
        error_msg = f"Invalid file format: {file.filename}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a PDF file"
        )
