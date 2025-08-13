"""
Image Router Module

This module provides FastAPI endpoints for parsing and converting image files to Markdown format.
It handles file uploads, validation, and processing of image content using OCR and text extraction.

The main functionality includes:
- Image file upload and validation
- Text extraction from images using OCR
- Conversion of extracted text to Markdown format
- Optional content saving to files
- Temporary file management and cleanup
"""

import os
import traceback
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from markio.parsers.image_parser import image_parse_main
from markio.schemas.parsers_schemas import ImageParserConfig
from markio.settings import settings
from markio.utils.file_utils import calculate_file_size, ensure_output_directory
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir


@router.post(
    "/parse_image_file",
    tags=["Image Parser"],
    summary="Parse and convert image file to Markdown format",
    description="""
    This endpoint accepts an image file upload and converts it to Markdown format.

    Parameters:
        - file (UploadFile): The image file to be processed
        - config (Image_Parser_Config): Configuration options including:
            - save_parsed_content (bool): Whether to save parsed content
            - output_dir (str): Directory to save parsed content (optional)

    Returns:
        JSONResponse: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the uploaded file is not a valid image file
        HTTPException (500): If an error occurs during parsing or conversion
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_image_file_endpoint(
    file: UploadFile = File(...),
    config: ImageParserConfig = Depends(),
) -> JSONResponse:
    """
    Endpoint for parsing image files to Markdown format.
    """
    # Validate the uploaded image file
    _validate_img_file(file=file)

    logger.info(
        f"Starting to parse file: {file.filename}, File size: {calculate_file_size(file.size)}"
    )

    # Ensure the output directory exists
    output_dir = ensure_output_directory(config.output_dir or DEFAULT_OUTPUT_DIR)

    try:
        # Create temporary file with original filename to preserve the name
        temp_dir = os.path.dirname(NamedTemporaryFile().name)  # Get temp directory
        original_filename = os.path.basename(file.filename)
        temp_img_path = os.path.join(temp_dir, original_filename)

        # Write the uploaded file content to the temporary file
        with open(temp_img_path, "wb") as temp_img:
            temp_img.write(await file.read())

        logger.debug(
            f"Temporary image file created with original name: {temp_img_path}"
        )

        logger.debug(f"Processing image file: {file.filename}")

        # Parse the image file
        parsed_content = await image_parse_main(
            resource_path=temp_img_path,
            save_parsed_content=config.save_parsed_content,
            output_dir=output_dir,
        )

        # Log success
        logger.info(f"Image parsed successfully: {file.filename}")

        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        # Log detailed error with traceback
        logger.error(
            f"Error occurred while parsing {file.filename}: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=f"Image parsing error: {e}")

    finally:
        # Clean up the temporary image file
        if temp_img_path and os.path.exists(temp_img_path):
            os.unlink(temp_img_path)
            logger.debug(f"Temporary image file deleted: {temp_img_path}")


def _validate_img_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a valid image file.

    This function performs the following validation:
    1. File extension validation: Verifies the file has a supported image extension
       (Supported formats: .png, .jpg, .jpeg)
    2. Ensures the file is an actual image file

    Args:
        file (UploadFile): The image file to validate

    Raises:
        HTTPException (400): If the file is not a valid image file
            - Invalid file extension
            - Unsupported image format
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    valid_extensions = [
        ".png",
        ".jpg",
        ".jpeg",
    ]

    if file_extension not in valid_extensions:
        supported_formats = ", ".join(valid_extensions)
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Only image files are allowed. Supported formats: {supported_formats}",
        )
