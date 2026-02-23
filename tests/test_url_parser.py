from pathlib import Path

import aiohttp
import pytest

from markio.parsers import url_parser


class _FakeResponse:
    def __init__(self, text: str, error: Exception | None = None):
        self._text = text
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    async def text(self):
        return self._text


class _FakeSession:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_url_parse_main_saves_to_expected_markdown_path(monkeypatch, tmp_path: Path):
    response = _FakeResponse("Title: Demo\n\nHello Markio")
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(response))

    content = await url_parser.url_parse_main(
        url="https://example.com",
        save_parsed_content=True,
        output_dir=str(tmp_path),
    )

    assert "Hello Markio" in content
    markdown_file = tmp_path / "Demo" / "Demo.md"
    assert markdown_file.exists()
    assert "Hello Markio" in markdown_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_url_parse_main_raises_runtime_error_on_http_failure(monkeypatch):
    response = _FakeResponse(
        "",
        error=aiohttp.ClientError("bad gateway"),
    )
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(response))

    with pytest.raises(RuntimeError, match="Failed to fetch URL content"):
        await url_parser.url_parse_main(
            url="https://example.com",
            save_parsed_content=False,
            output_dir="outputs",
        )
