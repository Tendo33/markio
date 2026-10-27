"""PDF parsing on top of the MinerU 4 ``mineru.parser`` API.

MinerU 4 replaced the old pipeline/vlm/hybrid backend modules with a single
``MinerUParser`` that is configured by a quality *tier* and a ``VlmConfig``.
markio keeps its own engine names (``PDF_PARSE_ENGINE``) and maps them here:

* ``pipeline``                         -> tier ``basic`` (small ONNX/torch models, no VLM)
* ``vlm-engine`` / ``hybrid-engine``   -> tier ``standard`` with a local VLM engine
* ``vlm-http-client`` / ``hybrid-http-client`` -> tier ``standard`` with ``VlmConfig.server_url``
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from markio.schemas.parsers_schemas import PDF_PARSE_LANG, PDF_PARSE_TYPE
from markio.settings import settings
from markio.settings.config_model import (
    PIPELINE_PDF_ENGINE,
    VLM_PDF_ENGINES,
    normalize_pdf_engine,
)
from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)

_VLM_WARMUP_LOCK = asyncio.Lock()
_VLM_WARMED_KEYS: set[str] = set()

PIPELINE_TIER = "basic"
VLM_TIER = "standard"
_PARSE_MODES = {"auto", "txt", "ocr"}


def _normalize_backend(raw_backend: str | None) -> str:
    backend = normalize_pdf_engine(raw_backend or settings.pdf_parse_engine)
    if backend != PIPELINE_PDF_ENGINE and backend not in VLM_PDF_ENGINES:
        raise ValueError(f"Unsupported backend: {backend}")
    return backend


def tier_for_backend(backend: str) -> str:
    """Map a canonical markio engine name onto a MinerU 4 tier."""
    return PIPELINE_TIER if backend == PIPELINE_PDF_ENGINE else VLM_TIER


def build_vlm_config(backend: str, server_url: str | None = None, api_key: str | None = None):
    """Build the MinerU 4 ``VlmConfig`` for a markio engine, or None for pipeline.

    Starts from MinerU's global VLM config so ``MINERU_*`` settings (engine, model,
    api_key, timeouts) are kept; markio only overrides ``server_url`` / ``api_key``.
    """
    if backend == PIPELINE_PDF_ENGINE:
        return None
    from mineru.config import config as mineru_config

    base = mineru_config.model.vlm
    if backend.endswith("-http-client"):
        if not server_url:
            raise ValueError(f"VLM server_url is required for {backend}")
        update = {"server_url": server_url}
        key = api_key if api_key is not None else settings.vlm_api_key
        if key:
            update["api_key"] = key
        return base.model_copy(update=update)
    # Local engines: never talk to a remote server.
    return base.model_copy(update={"server_url": ""})


def page_range_from_pages(start_page: int = 0, end_page: int | None = None) -> str:
    """Translate markio's 0-based inclusive start/end pages to MinerU's 1-based range."""
    start = max(int(start_page or 0), 0)
    if end_page is None:
        return "" if start == 0 else f"{start + 1}-r1"
    end = int(end_page)
    if end < start:
        raise ValueError(f"end_page ({end}) must be >= start_page ({start})")
    return f"{start + 1}-{end + 1}"


def _parse_mode(parse_method: str | None) -> str:
    mode = getattr(parse_method, "value", parse_method) or "auto"
    if mode not in _PARSE_MODES:
        raise ValueError(f"Unsupported parse_method: {mode}")
    return mode


def _run_parse(
    pdf_path: str,
    *,
    backend: str,
    parse_method: str,
    page_range: str,
    server_url: str | None,
):
    """Run MinerU synchronously and return its ``ParseResult``."""
    from mineru.parser import MinerUParser

    parser = MinerUParser(
        tier=tier_for_backend(backend),
        parse_mode=_parse_mode(parse_method),
        vlm_config=build_vlm_config(backend, server_url),
    )
    try:
        return parser.parse(pdf_path, page_range=page_range)
    finally:
        parser.close()


async def _run_parse_async(**kwargs):
    """Offload parsing to a thread; serialize the first (warm-up) call per VLM backend."""
    backend = kwargs["backend"]
    if backend == PIPELINE_PDF_ENGINE or backend in _VLM_WARMED_KEYS:
        return await asyncio.to_thread(_run_parse, **kwargs)

    async with _VLM_WARMUP_LOCK:
        if backend in _VLM_WARMED_KEYS:
            return await asyncio.to_thread(_run_parse, **kwargs)
        result = await asyncio.to_thread(_run_parse, **kwargs)
        _VLM_WARMED_KEYS.add(backend)
        return result


def _prepare_output_dirs(
    file_name: str, save_parsed_content: bool, output_dir: str
) -> tuple[str, str, str]:
    if save_parsed_content:
        base_dir = os.path.join(output_dir, file_name)
    else:
        base_dir = tempfile.mkdtemp(prefix="markio_pdf_")

    local_md_dir = os.path.join(base_dir, file_name)
    local_image_dir = os.path.join(local_md_dir, f"{file_name}_artifacts")
    os.makedirs(local_image_dir, exist_ok=True)
    return base_dir, local_image_dir, local_md_dir


def _export_result(result, image_dir_name: str) -> tuple[str, Any, dict, dict[str, bytes]]:
    """Externalize images and render markdown that points at ``image_dir_name/``.

    Returns (markdown, structured_content, middle_json_dict, assets).
    """
    from docvortex.export import materialize_middle
    from mineru.parser import ParseResult

    middle_json, assets = materialize_middle(result.middle_json)
    exported = ParseResult(middle_json=middle_json)
    base_url = f"{image_dir_name}/" if image_dir_name else ""
    markdown = exported.markdown(asset_base_url=base_url)
    content_list = exported.structured_content(asset_base_url=base_url)
    return markdown, content_list, exported.to_dict(), dict(assets.items())


def _write_bytes(root: str, rel_path: str, data: bytes) -> None:
    target = os.path.normpath(os.path.join(root, rel_path))
    if not target.startswith(os.path.normpath(root) + os.sep):
        raise ValueError(f"Refusing to write asset outside output dir: {rel_path}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(data)


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
    """Parse a PDF into markdown.

    ``lang`` is accepted for API compatibility only: MinerU 4 selects the OCR
    language model automatically and no longer exposes a per-call language.
    """
    local_pdf_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )
    file_name = Path(local_pdf_path).stem
    base_dir, local_image_dir, local_md_dir = _prepare_output_dirs(
        file_name=file_name,
        save_parsed_content=save_parsed_content,
        output_dir=output_dir,
    )

    try:
        normalized_backend = _normalize_backend(backend)
        page_range = page_range_from_pages(start_page, end_page)
        if lang and str(getattr(lang, "value", lang)) != PDF_PARSE_LANG.ch.value:
            logger.debug("lang=%s ignored: MinerU 4 auto-selects the OCR language", lang)

        result = await _run_parse_async(
            pdf_path=str(local_pdf_path),
            backend=normalized_backend,
            parse_method=parse_method,
            page_range=page_range,
            server_url=server_url or settings.vlm_server_url,
        )

        image_dir_name = os.path.basename(local_image_dir)
        markdown_content, content_list, middle_dict, assets = _export_result(
            result, image_dir_name
        )

        if save_parsed_content:
            for rel_path, payload in assets.items():
                _write_bytes(local_image_dir, rel_path, payload)
            with open(os.path.join(local_md_dir, f"{file_name}.md"), "w", encoding="utf-8") as f:
                f.write(markdown_content)
            with open(
                os.path.join(local_md_dir, f"{file_name}_content_list.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(content_list, f, ensure_ascii=False, indent=4)

            if save_middle_content:
                shutil.copyfile(local_pdf_path, os.path.join(local_md_dir, f"{file_name}_origin.pdf"))
                with open(os.path.join(local_md_dir, f"{file_name}_middle.json"), "w", encoding="utf-8") as f:
                    json.dump(middle_dict, f, ensure_ascii=False, indent=4)
                model_output = getattr(result, "_model_output", None)
                if model_output is not None:
                    with open(os.path.join(local_md_dir, f"{file_name}_model.json"), "w", encoding="utf-8") as f:
                        json.dump(
                            model_output.to_dict(skip_defaults=False),
                            f,
                            ensure_ascii=False,
                            indent=4,
                            default=str,
                        )

        logger.info(f"PDF {file_name} parsed successfully with backend={normalized_backend}")
        return markdown_content

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Error occurred during PDF parsing: {exc}")
        raise HTTPException(status_code=500, detail="PDF parsing failed")
    finally:
        if not save_parsed_content:
            shutil.rmtree(base_dir, ignore_errors=True)
