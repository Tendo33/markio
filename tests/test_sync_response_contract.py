from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import markio.services.parser_registry as parser_registry
from markio.routers import file_router, url_router


@pytest.mark.asyncio
async def test_parse_file_response_contract(monkeypatch, tmp_path: Path):
    async def fake_parser(
        resource_path: str,
        save_parsed_content: bool,
        output_dir: str,
    ) -> str:
        return "# parsed"

    monkeypatch.setitem(parser_registry.EXTENSION_PARSERS, ".html", fake_parser)

    file_path = tmp_path / "demo.html"
    file_path.write_text("<html></html>", encoding="utf-8")

    app = FastAPI()
    app.include_router(file_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_file",
            files={"file": ("demo.html", file_path.read_bytes(), "text/html")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "v1"
    assert payload["parsed_content"] == "# parsed"
    assert payload["parser"] == "html"
    assert payload["source_type"] == "file"
    assert isinstance(payload["request_id"], str)
    assert payload["request_id"]
    assert isinstance(payload["duration_ms"], int)
    assert payload["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_parse_url_response_contract(monkeypatch):
    async def fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        return "# from url"

    monkeypatch.setattr(url_router, "url_parse_main", fake_url_parse_main)

    app = FastAPI()
    app.include_router(url_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "v1"
    assert payload["parsed_content"] == "# from url"
    assert payload["parser"] == "url"
    assert payload["source_type"] == "url"
    assert isinstance(payload["request_id"], str)
    assert payload["request_id"]
    assert isinstance(payload["duration_ms"], int)
    assert payload["duration_ms"] >= 0
