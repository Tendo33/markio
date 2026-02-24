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

import traceback
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.genbank_parser import genbank_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import GenBankParserConfig
from markio.services.sync_parse_service import (
    build_parse_response,
    run_uploaded_file_parser,
)
from markio.settings import settings
from markio.utils.file_utils import (
    calculate_file_size,
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

    # Ensure output directory exists and is constrained
    output_dir = resolve_parser_output_dir(
        requested_output_dir=config.output_dir or DEFAULT_OUTPUT_DIR,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        save_parsed_content=config.save_parsed_content,
    )
    logger.debug(f"Output directory ensured: {output_dir}")

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )
    started_at = perf_counter()

    try:
        parsed_content = await run_uploaded_file_parser(
            file=file,
            parser=genbank_parse_main,
            parser_kwargs={
                "save_parsed_content": config.save_parsed_content,
                "output_dir": output_dir,
                "include_features": config.include_features,
                "include_sequence": config.include_sequence,
            },
        )

        logger.info(f"GenBank {file.filename} parsed successfully")

        return build_parse_response(
            parsed_content=parsed_content,
            parser="genbank",
            source_type="file",
            started_at=started_at,
        )

    except HTTPException:
        raise
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
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={".gb", ".gbk", ".genbank", ".gbff", ".txt"},
    )
