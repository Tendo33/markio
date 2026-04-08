import ipaddress
import socket
from pathlib import Path

import aiohttp
import pytest

from markio.parsers import url_parser
from markio.settings import settings


async def _allow_all_targets(*args, **kwargs):
    return None


class _FakeContent:
    def __init__(self, payload: bytes):
        self.payload = payload

    async def iter_chunked(self, chunk_size: int):
        for start in range(0, len(self.payload), chunk_size):
            yield self.payload[start : start + chunk_size]


class _FakeResponse:
    def __init__(
        self,
        *,
        text: str = "",
        status: int = 200,
        headers: dict[str, str] | None = None,
        url: str = "https://example.com",
        error: Exception | None = None,
    ):
        self.status = status
        self.headers = headers or {}
        self.url = url
        self._error = error
        self._payload = text.encode("utf-8")
        self.content = _FakeContent(self._payload)
        self.charset = "utf-8"

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        return False

    def raise_for_status(self):
        if self._error is not None:
            raise self._error


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse], seen_urls: list[str], **kwargs):
        self._responses = responses
        self._seen_urls = seen_urls
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        return False

    def get(self, url: str, *args, **kwargs):
        self._seen_urls.append(url)
        if not self._responses:
            raise AssertionError("No fake response queued")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_url_parse_main_saves_to_expected_markdown_path(monkeypatch, tmp_path: Path):
    seen_urls: list[str] = []
    response = _FakeResponse(text="Title: Demo\n\nHello Markio")
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([response], seen_urls),
    )
    monkeypatch.setattr(
        url_parser,
        "_validate_target_host",
        _allow_all_targets,
    )
    monkeypatch.setattr(settings, "url_fetch_mode", "direct", raising=False)
    monkeypatch.setattr(settings, "url_max_response_bytes", 1024 * 1024, raising=False)
    monkeypatch.setattr(settings, "url_request_timeout_seconds", 10, raising=False)
    monkeypatch.setattr(settings, "url_max_redirects", 1, raising=False)

    content = await url_parser.url_parse_main(
        url="https://example.com",
        save_parsed_content=True,
        output_dir=str(tmp_path),
    )

    assert "Hello Markio" in content
    assert seen_urls == ["https://example.com"]
    markdown_file = tmp_path / "demo" / "demo.md"
    assert markdown_file.exists()
    assert "Hello Markio" in markdown_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_url_parse_main_sanitizes_malicious_title(monkeypatch, tmp_path: Path):
    seen_urls: list[str] = []
    response = _FakeResponse(text="Title: ../../..\\\\evil/title\n\nHello")
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([response], seen_urls),
    )
    monkeypatch.setattr(
        url_parser,
        "_validate_target_host",
        _allow_all_targets,
    )

    await url_parser.url_parse_main(
        url="https://example.com",
        save_parsed_content=True,
        output_dir=str(tmp_path),
    )

    escaped_target = tmp_path.parent / "evil"
    assert not escaped_target.exists()
    saved_files = list(tmp_path.rglob("*.md"))
    assert len(saved_files) == 1
    assert saved_files[0].resolve().is_relative_to(tmp_path.resolve())


@pytest.mark.asyncio
async def test_url_parse_main_raises_fetch_error_on_http_failure(monkeypatch):
    seen_urls: list[str] = []
    response = _FakeResponse(error=aiohttp.ClientError("bad gateway"))
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([response], seen_urls),
    )
    monkeypatch.setattr(
        url_parser,
        "_validate_target_host",
        _allow_all_targets,
    )

    with pytest.raises(url_parser.URLFetchError, match="Failed to fetch URL content"):
        await url_parser.url_parse_main(
            url="https://example.com",
            save_parsed_content=False,
            output_dir="outputs",
        )


@pytest.mark.asyncio
async def test_url_parse_main_blocks_private_network_targets(monkeypatch):
    async def fake_resolve(hostname: str):
        return {ipaddress.ip_address("127.0.0.1")}

    monkeypatch.setattr(url_parser, "_resolve_hostname_ips", fake_resolve)
    monkeypatch.setattr(settings, "url_block_private_networks", True, raising=False)
    monkeypatch.setattr(settings, "url_allowed_domains", "", raising=False)

    with pytest.raises(
        url_parser.URLSecurityError,
        match="blocked network address",
    ):
        await url_parser.url_parse_main(
            url="http://localhost/test",
            save_parsed_content=False,
            output_dir="outputs",
        )


@pytest.mark.asyncio
async def test_url_parse_main_rejects_oversized_response(monkeypatch):
    seen_urls: list[str] = []
    response = _FakeResponse(text="12345")
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([response], seen_urls),
    )
    monkeypatch.setattr(
        url_parser,
        "_validate_target_host",
        _allow_all_targets,
    )
    monkeypatch.setattr(settings, "url_max_response_bytes", 4, raising=False)

    with pytest.raises(url_parser.URLFetchError, match="size limit"):
        await url_parser.url_parse_main(
            url="https://example.com",
            save_parsed_content=False,
            output_dir="outputs",
        )


@pytest.mark.asyncio
async def test_url_parse_main_supports_proxy_fetch_mode(monkeypatch):
    seen_urls: list[str] = []
    response = _FakeResponse(text="Title: Proxy\n\nok")
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([response], seen_urls),
    )
    monkeypatch.setattr(
        url_parser,
        "_validate_target_host",
        _allow_all_targets,
    )
    monkeypatch.setattr(settings, "url_fetch_mode", "jina_proxy", raising=False)
    monkeypatch.setattr(settings, "url_proxy_base", "https://r.jina.ai", raising=False)

    content = await url_parser.url_parse_main(
        url="https://example.com/doc",
        save_parsed_content=False,
        output_dir="outputs",
    )

    assert "ok" in content
    assert seen_urls == ["https://r.jina.ai/https://example.com/doc"]


@pytest.mark.asyncio
async def test_download_file_from_url_rejects_redirect_to_blocked_target(monkeypatch, tmp_path: Path):
    seen_urls: list[str] = []
    redirect_response = _FakeResponse(
        status=302,
        headers={"Location": "http://127.0.0.1/private"},
        url="https://example.com/start",
    )
    monkeypatch.setattr(
        aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _FakeSession([redirect_response], seen_urls),
    )

    async def _validate_target_host(url: str, **kwargs):
        if "127.0.0.1" in url:
            raise url_parser.URLSecurityError("URL host resolves to blocked network address")
        return {ipaddress.ip_address("93.184.216.34")}

    monkeypatch.setattr(url_parser, "_validate_target_host", _validate_target_host)
    monkeypatch.setattr(settings, "url_max_redirects", 2, raising=False)

    with pytest.raises(url_parser.URLSecurityError, match="blocked network address"):
        await url_parser.download_file_from_url(
            url="https://example.com/start",
            output_dir=str(tmp_path),
        )

    assert seen_urls == ["https://example.com/start"]


@pytest.mark.asyncio
async def test_pinned_resolver_returns_only_pinned_addresses():
    resolver = url_parser._PinnedResolver()
    resolver.pin("example.com", {ipaddress.ip_address("93.184.216.34")})

    resolved = await resolver.resolve("example.com", 443, socket.AF_UNSPEC)

    assert resolved == [
        {
            "hostname": "example.com",
            "host": "93.184.216.34",
            "port": 443,
            "family": socket.AF_INET,
            "proto": socket.IPPROTO_TCP,
            "flags": socket.AI_NUMERICHOST,
        }
    ]


@pytest.mark.asyncio
async def test_download_file_from_url_uses_pinned_resolver(monkeypatch, tmp_path: Path):
    seen_urls: list[str] = []
    captured_connector = {}

    response = _FakeResponse(text="ok", url="https://example.com/download.txt")

    def _fake_client_session(*args, **kwargs):
        captured_connector["connector"] = kwargs.get("connector")
        return _FakeSession([response], seen_urls, **kwargs)

    async def _fake_validate_target_host(url: str, **kwargs):
        return {ipaddress.ip_address("93.184.216.34")}

    monkeypatch.setattr(aiohttp, "ClientSession", _fake_client_session)
    monkeypatch.setattr(url_parser, "_validate_target_host", _fake_validate_target_host)

    output_path = await url_parser.download_file_from_url(
        url="https://example.com/download.txt",
        output_dir=str(tmp_path),
    )

    resolver = captured_connector["connector"]._resolver
    assert isinstance(resolver, url_parser._PinnedResolver)
    assert resolver._pinned_hosts["example.com"] == ("93.184.216.34",)
    assert seen_urls == ["https://example.com/download.txt"]
    assert Path(output_path).exists()
