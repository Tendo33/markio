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

from time import perf_counter

from fastapi import APIRouter, HTTPException, Query

from markio.parsers.url_parser import URLFetchError, URLSecurityError, url_parse_main
from markio.routers._request_guards import resolve_parser_output_dir
from markio.services.sync_parse_service import execute_parse_request
from markio.settings import settings
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
        - output_dir (str): Directory to save parsed content (optional, defaults to the configured outputs directory)

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
        description="Directory to save the output file. Relative paths are resolved inside the configured outputs directory.",
    ),
):
    """
    Endpoint for parsing HTML content from URLs to Markdown format.
    """
    _validate_url(url)
    output_dir = resolve_parser_output_dir(
        requested_output_dir=output_dir or DEFAULT_OUTPUT_DIR,
        base_output_dir=DEFAULT_OUTPUT_DIR,
        save_parsed_content=save_parsed_content,
    )
    started_at = perf_counter()
    return await execute_parse_request(
        parse_fn=lambda: url_parse_main(
            url=url,
            save_parsed_content=save_parsed_content,
            output_dir=output_dir,
        ),
        parser="url",
        source_type="url",
        source_name=url,
        started_at=started_at,
        logger=logger,
        handled_errors={
            URLSecurityError: lambda error: HTTPException(
                status_code=400,
                detail=str(error),
            ),
            URLFetchError: lambda error: HTTPException(
                status_code=502,
                detail="Failed to fetch URL content",
            ),
        },
    )


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
