from __future__ import annotations

import asyncio
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
from mineru.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.utils.draw_bbox import draw_layout_bbox, draw_span_bbox
from mineru.utils.enum_class import MakeMode

from markio.schemas.parsers_schemas import PDF_PARSE_LANG, PDF_PARSE_TYPE
from markio.settings import settings
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)

_VLM_WARMUP_LOCK = asyncio.Lock()
_VLM_WARMED_KEYS: set[str] = set()


def _normalize_backend(raw_backend: str | None) -> str:
    backend = (raw_backend or settings.pdf_parse_engine).lower()
    alias_map = {
        "vlm-vllm-engine": "vlm-auto-engine",
        "vlm-vllm-client": "vlm-http-client",
    }
    return alias_map.get(backend, backend)


def _prepare_output_dirs(
    file_name: str,
    save_parsed_content: bool,
    output_dir: str,
) -> tuple[str, str, str, FileBasedDataWriter, FileBasedDataWriter]:
    if save_parsed_content:
        base_dir = os.path.join(output_dir, file_name)
    else:
        base_dir = tempfile.mkdtemp(prefix="markio_pdf_")

    local_image_dir = os.path.join(base_dir, file_name, f"{file_name}_artifacts")
    local_md_dir = os.path.join(base_dir, file_name)
    os.makedirs(local_image_dir, exist_ok=True)
    os.makedirs(local_md_dir, exist_ok=True)

    image_writer = FileBasedDataWriter(local_image_dir)
    md_writer = FileBasedDataWriter(local_md_dir)
    return base_dir, local_image_dir, local_md_dir, image_writer, md_writer


def _run_pipeline(
    pdf_bytes: bytes,
    lang: str,
    parse_method: str,
    image_writer: FileBasedDataWriter,
):
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
    middle_json = pipeline_result_to_middle_json(
        model_list,
        images_list,
        pdf_doc,
        image_writer,
        lang_list[0],
        ocr_enabled_list[0],
        True,
    )

    return middle_json, model_list, "pipeline"


def _run_vlm_or_hybrid(
    backend: str,
    pdf_bytes: bytes,
    lang: str,
    parse_method: str,
    image_writer: FileBasedDataWriter,
    server_url: str | None,
):
    from mineru.backend.hybrid.hybrid_analyze import doc_analyze as hybrid_doc_analyze
    from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
    from mineru.utils.engine_utils import get_vlm_engine

    if backend.startswith("vlm-"):
        runtime_backend = backend[4:]
        if runtime_backend == "auto-engine":
            runtime_backend = get_vlm_engine(inference_engine="auto", is_async=False)
        if runtime_backend == "http-client" and not server_url:
            raise ValueError("VLM server_url is required for vlm-http-client")

        middle_json, infer_result = vlm_doc_analyze(
            pdf_bytes,
            image_writer=image_writer,
            backend=runtime_backend,
            server_url=server_url,
        )
        return middle_json, infer_result, "vlm"

    if backend.startswith("hybrid-"):
        runtime_backend = backend[7:]
        if runtime_backend == "auto-engine":
            runtime_backend = get_vlm_engine(inference_engine="auto", is_async=False)
        if runtime_backend == "http-client" and not server_url:
            raise ValueError("VLM server_url is required for hybrid-http-client")

        middle_json, infer_result, _ = hybrid_doc_analyze(
            pdf_bytes,
            image_writer=image_writer,
            backend=runtime_backend,
            parse_method=parse_method,
            language=lang,
            inline_formula_enable=True,
            server_url=server_url,
        )
        return middle_json, infer_result, "hybrid"

    raise ValueError(f"Unsupported backend: {backend}")


async def _run_vlm_or_hybrid_async(
    backend: str,
    pdf_bytes: bytes,
    lang: str,
    parse_method: str,
    image_writer: FileBasedDataWriter | None,
    server_url: str | None,
):
    warmup_key = backend

    if warmup_key in _VLM_WARMED_KEYS:
        return await asyncio.to_thread(
            _run_vlm_or_hybrid,
            backend=backend,
            pdf_bytes=pdf_bytes,
            lang=lang,
            parse_method=parse_method,
            image_writer=image_writer,
            server_url=server_url,
        )

    async with _VLM_WARMUP_LOCK:
        if warmup_key in _VLM_WARMED_KEYS:
            return await asyncio.to_thread(
                _run_vlm_or_hybrid,
                backend=backend,
                pdf_bytes=pdf_bytes,
                lang=lang,
                parse_method=parse_method,
                image_writer=image_writer,
                server_url=server_url,
            )

        result = await asyncio.to_thread(
            _run_vlm_or_hybrid,
            backend=backend,
            pdf_bytes=pdf_bytes,
            lang=lang,
            parse_method=parse_method,
            image_writer=image_writer,
            server_url=server_url,
        )
        _VLM_WARMED_KEYS.add(warmup_key)
        return result


def _build_markdown(pdf_info: dict, image_dir: str, parser_mode: str):
    if parser_mode == "pipeline":
        markdown_content = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)
        content_list_content = pipeline_union_make(
            pdf_info, MakeMode.CONTENT_LIST, image_dir
        )
        return markdown_content, content_list_content

    from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make

    markdown_content = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)
    content_list_content = vlm_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
    return markdown_content, content_list_content


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
    backend: str | None = None,
    server_url: str | None = None,
):
    local_pdf_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_pdf_path)
    file_name = file_path.stem

    with open(local_pdf_path, "rb") as source:
        pdf_bytes = source.read()

    if start_page > 0 or end_page is not None:
        pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(
            pdf_bytes=pdf_bytes,
            start_page_id=start_page,
            end_page_id=end_page,
        )

    (
        base_dir,
        local_image_dir,
        local_md_dir,
        image_writer,
        md_writer,
    ) = _prepare_output_dirs(
        file_name=file_name,
        save_parsed_content=save_parsed_content,
        output_dir=output_dir,
    )

    normalized_backend = _normalize_backend(backend)

    try:
        if normalized_backend == "pipeline":
            middle_json, model_output, parser_mode = _run_pipeline(
                pdf_bytes=pdf_bytes,
                lang=lang,
                parse_method=parse_method,
                image_writer=image_writer,
            )
        else:
            middle_json, model_output, parser_mode = await _run_vlm_or_hybrid_async(
                backend=normalized_backend,
                pdf_bytes=pdf_bytes,
                lang=lang,
                parse_method=parse_method,
                image_writer=image_writer,
                server_url=server_url or settings.vlm_server_url,
            )

        pdf_info = middle_json["pdf_info"]
        image_dir = str(os.path.basename(local_image_dir))
        markdown_content, content_list_content = _build_markdown(
            pdf_info=pdf_info,
            image_dir=image_dir,
            parser_mode=parser_mode,
        )

        if save_parsed_content:
            md_writer.write_string(f"{file_name}.md", markdown_content)
            md_writer.write_string(
                f"{file_name}_content_list.json",
                json.dumps(content_list_content, ensure_ascii=False, indent=4),
            )

        if save_middle_content and save_parsed_content:
            draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{file_name}_layout.pdf")
            if parser_mode == "pipeline":
                draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{file_name}_spans.pdf")

            md_writer.write(f"{file_name}_origin.pdf", pdf_bytes)
            md_writer.write_string(
                f"{file_name}_model.json",
                json.dumps(copy.deepcopy(model_output), ensure_ascii=False, indent=4, default=str),
            )
            md_writer.write_string(
                f"{file_name}_middle.json",
                json.dumps(middle_json, ensure_ascii=False, indent=4),
            )

        logger.info(
            f"PDF {file_name} parsed successfully with backend={normalized_backend}"
        )
        return markdown_content

    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error occurred during PDF parsing: {exc}")
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(exc)}")
    finally:
        if not save_parsed_content:
            import shutil

            try:
                shutil.rmtree(base_dir, ignore_errors=True)
            except Exception as cleanup_error:  # noqa: BLE001
                logger.warning(f"Failed to clean up temporary directory: {cleanup_error}")
