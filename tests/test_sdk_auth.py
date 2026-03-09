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
