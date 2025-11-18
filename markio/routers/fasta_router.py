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

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.fasta_parser import fasta_parse_main
from markio.schemas.parsers_schemas import FASTAParserConfig
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
        temp_fasta_path, unique_filename = create_unique_temp_file(
            original_filename, temp_dir
        )

        # Write the uploaded file content to the temporary file
        with open(temp_fasta_path, "wb") as temp_fasta:
            temp_fasta.write(await file.read())

        logger.debug(
            f"Temporary FASTA file created with original name: {temp_fasta_path}"
        )

        logger.debug(f"Processing FASTA file: {file.filename}")

        # Parse the FASTA file
        parsed_content = await fasta_parse_main(
            resource_path=temp_fasta_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
            include_statistics=config.include_statistics,
        )

        logger.info(f"FASTA {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

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

    finally:
        # Clean up the temporary FASTA file
        if temp_fasta_path and os.path.exists(temp_fasta_path):
            os.unlink(temp_fasta_path)
            logger.debug(f"Temporary FASTA file deleted: {temp_fasta_path}")


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
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Common FASTA file extensions
    valid_extensions = {
        ".fasta",  # Standard FASTA
        ".fa",  # Short form
        ".fna",  # FASTA nucleic acid
        ".faa",  # FASTA amino acid
        ".ffn",  # FASTA nucleotide coding regions
        ".fsa",  # FASTA sequence alignment
        ".fas",  # Alternative
        ".txt",  # Plain text (common for FASTA)
    }

    if file_extension not in valid_extensions:
        error_msg = (
            f"Invalid file format: {file.filename}. "
            f"Expected FASTA file with extensions: {', '.join(valid_extensions)}"
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=400, detail="Invalid file type, please upload a FASTA file"
        )

    logger.debug(f"File validation passed for: {file.filename}")
