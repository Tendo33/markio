"""
File Router Module

This module provides a unified FastAPI endpoint for handling file uploads and automatically
routing them to the appropriate parser based on file extension. It supports various file
formats including DOC, DOCX, PDF, PPT, PPTX, XLSX, HTML, and images.

The main functionality includes:
- Unified file upload endpoint
- Automatic file type detection and routing
- Support for multiple file formats
- Consistent error handling and response format
"""

import os
import traceback
from tempfile import NamedTemporaryFile
from typing import Callable, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers import (
    doc_parser,
    docx_parser,
    epub_parser,
    html_parser,
    image_parser,
    pdf_parser,
    pdf_parser_vlm,
    ppt_parser,
    pptx_parser,
    xlsx_parser,
)
from markio.schemas.parsers_schemas import (
    BaseParserConfig,
)
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

# File extension to parser mapping
FILE_PARSERS: Dict[str, Callable] = {
    ".doc": (doc_parser.doc_parse_main),
    ".docx": (docx_parser.docx_parse_main),
    ".pdf": (pdf_parser.pdf_parse_main),
    ".ppt": (ppt_parser.ppt_parse_main),
    ".pptx": (pptx_parser.pptx_parse_main),
    ".xlsx": (xlsx_parser.xlsx_parse_main),
    ".html": (html_parser.html_parse_main),
    ".epub": (epub_parser.epub_parse_main),
    # Image formats
    ".png": (image_parser.image_parse_main),
    ".jpg": (image_parser.image_parse_main),
    ".jpeg": (image_parser.image_parse_main),
}

# Supported MIME types mapping
MIME_TYPES = {
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".html": "text/html",
    ".htm": "text/html",
    # Image MIME types
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@router.post(
    "/parse_file",
    tags=["File Parser"],
    summary="Parse and convert file to Markdown format",
    description="""
    Unified endpoint for parsing various file formats to Markdown format.
    Automatically routes to the appropriate parser based on file extension.

    Parameters:
        - file (UploadFile): The file to be processed
        - config (BaseParserConfig): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content (default: false)
            - output_dir (str): Directory to save parsed content (optional, uses system default if not specified)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file type is not supported
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_file_endpoint(
    file: UploadFile = File(...),
    config: BaseParserConfig = Depends(),
) -> JSONResponse:
    """
    Unified endpoint for file parsing that automatically routes to the appropriate parser
    based on file extension.
    """
    logger.info(
        f"Received file parsing request for file: {file.filename},config: {config}"
    )

    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Check if file type is supported
    if file_extension not in FILE_PARSERS:
        supported_types = ", ".join(FILE_PARSERS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types are: {supported_types}",
        )

    # Validate file type
    if file.content_type != MIME_TYPES.get(file_extension):
        logger.warning(
            f"File content type ({file.content_type}) doesn't match expected type "
            f"({MIME_TYPES.get(file_extension)}) for extension {file_extension}"
        )

    # Ensure output directory exists
    if config.save_parsed_content:
        output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    logger.debug(f"Output directory ensured: {output_dir}")

    # Update config with the correct output_dir for parser functions
    config.output_dir = output_dir

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )

    temp_file_path = None
    try:
        # Create temporary file with unique filename to avoid conflicts
        temp_dir = os.path.dirname(NamedTemporaryFile().name)
        original_filename = os.path.basename(file.filename)

        temp_file_path, unique_filename = create_unique_temp_file(
            original_filename, temp_dir
        )

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        logger.debug(f"Temporary file created with unique name: {temp_file_path}")

        # Get parser function
        parser_func = FILE_PARSERS[file_extension]

        # Process file based on type
        if file_extension == ".pdf":
            pdf_parse_engine = settings.pdf_parse_engine
            logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

            if pdf_parse_engine == "pipeline":
                parsed_content = await pdf_parser.pdf_parse_main(
                    resource_path=temp_file_path,
                    save_parsed_content=config.save_parsed_content,
                    output_dir=output_dir,
                )
            elif pdf_parse_engine == "vlm-sglang-engine":
                parsed_content = await pdf_parser_vlm.pdf_parse_vlm_main(
                    resource_path=temp_file_path,
                    save_parsed_content=config.save_parsed_content,
                    output_dir=output_dir,
                )
            else:
                error_msg = f"Invalid PDF_PARSE_ENGINE value: {pdf_parse_engine}. Must be 'pipeline' or 'vlm-sglang-engine'"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
        else:
            parsed_content = await parser_func(
                temp_file_path, config.save_parsed_content, config.output_dir
            )

        logger.info(f"File {file.filename} parsed successfully")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.debug(f"Temporary file deleted: {temp_file_path}")
