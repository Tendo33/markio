import asyncio
import sys
import types

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
        return "result"

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(pdf_parser, "_run_parse", fake_run)
    pdf_parser._VLM_WARMED_KEYS.clear()

    result = await pdf_parser._run_parse_async(
        pdf_path="x.pdf",
        backend="vlm-engine",
        parse_method="auto",
        page_range="",
        server_url=None,
    )

    assert result == "result"
    assert len(calls) == 1
    assert calls[0][0] is fake_run
    assert "vlm-engine" in pdf_parser._VLM_WARMED_KEYS


@pytest.mark.asyncio
async def test_vlm_warmup_failure_does_not_mark_backend_ready(monkeypatch):
    attempts = {"count": 0}

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    def flaky_run(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("warmup failed")
        return "ok"

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(pdf_parser, "_run_parse", flaky_run)
    pdf_parser._VLM_WARMED_KEYS.clear()
    kwargs = dict(pdf_path="x.pdf", backend="vlm-engine", parse_method="auto", page_range="", server_url=None)

    with pytest.raises(RuntimeError):
        await pdf_parser._run_parse_async(**kwargs)
    assert "vlm-engine" not in pdf_parser._VLM_WARMED_KEYS

    assert await pdf_parser._run_parse_async(**kwargs) == "ok"
    assert attempts["count"] == 2
    assert "vlm-engine" in pdf_parser._VLM_WARMED_KEYS


@pytest.mark.asyncio
async def test_pdf_parse_returns_generic_http_500_error(monkeypatch, tmp_path):
    pdf_path = tmp_path / "boom.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake")

    async def fake_process_resource_path(resource_path: str, output_dir=None):
        return resource_path

    def fake_run_parse(**kwargs):
        raise RuntimeError("internal parse stack details")

    monkeypatch.setattr(pdf_parser, "process_resource_path", fake_process_resource_path)
    monkeypatch.setattr(pdf_parser, "_run_parse", fake_run_parse)

    with pytest.raises(HTTPException) as exc:
        await pdf_parser.pdf_parse_main(
            resource_path=str(pdf_path),
            backend="pipeline",
            save_parsed_content=False,
            output_dir=str(tmp_path),
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "PDF parsing failed"


def _install_fake_parser(monkeypatch, record):
    class FakeParser:
        def __init__(self, **kwargs):
            record["init"] = kwargs

        def parse(self, path, *, page_range=""):
            record["parse"] = (path, page_range)
            return "parse-result"

        def close(self):
            record["closed"] = True

    fake = types.ModuleType("mineru.parser")
    fake.MinerUParser = FakeParser
    monkeypatch.setitem(sys.modules, "mineru.parser", fake)


def test_run_parse_pipeline_maps_to_basic_tier(monkeypatch):
    record = {}
    _install_fake_parser(monkeypatch, record)

    out = pdf_parser._run_parse(
        pdf_path="a.pdf", backend="pipeline", parse_method="ocr", page_range="2-3", server_url=None
    )

    assert out == "parse-result"
    assert record["init"] == {"tier": "basic", "parse_mode": "ocr", "vlm_config": None}
    assert record["parse"] == ("a.pdf", "2-3")
    assert record["closed"] is True


def test_run_parse_http_client_uses_server_url(monkeypatch):
    record = {}
    _install_fake_parser(monkeypatch, record)

    pdf_parser._run_parse(
        pdf_path="a.pdf",
        backend="hybrid-http-client",
        parse_method="auto",
        page_range="",
        server_url="http://vlm:30000/v1",
    )

    assert record["init"]["tier"] == "standard"
    assert record["init"]["vlm_config"].server_url == "http://vlm:30000/"


def test_build_vlm_config():
    assert pdf_parser.build_vlm_config("pipeline") is None
    assert pdf_parser.build_vlm_config("vlm-engine").engine == "auto"
    assert pdf_parser.build_vlm_config("vlm-engine").server_url == ""
    with pytest.raises(ValueError):
        pdf_parser.build_vlm_config("vlm-http-client", None)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [(0, None, ""), (2, None, "3-r1"), (0, 0, "1-1"), (1, 4, "2-5")],
)
def test_page_range_from_pages(start, end, expected):
    assert pdf_parser.page_range_from_pages(start, end) == expected


def test_page_range_rejects_inverted_range():
    with pytest.raises(ValueError):
        pdf_parser.page_range_from_pages(5, 2)


def test_parse_mode_validation():
    assert pdf_parser._parse_mode(None) == "auto"
    assert pdf_parser._parse_mode(pdf_parser.PDF_PARSE_TYPE.txt) == "txt"
    with pytest.raises(ValueError):
        pdf_parser._parse_mode("bogus")


def test_normalize_backend_supports_legacy_and_new_names():
    assert pdf_parser._normalize_backend("pipeline") == "pipeline"
    assert pdf_parser._normalize_backend("vlm-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("hybrid-engine") == "hybrid-engine"
    assert pdf_parser._normalize_backend("vlm-vllm-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("vlm-vllm-client") == "vlm-http-client"
    assert pdf_parser._normalize_backend("vlm-auto-engine") == "vlm-engine"
    assert pdf_parser._normalize_backend("hybrid-auto-engine") == "hybrid-engine"
    with pytest.raises(ValueError):
        pdf_parser._normalize_backend("bogus-engine")


def test_tier_for_backend():
    assert pdf_parser.tier_for_backend("pipeline") == "basic"
    for b in ("vlm-engine", "hybrid-engine", "vlm-http-client", "hybrid-http-client"):
        assert pdf_parser.tier_for_backend(b) == "standard"


def test_every_accepted_engine_value_is_dispatchable():
    from typing import get_args

    from markio.settings.config_model import (
        PIPELINE_PDF_ENGINE,
        VLM_PDF_ENGINES,
        ApplicationConfig,
        normalize_pdf_engine,
    )

    accepted = get_args(ApplicationConfig.model_fields["pdf_parse_engine"].annotation)
    assert accepted

    for value in accepted:
        normalized = normalize_pdf_engine(value)
        assert normalized == PIPELINE_PDF_ENGINE or normalized in VLM_PDF_ENGINES


def test_mineru4_public_api_is_available():
    """Guard the MinerU 4 surface markio depends on."""
    from docvortex.document.pdf import PDFDocument  # noqa: F401
    from docvortex.export import materialize_middle  # noqa: F401
    from mineru.config import VlmConfig  # noqa: F401
    from mineru.parser import MinerUParser, ParseResult  # noqa: F401
    from mineru.parser.tier import ensure_tier_runtime_dependencies  # noqa: F401


def test_image_to_pdf_produces_pdf(tmp_path):
    from PIL import Image

    from markio.parsers.image_parser import image_to_pdf

    img = tmp_path / "x.PNG"
    Image.new("RGB", (40, 30), "white").save(img)
    assert image_to_pdf(img).startswith(b"%PDF")
