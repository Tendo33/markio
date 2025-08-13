from markio.parsers.pptx_parser import pptx_parse_main
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.libreoffice_converter import convert_by_libreoffice
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def ppt_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
):
    """
    Parse PPT files and convert to Markdown format using Docling.

    This parser handles PPT files and converts them to Markdown, automatically saving images (when save_parsed_content is True).
    Supports both local file paths and URLs - URLs will be automatically downloaded before processing.

    Args:
        ppt_file_path (str): PPT file path or URL
        save_parsed_content (bool, optional): Whether to save parsed content (automatically saves images when True)
        output_dir (str, optional): Output directory

    Returns:
        str: Markdown content
    """
    # Process file path or URL - download if necessary
    local_ppt_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    # Use LibreOffice to convert PPT to PPTX
    converted_pptx_path = await convert_by_libreoffice(
        input_path=local_ppt_path,
        output_format="pptx",
        rm_original=False,
    )

    # Directly call the PPTX parsing function
    parsed_content = await pptx_parse_main(
        pptx_file_path=converted_pptx_path,
        save_parsed_content=save_parsed_content,
        output_dir=output_dir,
    )

    logger.info("PPT file parsed successfully, preparing to return the result")
    return parsed_content
