from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from markio.main import app
from markio.middlewares import error_handlers
from markio.middlewares.error_handlers import add_error_handlers
from markio.middlewares.rate_limit_middleware import add_rate_limit_middleware
from markio.middlewares.trace_middleware import add_trace_middleware
from markio.parsers.url_parser import URLFetchError, URLSecurityError
from markio.routers import html_router, url_router
from markio.utils import logger_config


client = TestClient(app)


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "timestamp" in payload
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"]
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "unsafe-eval" not in csp
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp


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
async def test_parse_url_internal_error_uses_generic_message(monkeypatch):
    async def fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        raise RuntimeError("boom with implementation detail")

    monkeypatch.setattr(url_router, "url_parse_main", fake_url_parse_main)

    test_app = FastAPI()
    add_error_handlers(test_app)
    test_app.include_router(url_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["message"] == "Internal server error"
    assert "implementation detail" not in payload["detail"]


@pytest.mark.asyncio
async def test_unexpected_error_is_logged_with_generic_response(monkeypatch):
    captured_messages: list[str] = []

    class _LoggerStub:
        def exception(self, message: str):
            captured_messages.append(message)

    monkeypatch.setattr(error_handlers, "logger", _LoggerStub(), raising=False)

    test_app = FastAPI()
    add_error_handlers(test_app)

    @test_app.get("/boom")
    async def boom():
        raise RuntimeError("boom detail should not leak")

    async with AsyncClient(
        transport=ASGITransport(app=test_app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.get("/boom")

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["message"] == "Internal server error"
    assert "boom detail should not leak" not in payload["detail"]
    assert captured_messages


@pytest.mark.asyncio
async def test_parse_url_security_errors_return_400(monkeypatch):
    async def fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        raise URLSecurityError("URL host is not in allowed domains")

    monkeypatch.setattr(url_router, "url_parse_main", fake_url_parse_main)

    test_app = FastAPI()
    add_error_handlers(test_app)
    test_app.include_router(url_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["message"] == "URL host is not in allowed domains"


@pytest.mark.asyncio
async def test_parse_url_fetch_errors_return_502(monkeypatch):
    async def fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        raise URLFetchError("URL fetch timeout")

    monkeypatch.setattr(url_router, "url_parse_main", fake_url_parse_main)

    test_app = FastAPI()
    add_error_handlers(test_app)
    test_app.include_router(url_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testserver",
    ) as async_client:
        response = await async_client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )

    assert response.status_code == 502
    payload = response.json()
    assert payload["error"]["message"] == "Failed to fetch URL content"


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


def test_trace_middleware_emits_x_request_id_header():
    test_app = FastAPI()
    add_trace_middleware(test_app)

    @test_app.get("/ping")
    async def ping():
        return JSONResponse({"ok": True})

    client = TestClient(test_app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["request-id"]


def test_trace_middleware_preserves_incoming_request_id():
    test_app = FastAPI()
    add_trace_middleware(test_app)

    @test_app.get("/ping")
    async def ping():
        return JSONResponse({"ok": True})

    client = TestClient(test_app)
    incoming = "external-request-id-123"
    response = client.get("/ping", headers={"X-Request-ID": incoming})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == incoming
    assert response.headers["request-id"] == incoming


def test_rate_limit_middleware_returns_429_when_exceeded():
    test_app = FastAPI()
    add_trace_middleware(test_app)
    add_rate_limit_middleware(
        test_app,
        enabled=True,
        max_requests=2,
        window_seconds=60,
    )
    add_error_handlers(test_app)

    @test_app.get("/limited")
    async def limited():
        return {"ok": True}

    client = TestClient(test_app)
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200

    limited_response = client.get("/limited")
    assert limited_response.status_code == 429
    payload = limited_response.json()
    assert payload["error"]["code"] == "http_429"
    assert payload["request_id"]
    assert limited_response.headers["X-Request-ID"] == payload["request_id"]


def test_setup_logger_disables_diagnose_and_backtrace_outside_debug(monkeypatch, tmp_path):
    captured = []

    def fake_add(*args, **kwargs):
        captured.append(kwargs)
        return len(captured)

    monkeypatch.setattr(logger_config.logger, "remove", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(logger_config.logger, "add", fake_add)

    logger_config.setup_logger(
        project_name="markio-test",
        log_dir=str(tmp_path),
        log_level="INFO",
    )

    assert len(captured) == 3
    assert all(item["backtrace"] is False for item in captured)
    assert all(item["diagnose"] is False for item in captured)


def test_setup_logger_keeps_diagnose_and_backtrace_in_debug(monkeypatch, tmp_path):
    captured = []

    def fake_add(*args, **kwargs):
        captured.append(kwargs)
        return len(captured)

    monkeypatch.setattr(logger_config.logger, "remove", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(logger_config.logger, "add", fake_add)

    logger_config.setup_logger(
        project_name="markio-test",
        log_dir=str(tmp_path),
        log_level="DEBUG",
    )

    assert len(captured) == 3
    assert all(item["backtrace"] is True for item in captured)
    assert all(item["diagnose"] is True for item in captured)
