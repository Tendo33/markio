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
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

import markio.services.parser_registry as parser_registry
from markio.parsers import pdf_parser
from markio.schemas.parsers_schemas import (
    BaseParserConfig,
)
from markio.services.sync_parse_service import (
    build_parse_response,
    run_uploaded_file_parser,
)
from markio.settings import settings
from markio.utils.file_utils import (
    calculate_file_size,
    ensure_output_directory,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


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
    started_at = perf_counter()

    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Check if file type is supported
    if not parser_registry.get_parser_for_extension(file_extension):
        supported_types = ", ".join(parser_registry.get_supported_extensions())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types are: {supported_types}",
        )

    # Validate file type
    if not parser_registry.is_expected_mime_type(file_extension, file.content_type):
        expected = ", ".join(parser_registry.get_expected_mime_types(file_extension)) or "unknown"
        logger.warning(
            f"File content type ({file.content_type}) doesn't match expected type "
            f"({expected}) for extension {file_extension}"
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

    try:
        # Get parser function
        parser_func = parser_registry.get_parser_for_extension(file_extension)

        # Process file based on type
        if file_extension == ".pdf":
            pdf_parse_engine = settings.pdf_parse_engine
            logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

            async def parse_pdf(temp_path: str) -> str:
                return await pdf_parser.pdf_parse_main(
                    resource_path=temp_path,
                    parse_method=getattr(config, "parse_method", "auto"),
                    lang=getattr(config, "lang", "ch"),
                    save_parsed_content=config.save_parsed_content,
                    save_middle_content=getattr(config, "save_middle_content", False),
                    output_dir=output_dir,
                    start_page=getattr(config, "start_page", 0),
                    end_page=getattr(config, "end_page", None),
                    backend=pdf_parse_engine,
                    server_url=settings.vlm_server_url,
                )

            parsed_content = await run_uploaded_file_parser(file=file, parser=parse_pdf)
        elif parser_func is not None:
            parsed_content = await run_uploaded_file_parser(
                file=file,
                parser=parser_func,
                parser_args=(config.save_parsed_content, config.output_dir),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}",
            )

        logger.info(f"File {file.filename} parsed successfully")

        parser_name = "pdf" if file_extension == ".pdf" else file_extension.lstrip(".")
        return build_parse_response(
            parsed_content=parsed_content,
            parser=parser_name,
            source_type="file",
            started_at=started_at,
        )

    except Exception as e:
        error_msg = f"Error occurred while parsing {file.filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)
