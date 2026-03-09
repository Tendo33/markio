import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.mcps import mcp_server
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
