import json
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException
from mineru.backend.vlm.vlm_analyze import aio_doc_analyze as aio_vlm_doc_analyze
from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
from mineru.cli.common import (
    convert_pdf_bytes_to_bytes_by_pypdfium2,
)
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.utils.draw_bbox import draw_layout_bbox
from mineru.utils.enum_class import MakeMode

from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def pdf_parse_vlm_main(
    resource_path: str = "",
    parse_method: str = "",  # Unused parameter for compatibility
    lang: str = "ch",  # Unused parameter for compatibility
    save_parsed_content: bool = False,
    save_middle_content: bool = False,
    output_dir: str = "",
    start_page: int = 0,
    end_page: int = None,
    server_url: str = None,
):
    """
    Parse PDF files using VLM (Vision Language Model) backend and convert to Markdown format.

    This parser uses VLM-based approach for PDF parsing, which is particularly effective for:
    - Complex document layouts
    - Mixed content (text, images, tables, formulas)
    - Documents with rich visual elements
    - High-quality OCR and content understanding

    Features:
    - VLM-based document understanding
    - Advanced OCR capabilities
    - Table and formula detection
    - Image extraction and reference
    - Layout preservation
    - Page range selection
    - Automatic backend selection based on server_url

    Args:
        pdf_file_path: Path to the PDF file to be parsed or URL
        parse_method: Unused parameter for compatibility
        lang: Unused parameter for compatibility
        save_parsed_content: Whether to save parsed content to files
        save_middle_content: Whether to save intermediate processing results
        output_dir: Directory where parsed content and images will be saved
        start_page: First page to parse (0-based indexing)
        end_page: Last page to parse (inclusive)
        server_url: Server URL for sglang-client backend.
            If provided, uses sglang-client backend; otherwise uses sglang-engine backend.
    Returns:
        str: Parsed content in Markdown format

    Raises:
        FileNotFoundError: If file not found or not accessible
        ValueError: If required parameters missing
        HTTPException: For errors during file operations or parsing
        Exception: For other errors during parsing or conversion
    """
    local_pdf_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    # Get backend and server_url from configuration
    from markio.settings import settings

    engine = settings.pdf_parse_engine.lower()
    if engine == "vlm-sglang-client":
        backend = "sglang-client"
    else:
        backend = "sglang-engine"

    # Extract file name from the file path
    file_path = Path(local_pdf_path)
    file_name = file_path.stem  # Get filename without extension

    # Initialize output_path variable
    output_path = ""

    # Read PDF file
    with open(local_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Convert PDF bytes for page range if specified
    if start_page > 0 or end_page is not None:
        pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(
            pdf_bytes=pdf_bytes, start_page_id=start_page, end_page_id=end_page
        )

    # Setup output directories
    if save_parsed_content:
        output_path = os.path.join(output_dir, file_name)
        local_image_dir = os.path.join(output_path, file_name, f"{file_name}_artifacts")
        os.makedirs(local_image_dir, exist_ok=True)
        local_md_dir = os.path.join(output_path, file_name)
        os.makedirs(local_md_dir, exist_ok=True)
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)
    else:
        temp_dir = tempfile.mkdtemp()
        output_path = temp_dir  # Set output_path for temporary directory case
        local_image_dir = os.path.join(temp_dir, file_name, f"{file_name}_artifacts")
        os.makedirs(local_image_dir, exist_ok=True)
        local_md_dir = os.path.join(temp_dir, file_name)
        os.makedirs(local_md_dir, exist_ok=True)
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)

    try:
        # Run VLM analysis using async aio_doc_analyze (no ThreadPoolExecutor)
        middle_json, infer_result = await aio_vlm_doc_analyze(
            pdf_bytes=pdf_bytes,
            image_writer=image_writer,
            backend=backend,
            server_url=server_url,
        )

        pdf_info = middle_json["pdf_info"]

        # Generate markdown content
        image_dir = str(os.path.basename(local_image_dir))
        markdown_content = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)

        # Generate content list
        content_list_content = vlm_union_make(
            pdf_info, MakeMode.CONTENT_LIST, image_dir
        )

        # Save parsed content if requested
        if save_parsed_content:
            # Save markdown content
            md_writer.write_string(f"{file_name}.md", markdown_content)

            # Save content list JSON
            md_writer.write_string(
                f"{file_name}_content_list.json",
                json.dumps(content_list_content, ensure_ascii=False, indent=4),
            )

        # Handle middle content visualization
        if save_middle_content and save_parsed_content:
            # Draw layout bounding boxes
            draw_layout_bbox(
                pdf_info, pdf_bytes, local_md_dir, f"{file_name}_layout.pdf"
            )

            # Note: VLM backend doesn't support span bounding boxes
            # draw_span_bbox is not available for VLM

            # Save original PDF
            md_writer.write(f"{file_name}_origin.pdf", pdf_bytes)

            # Save model output (VLM specific format)
            model_output = ("\n" + "-" * 50 + "\n").join(infer_result)
            md_writer.write_string(
                f"{file_name}_model_output.txt",
                model_output,
            )

            # Save middle JSON
            md_writer.write_string(
                f"{file_name}_middle.json",
                json.dumps(middle_json, ensure_ascii=False, indent=4),
            )

        logger.info(f"PDF {file_name} saved to {output_path}")
        return markdown_content

    except Exception as e:
        logger.error(f"Error occurred during VLM PDF parsing: {e}")
        raise HTTPException(status_code=500, detail=f"VLM PDF parsing failed: {str(e)}")
    finally:
        # Clean up temporary directories if not saving content
        if not save_parsed_content:
            import shutil

            try:
                shutil.rmtree(os.path.dirname(local_image_dir))
                shutil.rmtree(os.path.dirname(local_md_dir))
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")


@func_processing_time
async def pdf_parse_vlm_batch(
    pdf_file_paths: list[str],
    save_parsed_content: bool = False,
    save_middle_content: bool = False,
    output_dir: str = "",
    start_page: int = 0,
    end_page: int = None,
    server_url: str = None,
):
    """
    Parse multiple PDF files using VLM backend in batch mode.

    This function processes multiple PDF files using the VLM backend, which is more efficient
    than processing them individually when dealing with multiple documents.

    Args:
        pdf_file_paths (list[str]): List of paths to PDF files to be parsed.
        save_parsed_content (bool, optional): Whether to save parsed content to files.
        save_middle_content (bool, optional): Whether to save intermediate results.
        output_dir (str, optional): Directory for saving output files.
        start_page (int, optional): First page to parse (0-based indexing).
        end_page (int, optional): Last page to parse (inclusive).
        server_url (str, optional): Server URL for sglang-client backend.
            If provided, uses sglang-client backend; otherwise uses sglang-engine backend.

    Returns:
        list[str]: List of parsed markdown contents for each PDF file.

    Raises:
        ValueError: If no valid PDF files are provided.
        HTTPException: If there are errors during batch processing.
    """
    if not pdf_file_paths:
        raise ValueError("No PDF file paths provided")

    results = []

    for pdf_file_path in pdf_file_paths:
        try:
            result = await pdf_parse_vlm_main(
                pdf_file_path=pdf_file_path,
                save_parsed_content=save_parsed_content,
                save_middle_content=save_middle_content,
                output_dir=output_dir,
                start_page=start_page,
                end_page=end_page,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to parse {pdf_file_path}: {e}")
            # Continue with other files, but log the error
            results.append(f"Error parsing {pdf_file_path}: {str(e)}")

    return results
