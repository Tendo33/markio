"""
URL Router Module

This module provides FastAPI endpoints for parsing and converting HTML content from URLs to Markdown format.
It handles URL validation, content fetching, and processing using the Docling library.

The main functionality includes:
- URL validation and content fetching
- Conversion of HTML content to Markdown format
- Optional content saving to files
- Error handling and logging
"""

import traceback

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from markio.parsers.url_parser import url_parse_main
from markio.settings import settings
from markio.utils.file_utils import ensure_output_directory
from markio.utils.logger_config import get_logger

router = APIRouter()

# Default output directory for parsed files
DEFAULT_OUTPUT_DIR = settings.output_dir
logger = get_logger(__name__)


@router.post(
    "/parse_url",
    tags=["URL Parser"],
    summary="Parse and convert HTML content from URL to Markdown format",
    description="""
    This endpoint fetches HTML content from a specified URL and converts it to Markdown format.

    Parameters:
        - url (str): The URL to fetch and parse HTML content from
        - save_parsed_content (bool): Whether to save the parsed content to a file
        - output_dir (str): Directory to save parsed content (optional, defaults to ~/mark_flow_parsed_content)

    Returns:
        dict: A JSON response containing:
            - parsed_content (str): The converted Markdown content
            - status_code (int): HTTP status code (200 for success)

    Raises:
        HTTPException (400): If the URL format is invalid
        HTTPException (500): If an error occurs during fetching or parsing
    """,
    response_description="Returns the parsed Markdown content in JSON format",
)
async def parse_html_url_endpoint(
    url: str = Query(..., description="The URL of the HTML page to parse."),
    save_parsed_content: bool = Query(
        default=False,
        description="Whether to save the parsed content to a file in the output directory.",
    ),
    output_dir: str = Query(
        default=DEFAULT_OUTPUT_DIR,
        description="Directory to save the output file. Defaults to ~/mark_flow_parsed_content.",
    ),
):
    """
    Endpoint for parsing HTML content from URLs to Markdown format.
    """
    _validate_url(url)
    output_dir = ensure_output_directory(output_dir or DEFAULT_OUTPUT_DIR)

    try:
        parsed_content = await url_parse_main(
            url=url, save_parsed_content=save_parsed_content, output_dir=output_dir
        )
        logger.info("Successfully parsed content from URL", extra={"url": url})
        return JSONResponse({"parsed_content": parsed_content}, status_code=200)

    except Exception as e:
        logger.exception(f"Error during URL parsing: {url} - {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"HTML parsing failed: {str(e)}")


def _validate_url(url: str) -> None:
    """
    Validates that the provided URL has a valid format.

    Args:
        url (str): The URL to validate

    Raises:
        HTTPException (400): If the URL format is invalid
            - URL must start with http:// or https://
    """
    if not url.startswith(("http://", "https://")):
        logger.error("Invalid URL format", extra={"url": url})
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://."
        )
