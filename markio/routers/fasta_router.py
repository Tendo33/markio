"""
FASTA Router Module

This module provides FastAPI endpoints for parsing and converting FASTA files to Markdown format.
It handles file uploads, validation, and processing of FASTA biological sequence data.

FASTA format is widely used in bioinformatics for representing nucleotide or peptide sequences.

The main functionality includes:
- FASTA file upload and validation
- Conversion of FASTA sequences to structured Markdown format
- Sequence statistics calculation (length, GC content, type)
- Optional content saving with formatted output
- Temporary file management and cleanup
"""

import traceback
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.fasta_parser import fasta_parse_main
from markio.routers._request_guards import (
    resolve_parser_output_dir,
    validate_upload_file,
)
from markio.schemas.parsers_schemas import FASTAParserConfig
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
    "/parse_fasta_file",
    tags=["Biological Data Parser"],
    summary="Parse and convert FASTA file to Markdown format",
    description="""
    This endpoint accepts a FASTA file upload and converts it to structured Markdown format.

    FASTA format is a text-based format for representing nucleotide or peptide sequences,
    widely used in bioinformatics. Each sequence begins with a description line (header)
    starting with '>', followed by sequence data.

    Parameters:
        - file (UploadFile): The FASTA file to be processed (.fasta, .fa, .fna, .faa)
        - config (FASTAParserConfig): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content to disk
            - output_dir (str): Directory to save parsed content (optional)
            - include_statistics (bool): Include sequence statistics in output (default: True)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content with sequence information
            - status_code (int): HTTP status code (200 for success)

    Features:
        - Parse single or multiple sequences
        - Extract sequence metadata (ID, description, type)
        - Calculate statistics (length, GC content for DNA sequences)
        - Detect sequence type (DNA, Protein, Unknown)
        - Format sequences in readable blocks

    Raises:
        HTTPException (400): If the uploaded file is not a valid FASTA file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content with sequence information",
)
async def parse_fasta_endpoint(
    file: UploadFile = File(...),
    config: FASTAParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing FASTA files to Markdown format.
    """
    logger.info(f"Received FASTA parsing request for file: {file.filename}")

    # Validate file type
    _validate_fasta_file(file=file)

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
            parser=fasta_parse_main,
            parser_kwargs={
                "save_parsed_content": config.save_parsed_content,
                "output_dir": output_dir,
                "include_statistics": config.include_statistics,
            },
        )

        logger.info(f"FASTA {file.filename} parsed successfully")

        return build_parse_response(
            parsed_content=parsed_content,
            parser="fasta",
            source_type="file",
            started_at=started_at,
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Handle format validation errors
        error_msg = f"Invalid FASTA format in {file.filename}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


def _validate_fasta_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid FASTA file.

    This function performs validation based on:
    1. File extension validation: Checks for common FASTA extensions
       (.fasta, .fa, .fna, .faa, .ffn, .fsa, .fas, .txt)

    Note: Content-Type may vary, so we primarily rely on file extension.

    Args:
        file (UploadFile): The FASTA file to validate

    Raises:
        HTTPException (400): If the file is not a valid FASTA file
            - Invalid file extension
    """
    validate_upload_file(
        file,
        logger=logger,
        allowed_extensions={
            ".fasta",
            ".fa",
            ".fna",
            ".faa",
            ".ffn",
            ".fsa",
            ".fas",
            ".txt",
        },
    )
