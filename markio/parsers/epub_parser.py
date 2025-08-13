from pathlib import Path

import pypandoc

from markio.utils.file_utils import (
    func_processing_time,
    md_dump_io,
    process_resource_path,
)
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def epub_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
):
    """
    Parse EPUB files and convert to Markdown format using pypandoc.

    This parser handles EPUB files and converts them to Markdown while preserving:
    - Text formatting and structure
    - Tables and lists
    - Images (when save_parsed_content is True)
    - Document metadata

    Args:
        epub_file_path: Path to the EPUB file to be parsed
        save_parsed_content: Whether to save parsed markdown content to file
        output_dir: Directory where parsed content and images will be saved

    Returns:
        str: Parsed content in Markdown format

    Raises:
        FileNotFoundError: If file not found or not accessible
        ValueError: If required parameters missing when save_parsed_content is True
        Exception: For other errors during parsing or conversion
    """
    local_epub_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_epub_path)
    file_name = file_path.stem

    if save_parsed_content:
        output_dir = Path(output_dir)
        save_parsed_dir = output_dir / file_name
        save_parsed_dir.mkdir(parents=True, exist_ok=True)
        output_path = save_parsed_dir / f"{file_name}.md"

        markdown_content = pypandoc.convert_file(
            source_file=local_epub_path,
            to="markdown",
            format="epub",
            extra_args=["--extract-media=" + f"{Path(output_path).resolve()}/images"],
            verify_format=True,
        )
        await md_dump_io(
            md_content=markdown_content, output_path=output_path, file_name=file_name
        )
        logger.info(f"EPUB {file_name} saved to {output_path}")
    else:
        markdown_content = pypandoc.convert_file(
            source_file=local_epub_path,
            to="markdown",
            format="epub",
            verify_format=True,
        )

    return markdown_content
