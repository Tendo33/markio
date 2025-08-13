import os
import tempfile
from pathlib import Path

from markio.parsers.pdf_parser import pdf_parse_main
from markio.parsers.pdf_parser_vlm import pdf_parse_vlm_main
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

# Supported image formats for conversion
image_suffixes = [".png", ".jpeg", ".jpg"]
logger = get_logger(__name__)


def image_to_pdf(path):
    """Convert image to PDF format using MinerU tools"""
    if not isinstance(path, Path):
        path = Path(path)
    with open(str(path), "rb") as input_file:
        file_bytes = input_file.read()
        if path.suffix in image_suffixes:
            from mineru.utils.pdf_image_tools import images_bytes_to_pdf_bytes

            return images_bytes_to_pdf_bytes(file_bytes)
        else:
            raise Exception(f"Unknown file suffix: {path.suffix}")


@func_processing_time
async def image_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
    parse_backend: str = "pipeline",
):
    """
    Parse images or PDFs and convert to Markdown format.

    Images are first converted to PDF then processed through pipeline or VLM flow.
    Supports local file paths and URLs.

    Args:
        img_file_path: Image or PDF path or URL
        save_parsed_content: Whether to save markdown output
        output_dir: Output directory for saved content
        parse_backend: 'pipeline' or 'vlm' parsing engine

    Returns:
        str: Parsed markdown content

    Raises:
        FileNotFoundError: If file not found
        ValueError: If parse_backend is invalid
        HTTPException: For processing errors
    """
    local_img_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_img_path)

    if not os.path.exists(local_img_path):
        raise FileNotFoundError(f"Image/PDF file not found at {local_img_path}.")

    is_image = file_path.suffix.lower() in image_suffixes
    temp_pdf_path = None
    try:
        if is_image:
            pdf_bytes = image_to_pdf(local_img_path)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                tmp_pdf.write(pdf_bytes)
                temp_pdf_path = tmp_pdf.name
            pdf_file_path = temp_pdf_path
        else:
            pdf_file_path = local_img_path

        if parse_backend == "pipeline":
            result = await pdf_parse_main(
                pdf_file_path=pdf_file_path,
                parse_method="auto",
                save_parsed_content=save_parsed_content,
                save_middle_content=False,
                output_dir=output_dir,
            )
        elif parse_backend == "vlm":
            result = await pdf_parse_vlm_main(
                pdf_file_path=pdf_file_path,
                parse_method="auto",
                save_parsed_content=save_parsed_content,
                save_middle_content=False,
                output_dir=output_dir,
            )
        else:
            raise ValueError(f"Unknown parse_backend: {parse_backend}")
        return result
    except Exception as e:
        logger.error(f"Image parsing failed: {e}")
        raise
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.unlink(temp_pdf_path)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary PDF file {temp_pdf_path}: {e}"
                )
