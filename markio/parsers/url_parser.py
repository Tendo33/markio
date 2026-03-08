from pathlib import Path

import aiohttp

from markio.utils.file_utils import (
    func_processing_time,
    md_dump_io,
    resolve_path_within_base,
    slugify_path_component,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def url_parse_main(
    url: str,
    save_parsed_content: bool = False,
    output_dir: str = "",
) -> str:
    """
    Fetch and parse content from a URL, converting it to Markdown format.

    This parser fetches content from a URL using aiohttp and converts it to Markdown while:
    - Preserving the page structure and content
    - Handling various web page formats
    - Supporting image extraction (when save_parsed_content is True)
    - Managing timeouts and errors gracefully
    - Using a custom user agent for better compatibility

    Args:
        url: The URL to fetch and parse
        save_parsed_content: Whether to save parsed content to file
        output_dir: Directory where parsed content and images will be saved

    Returns:
        str: Parsed content in Markdown format

    Raises:
        aiohttp.ClientError: For network-related errors during fetch
        ValueError: If URL is invalid or required parameters missing
        Exception: For other errors during fetching or parsing
    """
    full_url = f"https://r.jina.ai/{url}"
    timeout = aiohttp.ClientTimeout(total=120)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                full_url, headers=headers, timeout=timeout
            ) as response:
                response.raise_for_status()
                markdown_content = await response.text()

        file_name = markdown_content.split("\n")[0].replace("Title:", "").strip()
        safe_slug = slugify_path_component(file_name, fallback="url-content")

        if save_parsed_content:
            resolved_output_dir = Path(output_dir).resolve()
            save_parsed_dir = (resolved_output_dir / safe_slug).resolve()
            try:
                resolve_path_within_base(resolved_output_dir, save_parsed_dir)
            except ValueError as exc:
                raise RuntimeError("Invalid URL output path") from exc
            save_parsed_dir.mkdir(parents=True, exist_ok=True)
            output_path = (save_parsed_dir / f"{safe_slug}.md").resolve()
            try:
                resolve_path_within_base(resolved_output_dir, output_path)
            except ValueError as exc:
                raise RuntimeError("Invalid URL output file path") from exc

            await md_dump_io(
                md_content=markdown_content,
                output_path=output_path,
            )
            logger.info(f"URL {safe_slug} saved to {output_path}")

        return markdown_content

    except aiohttp.ClientError as e:
        logger.error(f"Failed to fetch content from {full_url}. Error: {e}")
        raise RuntimeError(f"Failed to fetch URL content: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise RuntimeError(f"Unexpected URL parsing error: {e}") from e
