from markio.parsers.docx_parser import docx_parse_main
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.libreoffice_converter import convert_by_libreoffice
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def doc_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
):
    """
    Parse DOC files and convert to Markdown format using Docling.

    This parser handles DOC files and converts them to Markdown, automatically saving images (when save_parsed_content is True).
    Supports both local file paths and URLs - URLs will be automatically downloaded before processing.

    Args:
        doc_file_path: DOC file path or URL
        save_parsed_content: Whether to save parsed content (automatically saves images when True)
        output_dir: Output directory

    Returns:
        str: Markdown content
    """
    local_doc_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    converted_docx_path = await convert_by_libreoffice(
        input_path=local_doc_path,
        output_format="docx",
        rm_original=False,
    )

    parsed_content = await docx_parse_main(
        resource_path=converted_docx_path,
        save_parsed_content=save_parsed_content,
        output_dir=output_dir,
    )

    logger.info("DOC file parsed successfully, preparing to return result")
    return parsed_content
