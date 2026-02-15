import pytest

from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services import document_service
from markio.settings import settings


@pytest.mark.asyncio
async def test_pdf_routing_passes_configured_backend(monkeypatch):
    captured = {}

    async def fake_pdf_parser(**kwargs):
        captured.update(kwargs)
        return "# parsed"

    monkeypatch.setattr(document_service.pdf_parser, "pdf_parse_main", fake_pdf_parser)
    monkeypatch.setattr(settings, "pdf_parse_engine", "hybrid-auto-engine")
    monkeypatch.setattr(settings, "vlm_server_url", "http://localhost:30000")

    result = await document_service.parse_local_file(
        "/tmp/demo.pdf",
        SubmitTaskRequest(filename="demo.pdf", file_path="/tmp/demo.pdf"),
    )

    assert result == "# parsed"
    assert captured["resource_path"] == "/tmp/demo.pdf"
    assert captured["backend"] == "hybrid-auto-engine"
    assert captured["server_url"] == "http://localhost:30000"
