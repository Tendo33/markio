from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from markio.main import app
from markio.middlewares.error_handlers import add_error_handlers
from markio.routers import html_router, url_router


client = TestClient(app)


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "timestamp" in payload


def test_readyz_endpoint():
    response = client.get("/readyz")
    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert "checks" in payload


@pytest.mark.asyncio
async def test_parse_url_validation_error_uses_error_envelope():
    test_app = FastAPI()
    add_error_handlers(test_app)
    test_app.include_router(url_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.post(
            "/v1/parse_url",
            params={"url": "example.com"},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "http_400"
    assert payload["error"]["message"]
    assert payload["request_id"]


@pytest.mark.asyncio
async def test_html_router_accepts_htm_extension(monkeypatch, tmp_path: Path):
    html_path = tmp_path / "demo.htm"
    html_path.write_text("<html><body>demo</body></html>", encoding="utf-8")

    async def fake_html_parse_main(resource_path: str, **kwargs):
        return "# demo"

    monkeypatch.setattr(html_router, "html_parse_main", fake_html_parse_main)

    test_app = FastAPI()
    add_error_handlers(test_app)
    test_app.include_router(html_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.post(
            "/v1/parse_html_file",
            files={"file": ("demo.htm", html_path.read_bytes(), "text/html")},
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# demo"
