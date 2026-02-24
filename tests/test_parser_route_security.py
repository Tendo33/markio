import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.routers import (
    doc_router,
    docx_router,
    epub_router,
    fasta_router,
    file_router,
    genbank_router,
    html_router,
    image_router,
    pdf_router,
    ppt_router,
    pptx_router,
    url_router,
    xlsx_router,
)
from markio.services import sync_parse_service


UPLOAD_ROUTE_CASES = [
    (file_router, "/v1/parse_file", ("demo.pdf", b"demo", "application/pdf")),
    (pdf_router, "/v1/parse_pdf_file", ("demo.pdf", b"demo", "application/pdf")),
    (doc_router, "/v1/parse_doc_file", ("demo.doc", b"demo", "application/msword")),
    (
        docx_router,
        "/v1/parse_docx_file",
        (
            "demo.docx",
            b"demo",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ),
    (
        ppt_router,
        "/v1/parse_ppt_file",
        ("demo.ppt", b"demo", "application/vnd.ms-powerpoint"),
    ),
    (
        pptx_router,
        "/v1/parse_pptx_file",
        (
            "demo.pptx",
            b"demo",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
    ),
    (
        xlsx_router,
        "/v1/parse_xlsx_file",
        (
            "demo.xlsx",
            b"demo",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ),
    (html_router, "/v1/parse_html_file", ("demo.html", b"demo", "text/html")),
    (epub_router, "/v1/parse_epub_file", ("demo.epub", b"demo", "application/epub+zip")),
    (image_router, "/v1/parse_image_file", ("demo.png", b"demo", "image/png")),
    (fasta_router, "/v1/parse_fasta_file", ("demo.fasta", b"demo", "text/plain")),
    (genbank_router, "/v1/parse_genbank_file", ("demo.gb", b"demo", "text/plain")),
]


def _build_app(module) -> FastAPI:
    app = FastAPI()
    app.include_router(module.router, prefix="/v1")
    return app


@pytest.mark.asyncio
@pytest.mark.parametrize("module,endpoint,file_tuple", UPLOAD_ROUTE_CASES)
async def test_parse_upload_routes_reject_outside_output_dir_even_when_not_saving(
    monkeypatch,
    module,
    endpoint: str,
    file_tuple: tuple[str, bytes, str],
):
    async def fake_runner(*args, **kwargs) -> str:
        return "# parsed"

    monkeypatch.setattr(module, "run_uploaded_file_parser", fake_runner)

    app = _build_app(module)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            endpoint,
            files={"file": file_tuple},
            params={
                "save_parsed_content": "false",
                "output_dir": "/tmp/markio-outside-route-guard",
            },
        )

    assert response.status_code == 400
    assert "Invalid output_dir" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("module,endpoint,file_tuple", UPLOAD_ROUTE_CASES)
async def test_parse_upload_routes_accept_valid_output_subdir(
    monkeypatch,
    module,
    endpoint: str,
    file_tuple: tuple[str, bytes, str],
):
    async def fake_runner(*args, **kwargs) -> str:
        return "# parsed"

    monkeypatch.setattr(module, "run_uploaded_file_parser", fake_runner)

    app = _build_app(module)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            endpoint,
            files={"file": file_tuple},
            params={
                "save_parsed_content": "true",
                "output_dir": "outputs/nested/ok",
            },
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# parsed"


@pytest.mark.asyncio
async def test_parse_url_rejects_outside_output_dir_even_when_not_saving():
    app = _build_app(url_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_url",
            params={
                "url": "https://example.com",
                "save_parsed_content": "false",
                "output_dir": "/tmp/markio-url-outside",
            },
        )

    assert response.status_code == 400
    assert "Invalid output_dir" in response.text


@pytest.mark.asyncio
async def test_parse_url_accepts_valid_output_subdir(monkeypatch):
    async def fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        assert save_parsed_content is True
        assert output_dir.endswith("outputs/nested/ok")
        return "# parsed"

    monkeypatch.setattr(url_router, "url_parse_main", fake_url_parse_main)

    app = _build_app(url_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_url",
            params={
                "url": "https://example.com",
                "save_parsed_content": "true",
                "output_dir": "outputs/nested/ok",
            },
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# parsed"


@pytest.mark.asyncio
@pytest.mark.parametrize("module,endpoint,file_tuple", UPLOAD_ROUTE_CASES)
async def test_parse_upload_routes_reject_oversized_payload_with_413(
    monkeypatch,
    module,
    endpoint: str,
    file_tuple: tuple[str, bytes, str],
):
    filename, _, content_type = file_tuple
    oversized_payload = b"0123456789"

    monkeypatch.setattr(
        sync_parse_service.settings,
        "task_max_upload_size_bytes",
        4,
        raising=False,
    )

    app = _build_app(module)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            endpoint,
            files={"file": (filename, oversized_payload, content_type)},
            params={"save_parsed_content": "true", "output_dir": "outputs/oversized"},
        )

    assert response.status_code == 413
    assert "Maximum allowed size" in response.text


@pytest.mark.asyncio
async def test_parse_file_and_parse_html_file_share_extension_verdict(monkeypatch):
    async def fake_runner(*args, **kwargs) -> str:
        return "# parsed"

    monkeypatch.setattr(file_router, "run_uploaded_file_parser", fake_runner)
    monkeypatch.setattr(html_router, "run_uploaded_file_parser", fake_runner)

    app = FastAPI()
    app.include_router(file_router.router, prefix="/v1")
    app.include_router(html_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        accepted_by_unified = await client.post(
            "/v1/parse_file",
            files={"file": ("demo.htm", b"demo", "text/html")},
        )
        accepted_by_specific = await client.post(
            "/v1/parse_html_file",
            files={"file": ("demo.htm", b"demo", "text/html")},
        )
        rejected_by_unified = await client.post(
            "/v1/parse_file",
            files={"file": ("demo.md", b"demo", "text/markdown")},
        )
        rejected_by_specific = await client.post(
            "/v1/parse_html_file",
            files={"file": ("demo.md", b"demo", "text/markdown")},
        )

    assert accepted_by_unified.status_code == 200
    assert accepted_by_specific.status_code == 200
    assert rejected_by_unified.status_code == 400
    assert rejected_by_specific.status_code == 400
