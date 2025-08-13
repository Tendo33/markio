from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PowerpointFormatOption
from docling_core.types.doc import ImageRefMode

from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def pptx_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
):
    """
    Parse Microsoft PowerPoint PPTX files and convert to Markdown format using Docling.

    This parser handles PPTX files and converts them to Markdown while preserving:
    - Text formatting and structure
    - Tables and lists
    - Images (when save_parsed_content is True)
    - Document metadata

    Args:
        pptx_file_path: Path to the PPTX file to be parsed
        save_parsed_content: Whether to save parsed markdown content to file
        output_dir: Directory where parsed content and images will be saved

    Returns:
        str: Parsed content in Markdown format

    Raises:
        FileNotFoundError: If file not found or not accessible
        ValueError: If required parameters missing when save_parsed_content is True
        Exception: For other errors during parsing or conversion
    """
    local_pptx_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_pptx_path)
    file_name = file_path.stem

    if save_parsed_content:
        output_dir = Path(output_dir)
        save_parsed_dir = output_dir / file_name
        save_parsed_dir.mkdir(parents=True, exist_ok=True)
        output_path = save_parsed_dir / f"{file_name}.md"

        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True

        pptx_converter = DocumentConverter(
            format_options={
                InputFormat.PPTX: PowerpointFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )

        conv_res = pptx_converter.convert(local_pptx_path)
        conv_res.document.save_as_markdown(
            output_path, image_mode=ImageRefMode.REFERENCED
        )
        logger.info(f"PPTX {file_name} saved to {output_path}")
    else:
        pptx_converter = DocumentConverter()
        conv_res = pptx_converter.convert(local_pptx_path)

    markdown_content = conv_res.document.export_to_markdown()
    return markdown_content
