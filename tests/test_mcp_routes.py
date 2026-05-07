import base64
import hashlib
import hmac
import json
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.mcps import mcp_server
from markio.parsers.url_parser import URLFetchError
from markio.schemas.parsers_schemas import DOCXParserConfig
from markio.settings import settings


class _FakeFastApiMCP:
    def __init__(self, app: FastAPI):
        self.app = app

    def mount(self) -> None:
        return None

    def setup_server(self) -> None:
        return None


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _build_jwt(secret: str, sub: str = "user-a", role: str = "user") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": sub,
        "role": role,
        "exp": int(time.time()) + 300,
    }
    header_segment = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64url(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


@pytest.fixture
def mcp_app(monkeypatch) -> tuple[FastAPI, mcp_server.MarkioMCP]:
    monkeypatch.setattr(mcp_server, "FastApiMCP", _FakeFastApiMCP)
    app = FastAPI()
    instance = mcp_server.MarkioMCP(app)
    return app, instance


@pytest.mark.asyncio
async def test_mcp_routes_require_jwt(monkeypatch, mcp_app):
    secret = "mcp-auth-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    app, _ = mcp_app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        new_route = await client.post(
            "/v1/mcp/parse_url",
            json={"url": "https://example.com"},
        )
        legacy_route = await client.post(
            "/mcp/parse_url",
            json={"url": "https://example.com"},
        )

    assert new_route.status_code == 401
    assert legacy_route.status_code == 401


@pytest.mark.asyncio
async def test_legacy_mcp_route_returns_deprecation_headers(monkeypatch, mcp_app):
    secret = "mcp-legacy-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, _ = mcp_app

    async def fake_url_parse_main(
        url: str,
        save_parsed_content: bool,
        output_dir: str,
    ) -> str:
        return f"# {url}"

    monkeypatch.setattr("markio.parsers.url_parser.url_parse_main", fake_url_parse_main)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/mcp/parse_url",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.headers["Deprecation"] == "true"
    assert response.headers["X-Markio-Deprecated"] == "Use /v1/mcp/* endpoints"


@pytest.mark.asyncio
async def test_mcp_convert_document_non_pdf_passes_parser_signature(monkeypatch, mcp_app):
    secret = "mcp-signature-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, instance = mcp_app

    captured: dict[str, object] = {}

    async def fake_docx_parser(
        *,
        resource_path: str,
        save_parsed_content: bool,
        output_dir: str,
    ) -> str:
        captured["resource_path"] = resource_path
        captured["save_parsed_content"] = save_parsed_content
        captured["output_dir"] = output_dir
        return "# parsed-docx"

    instance.FILE_PARSERS = {
        ".docx": (fake_docx_parser, DOCXParserConfig),
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/mcp/convert_document",
            files={
                "file": (
                    "demo.docx",
                    b"fake",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["result"] == "# parsed-docx"
    assert captured["save_parsed_content"] is False
    assert isinstance(captured["resource_path"], str)


@pytest.mark.asyncio
async def test_mcp_convert_document_rejects_oversized_upload(monkeypatch, mcp_app):
    secret = "mcp-size-limit-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    monkeypatch.setattr(settings, "task_max_upload_size_bytes", 4, raising=False)
    token = _build_jwt(secret)
    app, _ = mcp_app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/mcp/convert_document",
            files={
                "file": (
                    "demo.docx",
                    b"abcdef",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 413
    assert "Maximum allowed size" in response.text


@pytest.mark.asyncio
async def test_mcp_convert_document_validation_error_uses_standard_error_envelope(monkeypatch, mcp_app):
    secret = "mcp-validation-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, _ = mcp_app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/mcp/convert_document",
            files={"file": ("demo.txt", b"hello", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "http_400"
    assert "Unsupported file type" in payload["error"]["message"]


@pytest.mark.asyncio
async def test_mcp_convert_document_cleans_temp_file_on_parser_failure(monkeypatch, mcp_app, tmp_path: Path):
    secret = "mcp-temp-cleanup-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, instance = mcp_app

    created_temp_paths: list[Path] = []
    original_named_temp_file = tempfile.NamedTemporaryFile

    def tracking_named_tempfile(*args, **kwargs):
        handle = original_named_temp_file(*args, **kwargs)
        created_temp_paths.append(Path(handle.name))
        return handle

    async def failing_docx_parser(*, resource_path: str, save_parsed_content: bool, output_dir: str) -> str:
        raise RuntimeError("boom")

    instance.FILE_PARSERS = {
        ".docx": (failing_docx_parser, DOCXParserConfig),
    }
    monkeypatch.setattr(tempfile, "NamedTemporaryFile", tracking_named_tempfile)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/mcp/convert_document",
            files={
                "file": (
                    "demo.docx",
                    b"fake",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "http_500"
    assert payload["error"]["message"] == "Parsing failed"
    assert created_temp_paths
    assert all(not path.exists() for path in created_temp_paths)


@pytest.mark.asyncio
async def test_legacy_mcp_error_keeps_deprecation_headers(monkeypatch, mcp_app):
    secret = "mcp-legacy-error-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, _ = mcp_app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/mcp/parse_url",
            json={"url": "notaurl"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert response.headers["Deprecation"] == "true"
    assert response.headers["X-Markio-Deprecated"] == "Use /v1/mcp/* endpoints"
    assert response.json()["error"]["code"] == "http_400"


@pytest.mark.asyncio
async def test_v1_mcp_parse_url_maps_fetch_failures_to_502(monkeypatch, mcp_app):
    secret = "mcp-fetch-error-secret"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)
    token = _build_jwt(secret)
    app, _ = mcp_app

    async def failing_url_parse_main(
        url: str,
        save_parsed_content: bool,
        output_dir: str,
    ) -> str:
        raise URLFetchError("URL fetch timeout")

    monkeypatch.setattr("markio.parsers.url_parser.url_parse_main", failing_url_parse_main)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/mcp/parse_url",
            json={"url": "https://example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 502
    payload = response.json()
    assert payload["error"]["code"] == "http_502"
    assert payload["error"]["message"] == "Failed to fetch URL content"
