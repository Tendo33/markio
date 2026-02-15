import asyncio

import pytest

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
