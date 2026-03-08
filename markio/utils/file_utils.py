import contextlib
import os
import re
import time
from functools import wraps
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import aiofiles
import aiohttp

from markio.utils.logger_config import get_logger

logger = get_logger(__name__)
_FILENAME_ALLOWED_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_SLUG_ALLOWED_CHARS = re.compile(r"[^a-z0-9-]+")


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

    return str(abs_output_dir)


def sanitize_filename(filename: str | None, fallback: str = "upload") -> str:
    raw_name = Path(filename or "").name
    if raw_name in {"", ".", ".."}:
        raw_name = fallback

    suffix = Path(raw_name).suffix
    stem = Path(raw_name).stem or fallback
    sanitized_stem = _FILENAME_ALLOWED_CHARS.sub("_", stem).strip("._-")
    if not sanitized_stem:
        sanitized_stem = fallback

    sanitized_suffix = _FILENAME_ALLOWED_CHARS.sub("", suffix)
    if sanitized_suffix and not sanitized_suffix.startswith("."):
        sanitized_suffix = f".{sanitized_suffix}"
    if len(sanitized_suffix) > 10:
        sanitized_suffix = sanitized_suffix[:10]
    if sanitized_suffix in {".", ".."}:
        sanitized_suffix = ""

    normalized = f"{sanitized_stem[:120]}{sanitized_suffix}"
    return normalized or fallback


def slugify_path_component(value: str, fallback: str = "untitled", max_length: int = 80) -> str:
    lowered = (value or "").strip().lower()
    normalized = (
        lowered.replace("\\", "-")
        .replace("/", "-")
        .replace(":", "-")
        .replace(" ", "-")
    )
    normalized = _SLUG_ALLOWED_CHARS.sub("-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        normalized = fallback
    return normalized[:max_length] or fallback


def resolve_path_within_base(base_dir: str | Path, candidate: str | Path) -> Path:
    base_path = Path(base_dir).expanduser().resolve()
    candidate_path = Path(candidate).expanduser().resolve()
    candidate_path.relative_to(base_path)
    return candidate_path


async def md_dump_io(
    md_content: str,
    output_path: str | Path,
) -> None:
    """
    Asynchronously save Markdown content to specified file.

    Args:
        output_path: Final markdown file path
        md_content: Markdown content to save
    """
    final_path = Path(output_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with aiofiles.open(final_path, mode="w", encoding="utf-8") as f:
            await f.write(md_content)
        logger.info(f"Markdown file saved to: {final_path}")
    except OSError as e:
        logger.error(f"File system error saving Markdown file: {e}")
        raise ValueError(f"Unable to save {final_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving Markdown file: {e}")
        raise ValueError(f"Unable to save {final_path}: {str(e)}")


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


def create_unique_temp_file(
    original_filename: str, temp_dir: str = None
) -> tuple[str, str]:
    """
    Create a unique temporary file path to avoid conflicts when multiple files with the same name are processed concurrently.

    Args:
        original_filename (str): The original filename to preserve extension
        temp_dir (str, optional): Directory for temporary file. If None, uses system temp directory

    Returns:
        tuple[str, str]: (temp_file_path, unique_filename)

    Example:
        temp_path, unique_name = create_unique_temp_file("document.docx")
        # Returns: ("/tmp/document_abc123.docx", "document_abc123.docx")
    """
    import tempfile
    import uuid

    if temp_dir is None:
        temp_dir = tempfile.gettempdir()

    safe_name = sanitize_filename(original_filename)
    base_name = os.path.splitext(safe_name)[0]
    file_extension = os.path.splitext(safe_name)[1]

    # Generate unique filename: original_name + UUID suffix + extension
    # This preserves the original name while ensuring uniqueness
    unique_suffix = uuid.uuid4().hex[:6]  # Use first 6 chars of UUID for shorter names
    unique_filename = f"{base_name}_{unique_suffix}{file_extension}"
    base_dir = Path(temp_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = (base_dir / unique_filename).resolve()
    temp_file_path.relative_to(base_dir)

    return str(temp_file_path), unique_filename
