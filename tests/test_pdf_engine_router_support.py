from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.routers import file_router, pdf_router
from markio.settings import settings


@pytest.mark.asyncio
async def test_file_router_accepts_hybrid_engine(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "demo.pdf"
    pdf_path.write_bytes(b"demo")

    async def fake_pdf_parse_main(**kwargs):
        return "# parsed"

    monkeypatch.setattr(file_router.pdf_parser, "pdf_parse_main", fake_pdf_parse_main)
    monkeypatch.setattr(settings, "pdf_parse_engine", "hybrid-auto-engine")

    app = FastAPI()
    app.include_router(file_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_file",
            files={"file": ("demo.pdf", pdf_path.read_bytes(), "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# parsed"


@pytest.mark.asyncio
async def test_pdf_router_accepts_hybrid_engine(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "demo.pdf"
    pdf_path.write_bytes(b"demo")

    async def fake_pdf_parse_main(**kwargs):
        return "# parsed"

    monkeypatch.setattr(pdf_router, "pdf_parse_main", fake_pdf_parse_main)
    monkeypatch.setattr(settings, "pdf_parse_engine", "hybrid-auto-engine")

    app = FastAPI()
    app.include_router(pdf_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_pdf_file",
            files={"file": ("demo.pdf", pdf_path.read_bytes(), "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# parsed"


@pytest.mark.asyncio
async def test_pdf_router_rejects_invalid_page_range(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "demo.pdf"
    pdf_path.write_bytes(b"demo")

    async def fake_pdf_parse_main(**kwargs):
        pytest.fail("Invalid page ranges should be rejected before parsing")

    monkeypatch.setattr(pdf_router, "pdf_parse_main", fake_pdf_parse_main)

    app = FastAPI()
    app.include_router(pdf_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_pdf_file",
            params={"start_page": "5", "end_page": "3"},
            files={"file": ("demo.pdf", pdf_path.read_bytes(), "application/pdf")},
        )

    assert response.status_code == 400
    assert "end_page" in response.text
