import contextlib
import os
import time
from functools import wraps
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import aiofiles
import aiohttp

from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


def ensure_output_directory(output_dir: str) -> str:
    """
    Ensure the given output directory exists, creating it if necessary.

    Args:
        output_dir: The directory path to ensure exists

    Returns:
        str: The absolute path to the output directory
    """
    abs_output_dir = Path(output_dir).resolve()
    abs_output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured output directory exists: {abs_output_dir}")

    return str(output_dir)


async def md_dump_io(
    md_content: str,
    output_path: str,
    file_name: str,
) -> None:
    """
    Asynchronously save Markdown content to specified file.

    Args:
        output_path: Path to save the file
        md_content: Markdown content to save
        file_name: File name for the markdown file
    """
    os.makedirs(output_path, exist_ok=True)

    final_path = os.path.join(output_path, f"{file_name}.md")

    try:
        async with aiofiles.open(final_path, mode="w", encoding="utf-8") as f:
            await f.write(md_content)
        logger.info(f"Markdown file saved to: {final_path}")
    except Exception as e:
        logger.error(f"Error saving Markdown file: {e}")
        raise ValueError(f"Unable to save {final_path} ")


@contextlib.contextmanager
def create_temporary_file(suffix="", delete=False):
    """
    Safe context manager for creating and managing temporary files.

    Args:
        suffix: Suffix for temporary file
        delete: Whether to automatically delete file after use
    """
    try:
        temp_file = NamedTemporaryFile(
            delete=delete,
            suffix=suffix,
        )
        yield temp_file
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise
    finally:
        if not delete and os.path.exists(temp_file.name):
            try:
                temp_file.close()
                os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {e}")


def calculate_file_size(size_in_bytes: int) -> str:
    """
    Convert bytes to human-readable format (KB, MB, GB, etc.)

    Args:
        size_in_bytes: File size in bytes

    Returns:
        str: Human-readable file size
    """
    if size_in_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_in_bytes >= 1024 and i < len(size_names) - 1:
        size_in_bytes /= 1024.0
        i += 1

    return f"{size_in_bytes:.1f}{size_names[i]}"


def func_processing_time(func):
    """
    Decorator to measure and log function processing time.

    Args:
        func: Function to be decorated

    Returns:
        Wrapped function with timing functionality
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()

        processing_time = end_time - start_time
        logger.info(f"Processed {func.__name__} in {processing_time:.2f} seconds")

        return result

    return wrapper


async def download_file_from_url(
    url: str,
    output_path: str = None,
    filename: str = None,
    timeout: int = 300,
) -> str:
    """
    Download file from URL to local path.

    Args:
        url: URL to download from
        output_path: Local directory to save file
        filename: Custom filename (optional)
        timeout: Download timeout in seconds

    Returns:
        str: Local file path

    Raises:
        ValueError: If URL is invalid
        Exception: For download errors
    """
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL format: {url}")

    if not filename:
        filename = extract_filename_from_url(url) or "downloaded_file"

    if output_path:
        output_path = os.path.join(output_path, filename)
    else:
        temp_dir = os.path.dirname(NamedTemporaryFile().name)
        output_path = os.path.join(temp_dir, filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()

                async with aiofiles.open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)

        logger.info(f"Successfully downloaded file from {url} to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to download file from {url}. Error: {e}")
        raise


def is_valid_url(url_string: str) -> bool:
    """
    Check if string is a valid URL.

    Args:
        url_string: String to validate

    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_filename_from_url(url: str) -> str:
    """
    Extract filename from URL path.

    Args:
        url: URL to extract filename from

    Returns:
        str: Extracted filename or empty string
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
        if path and path != "/":
            filename = os.path.basename(path)
            if filename and "." in filename:
                return filename
        return ""
    except Exception:
        return ""


def is_url_or_file_path(resource_path: str) -> str:
    """
    Determine if input is URL or local file path.

    Args:
        resource_path: Input string to analyze

    Returns:
        str: 'url' for URLs, 'local' for local paths
    """
    if not resource_path:
        return "local"

    try:
        parsed = urlparse(resource_path)

        if parsed.scheme in ["http", "https"]:
            return "url"
        elif parsed.scheme == "file":
            return "local"
        elif parsed.scheme:
            return "url"
    except Exception:
        pass

    if os.path.isabs(resource_path):
        return "local"
    elif os.path.exists(resource_path):
        return "local"
    else:
        return "local"


async def process_resource_path(
    resource_path: str,
    output_dir: str = None,
) -> str:
    """
    Process file path or URL, downloading if necessary.

    Args:
        resource_path: File path or URL to process
        output_dir: Directory to save downloaded files

    Returns:
        str: Local file path
    """
    input_type = is_url_or_file_path(resource_path)

    if input_type == "url":
        logger.info(f"Detected URL input: {resource_path}, downloading...")
        try:
            local_path = await download_file_from_url(resource_path, output_dir)
            logger.info(f"Successfully downloaded URL to: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to download URL {resource_path}: {e}")
            raise
    else:
        logger.info(f"Using local file: {resource_path}")
        return resource_path
