"""
GenBank Router Module

This module provides FastAPI endpoints for parsing and converting GenBank files to Markdown format.
It handles file uploads, validation, and processing of GenBank biological sequence data.

GenBank is a comprehensive database format used by NCBI that includes both sequence data
and extensive biological annotations.

The main functionality includes:
- GenBank file upload and validation
- Conversion of GenBank records to structured Markdown format
- Extraction of metadata, features, and sequence data
- Optional content saving with formatted output
- Temporary file management and cleanup
"""

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.genbank_parser import genbank_parse_main
from markio.schemas.parsers_schemas import GenBankParserConfig
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
    "/parse_genbank_file",
    tags=["Biological Data Parser"],
    summary="Parse and convert GenBank file to Markdown format",
    description="""
    This endpoint accepts a GenBank file upload and converts it to structured Markdown format.

    GenBank is a comprehensive database format that includes both sequence data and extensive
    biological annotations. It's the standard format used by NCBI GenBank database.

    Parameters:
        - file (UploadFile): The GenBank file to be processed (.gb, .gbk, .genbank, .gbff)
        - config (GenBankParserConfig): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content to disk
            - output_dir (str): Directory to save parsed content (optional)
            - include_features (bool): Include feature table in output (default: True)
            - include_sequence (bool): Include sequence data in output (default: True)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content with record information
            - status_code (int): HTTP status code (200 for success)

    Features:
        - Parse complete GenBank records with metadata
        - Extract LOCUS, DEFINITION, ACCESSION, VERSION information
        - Parse feature tables with locations and qualifiers
        - Extract and format sequence data
        - Calculate sequence statistics (length, GC content)
        - Support multiple records per file

    Raises:
        HTTPException (400): If the uploaded file is not a valid GenBank file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content with GenBank record information",
)
async def parse_genbank_endpoint(
    file: UploadFile = File(...),
    config: GenBankParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing GenBank files to Markdown format.
    """
    logger.info(f"Received GenBank parsing request for file: {file.filename}")

    # Validate file type
    _validate_genbank_file(file=file)

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
        temp_genbank_path, unique_filename = create_unique_temp_file(
            original_filename, temp_dir
        )

        # Write the uploaded file content to the temporary file
        with open(temp_genbank_path, "wb") as temp_genbank:
            temp_genbank.write(await file.read())

        logger.debug(
            f"Temporary GenBank file created with original name: {temp_genbank_path}"
        )

        logger.debug(f"Processing GenBank file: {file.filename}")

        # Parse the GenBank file
        parsed_content = await genbank_parse_main(
            resource_path=temp_genbank_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
            include_features=config.include_features,
            include_sequence=config.include_sequence,
        )

        logger.info(f"GenBank {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except ValueError as e:
        # Handle format validation errors
        error_msg = f"Invalid GenBank format in {file.filename}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up the temporary GenBank file
        if temp_genbank_path and os.path.exists(temp_genbank_path):
            os.unlink(temp_genbank_path)
            logger.debug(f"Temporary GenBank file deleted: {temp_genbank_path}")


def _validate_genbank_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid GenBank file.

    This function performs validation based on:
    1. File extension validation: Checks for common GenBank extensions
       (.gb, .gbk, .genbank, .gbff, .txt)

    Note: Content-Type may vary, so we primarily rely on file extension.

    Args:
        file (UploadFile): The GenBank file to validate

    Raises:
        HTTPException (400): If the file is not a valid GenBank file
            - Invalid file extension
    """
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Common GenBank file extensions
    valid_extensions = {
        ".gb",  # Standard GenBank
        ".gbk",  # GenBank
        ".genbank",  # Full name
        ".gbff",  # GenBank flat file
        ".txt",  # Plain text (common for GenBank)
    }

    if file_extension not in valid_extensions:
        error_msg = (
            f"Invalid file format: {file.filename}. "
            f"Expected GenBank file with extensions: {', '.join(valid_extensions)}"
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a GenBank file"
        )

    logger.debug(f"File validation passed for: {file.filename}")
