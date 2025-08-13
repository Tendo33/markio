import copy
import json
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException
from mineru.backend.pipeline.model_json_to_middle_json import (
    result_to_middle_json as pipeline_result_to_middle_json,
)
from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import (
    union_make as pipeline_union_make,
)
from mineru.cli.common import (
    convert_pdf_bytes_to_bytes_by_pypdfium2,
)
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.utils.draw_bbox import draw_layout_bbox, draw_span_bbox
from mineru.utils.enum_class import MakeMode

from markio.schemas.parsers_schemas import PDF_PARSE_LANG, PDF_PARSE_TYPE
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


@func_processing_time
async def pdf_parse_main(
    resource_path: str = "",
    parse_method: str = PDF_PARSE_TYPE.auto,
    lang: str = PDF_PARSE_LANG.ch,
    save_parsed_content: bool = False,
    save_middle_content: bool = False,
    output_dir: str = "outputs",
    start_page: int = 0,
    end_page: int = None,
):
    """
    Parse PDF files and convert to Markdown format with optional JSON output.

    Supports multiple parsing methods for various PDF types:
    - Text-based PDFs (text extraction)
    - Scanned PDFs (OCR processing)
    - Mixed PDFs (auto-detection)

    Features:
    - Automatic PDF type detection
    - OCR support for scanned documents
    - Table and formula detection
    - Image extraction and reference
    - Layout preservation
    - Page range selection
    - Optional intermediate output files

    Args:
        pdf_file_path: Path to PDF file
        parse_method: Parsing method ('auto', 'ocr', 'txt')
        save_parsed_content: Whether to save parsed content
        save_middle_content: Whether to save intermediate results
        output_dir: Output directory for saved content
        start_page: First page to parse (0-based)
        end_page: Last page to parse (inclusive)

    Returns:
        str: Parsed markdown content

    Raises:
        FileNotFoundError: If file not found
        ValueError: If parameters are invalid
        HTTPException: For processing errors
    """
    local_pdf_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_pdf_path)
    file_name = file_path.stem

    output_path = ""

    with open(local_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    if start_page > 0 or end_page is not None:
        pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(
            pdf_bytes=pdf_bytes, start_page_id=start_page, end_page_id=end_page
        )

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
        output_path = temp_dir
        local_image_dir = os.path.join(temp_dir, file_name, f"{file_name}_artifacts")
        os.makedirs(local_image_dir, exist_ok=True)
        local_md_dir = os.path.join(temp_dir, file_name)
        os.makedirs(local_md_dir, exist_ok=True)
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)

    try:
        infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = (
            pipeline_doc_analyze(
                pdf_bytes_list=[pdf_bytes],
                lang_list=[lang],
                parse_method=parse_method,
                formula_enable=True,
                table_enable=True,
            )
        )

        model_list = infer_results[0]
        images_list = all_image_lists[0]
        pdf_doc = all_pdf_docs[0]
        _lang = lang_list[0]
        _ocr_enable = ocr_enabled_list[0]

        middle_json = pipeline_result_to_middle_json(
            model_list,
            images_list,
            pdf_doc,
            image_writer,
            _lang,
            _ocr_enable,
            True,
        )

        pdf_info = middle_json["pdf_info"]

        image_dir = str(os.path.basename(local_image_dir))
        markdown_content = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)

        content_list_content = pipeline_union_make(
            pdf_info, MakeMode.CONTENT_LIST, image_dir
        )

        if save_parsed_content:
            md_writer.write_string(f"{file_name}.md", markdown_content)

            md_writer.write_string(
                f"{file_name}_content_list.json",
                json.dumps(content_list_content, ensure_ascii=False, indent=4),
            )

        if save_middle_content and save_parsed_content:
            draw_layout_bbox(
                pdf_info, pdf_bytes, local_md_dir, f"{file_name}_layout.pdf"
            )

            draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{file_name}_spans.pdf")

            md_writer.write(f"{file_name}_origin.pdf", pdf_bytes)

            model_json = copy.deepcopy(model_list)
            md_writer.write_string(
                f"{file_name}_model.json",
                json.dumps(model_json, ensure_ascii=False, indent=4),
            )

            md_writer.write_string(
                f"{file_name}_middle.json",
                json.dumps(middle_json, ensure_ascii=False, indent=4),
            )

        logger.info(f"PDF {file_name} saved to {output_path}")
        return markdown_content

    except Exception as e:
        logger.error(f"Error occurred during PDF parsing: {e}")
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")
    finally:
        if not save_parsed_content:
            import shutil

            try:
                shutil.rmtree(os.path.dirname(local_image_dir))
                shutil.rmtree(os.path.dirname(local_md_dir))
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")
