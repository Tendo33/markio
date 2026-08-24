import asyncio

import pytest
from fastapi import HTTPException

from markio.parsers import pdf_parser


@pytest.mark.asyncio
async def test_vlm_parse_runs_via_thread_offload(monkeypatch):
    calls = []

    async def fake_to_thread(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return func(*args, **kwargs)

    def fake_run(**kwargs):
        return {"pdf_info": {}}, {"model": "ok"}, "vlm"

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(pdf_parser, "_run_vlm_or_hybrid", fake_run)
    pdf_parser._VLM_WARMED_KEYS.clear()

    result = await pdf_parser._run_vlm_or_hybrid_async(
        backend="vlm-auto-engine",
        pdf_bytes=b"demo",
        lang="ch",
        parse_method="auto",
        image_writer=None,
        server_url=None,
    )

    assert result[2] == "vlm"
    assert len(calls) == 1
    assert calls[0][0] is fake_run


@pytest.mark.asyncio
async def test_vlm_warmup_failure_does_not_mark_backend_ready(monkeypatch):
    attempts = {"count": 0}

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    def flaky_run(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("warmup failed")
        return {"pdf_info": {}}, {"model": "ok"}, "vlm"

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(pdf_parser, "_run_vlm_or_hybrid", flaky_run)
    pdf_parser._VLM_WARMED_KEYS.clear()

    with pytest.raises(RuntimeError):
        await pdf_parser._run_vlm_or_hybrid_async(
            backend="vlm-auto-engine",
            pdf_bytes=b"demo",
            lang="ch",
            parse_method="auto",
            image_writer=None,
            server_url=None,
        )

    assert "vlm-auto-engine" not in pdf_parser._VLM_WARMED_KEYS

    result = await pdf_parser._run_vlm_or_hybrid_async(
        backend="vlm-auto-engine",
        pdf_bytes=b"demo",
        lang="ch",
        parse_method="auto",
        image_writer=None,
        server_url=None,
    )
    assert result[2] == "vlm"
    assert attempts["count"] == 2
    assert "vlm-auto-engine" in pdf_parser._VLM_WARMED_KEYS


@pytest.mark.asyncio
async def test_pdf_parse_returns_generic_http_500_error(monkeypatch, tmp_path):
    pdf_path = tmp_path / "boom.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake")

    async def fake_process_resource_path(resource_path: str, output_dir=None):
        return resource_path

    def fake_prepare_output_dirs(
        file_name: str, save_parsed_content: bool, output_dir: str
    ):
        base_dir = tmp_path / "runtime"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir, base_dir / "images", base_dir / "md", None, None

    def fake_run_pipeline(**kwargs):
        raise RuntimeError("internal parse stack details")

    monkeypatch.setattr(pdf_parser, "process_resource_path", fake_process_resource_path)
    monkeypatch.setattr(pdf_parser, "_prepare_output_dirs", fake_prepare_output_dirs)
    monkeypatch.setattr(pdf_parser, "_run_pipeline", fake_run_pipeline)

    with pytest.raises(HTTPException) as exc:
        await pdf_parser.pdf_parse_main(
            resource_path=str(pdf_path),
            backend="pipeline",
            save_parsed_content=False,
            output_dir=str(tmp_path),
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "PDF parsing failed"


def test_run_pipeline_uses_streaming_api_and_collects_result(monkeypatch):
    import sys

    calls = {"kw": None}

    def fake_streaming(
        *, pdf_bytes_list, image_writer_list, lang_list, on_doc_ready, **_kw
    ):
        calls["kw"] = {
            "pdf_bytes_list": pdf_bytes_list,
            "image_writer_list": image_writer_list,
            "lang_list": lang_list,
        }
        # Simulate MinerU invoking the callback with a finalized middle_json.
        on_doc_ready(
            0,
            ["model-block-1"],
            {"pdf_info": [{"preproc_blocks": []}]},
            True,
        )

    fake_module = type(
        "_fake_pipeline",
        (),
        {"doc_analyze_streaming": staticmethod(fake_streaming)},
    )()
    monkeypatch.setitem(
        sys.modules,
        "mineru.backend.pipeline.pipeline_analyze",
        fake_module,
    )
    monkeypatch.setattr(pdf_parser, "mineru_normalize_backend", lambda b: b)

    middle_json, model_list, mode = pdf_parser._run_pipeline(
        pdf_bytes=b"%PDF-demo",
        lang="en",
        parse_method="ocr",
        image_writer="writer",
    )

    assert mode == "pipeline"
    assert calls["kw"]["pdf_bytes_list"] == [b"%PDF-demo"]
    assert calls["kw"]["lang_list"] == ["en"]
    assert model_list == ["model-block-1"]
    assert middle_json == {"pdf_info": [{"preproc_blocks": []}]}


def test_normalize_backend_supports_legacy_and_new_names(monkeypatch):
    from mineru.cli.backend_options import normalize_backend as real_normalize

    monkeypatch.setattr(pdf_parser, "mineru_normalize_backend", real_normalize)

    assert pdf_parser._normalize_backend("pipeline") == "pipeline"
    assert pdf_parser._normalize_backend("vlm-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("hybrid-engine") == "hybrid-engine"
    # legacy aliases map to current names
    assert pdf_parser._normalize_backend("vlm-vllm-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("vlm-vllm-client") == "vlm-http-client"
    assert pdf_parser._normalize_backend("vlm-auto-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("hybrid-auto-engine") == "hybrid-engine"


def test_every_accepted_engine_value_is_dispatchable():
    """Guards against a value passing config validation but hitting no dispatch branch.

    Both mcp_server and run_local route on the normalized name, so anything the
    PDF_PARSE_ENGINE Literal accepts must normalize into a known engine.
    """
    from typing import get_args

    from markio.settings.config_model import (
        PIPELINE_PDF_ENGINE,
        VLM_PDF_ENGINES,
        ApplicationConfig,
        normalize_pdf_engine,
    )

    accepted = get_args(ApplicationConfig.model_fields["pdf_parse_engine"].annotation)
    assert accepted, "pdf_parse_engine should stay a Literal of accepted values"

    for value in accepted:
        normalized = normalize_pdf_engine(value)
        assert normalized == PIPELINE_PDF_ENGINE or normalized in VLM_PDF_ENGINES, (
            f"{value!r} normalizes to {normalized!r}, which no dispatch site handles"
        )


def test_run_pipeline_raises_when_callback_never_fires(monkeypatch):
    import sys

    def fake_streaming(**_kw):
        return None  # never invokes on_doc_ready

    fake_module = type(
        "_fake_pipeline",
        (),
        {"doc_analyze_streaming": staticmethod(fake_streaming)},
    )()
    monkeypatch.setitem(
        sys.modules,
        "mineru.backend.pipeline.pipeline_analyze",
        fake_module,
    )

    with pytest.raises(RuntimeError, match="on_doc_ready was never called"):
        pdf_parser._run_pipeline(
            pdf_bytes=b"%PDF-demo",
            lang="en",
            parse_method="ocr",
            image_writer="writer",
        )
