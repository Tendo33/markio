import pytest

from markio.sdk.markio_sdk import MarkioSDK


class _FakeResponse:
    def __init__(self):
        self._payload = {"parsed_content": "# parsed"}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_sdk_remote_mode_attaches_bearer_token(monkeypatch):
    captured_headers = {}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, _exc_type, _exc, _tb):
            return False

        async def post(self, url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return _FakeResponse()

    monkeypatch.setattr("markio.sdk.markio_sdk.httpx.AsyncClient", _FakeClient)

    sdk = MarkioSDK(
        output_dir="outputs",
        api_base_url="http://localhost:8000",
        token="token-123",
    )
    result = await sdk.parse_url("https://example.com", save_parsed_content=False)

    assert result["content"] == "# parsed"
    assert captured_headers["Authorization"] == "Bearer token-123"


@pytest.mark.asyncio
async def test_sdk_local_parse_url_uses_shared_url_parser(monkeypatch, tmp_path):
    captured = {}

    async def _fake_url_parse_main(url: str, save_parsed_content: bool, output_dir: str) -> str:
        captured["url"] = url
        captured["save_parsed_content"] = save_parsed_content
        captured["output_dir"] = output_dir
        return "# parsed locally"

    monkeypatch.setattr("markio.sdk.markio_sdk.url_parse_main", _fake_url_parse_main)

    sdk = MarkioSDK(output_dir=str(tmp_path))
    result = await sdk.parse_url("https://example.com/demo", save_parsed_content=True)

    assert result["content"] == "# parsed locally"
    assert captured == {
        "url": "https://example.com/demo",
        "save_parsed_content": True,
        "output_dir": str(tmp_path),
    }


@pytest.mark.asyncio
async def test_sdk_parse_pdf_passes_lang_and_uses_outputs_default(monkeypatch):
    captured = {}

    async def _fake_pdf_parse_main(**kwargs):
        captured.update(kwargs)
        return "# parsed pdf"

    monkeypatch.setattr("markio.sdk.markio_sdk.pdf_parse_main", _fake_pdf_parse_main)

    sdk = MarkioSDK()
    result = await sdk.parse_pdf("sample.pdf", parse_method="ocr", lang="en")

    assert result["content"] == "# parsed pdf"
    assert captured["parse_method"] == "ocr"
    assert captured["lang"] == "en"
    assert captured["output_dir"].endswith("outputs")
