from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import markio.services.parser_registry as parser_registry
from markio.routers import file_router
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services import document_service


@pytest.mark.asyncio
async def test_parse_file_and_task_dispatch_share_registry(monkeypatch, tmp_path: Path):
    calls: list[str] = []

    async def fake_parser(
        resource_path: str,
        save_parsed_content: bool,
        output_dir: str,
    ) -> str:
        calls.append(resource_path)
        return "# parsed from registry"

    monkeypatch.setitem(parser_registry.EXTENSION_PARSERS, ".htm", fake_parser)

    file_path = tmp_path / "page.htm"
    file_path.write_text("<html><body>demo</body></html>", encoding="utf-8")

    app = FastAPI()
    app.include_router(file_router.router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_file",
            files={"file": ("page.htm", file_path.read_bytes(), "text/html")},
        )

    assert response.status_code == 200
    assert response.json()["parsed_content"] == "# parsed from registry"

    task_result = await document_service.parse_local_file(
        file_path=str(file_path),
        request=SubmitTaskRequest(filename="page.htm", file_path=str(file_path)),
    )
    assert task_result == "# parsed from registry"
    assert len(calls) == 2


def test_registry_lists_shared_supported_extensions():
    supported = parser_registry.get_supported_extensions()
    assert ".html" in supported
    assert ".htm" in supported
    assert ".pdf" in supported
