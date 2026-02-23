import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.routers.task_router import router as task_router
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services import runtime
from markio.services.task_manager import AsyncTaskManager


@pytest.mark.asyncio
async def test_submit_task_endpoint_and_query(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "demo.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        assert request.filename == "demo.pdf"
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()

    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("demo.pdf", file_path.read_bytes(), "application/pdf")},
        )
        assert response.status_code == 200

        payload = response.json()
        task_id = payload["task_id"]
        assert payload["status"] in {"pending", "processing"}

        task_payload = None
        for _ in range(40):
            detail = await client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            task_payload = detail.json()
            if task_payload["status"] == "completed":
                break
            await asyncio.sleep(0.05)

        assert task_payload is not None
        assert task_payload["status"] == "completed"
        assert task_payload["result"] == "# done"

        stats = await client.get("/v1/tasks/stats")
        assert stats.status_code == 200
        assert stats.json()["completed"] == 1

        queue = await client.get("/v1/tasks/queue")
        assert queue.status_code == 200
        assert queue.json()["workers"] == 1

        dashboard = await client.get("/v1/tasks/dashboard?recent_limit=5")
        assert dashboard.status_code == 200
        body = dashboard.json()
        assert "stats" in body
        assert "recent_tasks" in body

    await manager.stop()


@pytest.mark.asyncio
async def test_queue_pause_resume_and_cancel(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "pause.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        pause = await client.post("/v1/tasks/queue/pause")
        assert pause.status_code == 200
        assert pause.json()["paused"] is True

        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("pause.pdf", file_path.read_bytes(), "application/pdf")},
        )
        task_id = response.json()["task_id"]

        await asyncio.sleep(0.1)
        detail = await client.get(f"/v1/tasks/{task_id}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "pending"

        cancel = await client.post(f"/v1/tasks/{task_id}/cancel")
        assert cancel.status_code == 200
        assert cancel.json()["canceled"] is True

        resume = await client.post("/v1/tasks/queue/resume")
        assert resume.status_code == 200
        assert resume.json()["paused"] is False

        detail = await client.get(f"/v1/tasks/{task_id}")
        assert detail.json()["status"] == "canceled"

    await manager.stop()


@pytest.mark.asyncio
async def test_retry_endpoint_and_pagination(monkeypatch, tmp_path: Path):
    async def parser(path: str, request: SubmitTaskRequest) -> str:
        if request.filename.startswith("fail"):
            raise RuntimeError("fail once")
        return "# ok"

    manager = AsyncTaskManager(worker_count=1, parser_func=parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        for name in ["ok1.pdf", "ok2.pdf", "fail1.pdf"]:
            path = tmp_path / name
            path.write_bytes(b"demo")
            await client.post(
                "/v1/tasks/submit",
                files={"file": (name, path.read_bytes(), "application/pdf")},
            )

        await asyncio.sleep(0.3)
        page = await client.get("/v1/tasks?page=1&page_size=1&status=completed")
        assert page.status_code == 200
        body = page.json()
        assert body["total"] == 2
        assert len(body["items"]) == 1

        failed = await client.get("/v1/tasks?page=1&page_size=10&status=failed")
        failed_task_id = failed.json()["items"][0]["task_id"]

        retry = await client.post(f"/v1/tasks/{failed_task_id}/retry")
        assert retry.status_code == 200
        assert retry.json()["retried"] is True

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_rejects_invalid_page_range(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "invalid.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("invalid.pdf", file_path.read_bytes(), "application/pdf")},
            data={"start_page": "5", "end_page": "3"},
        )
        assert response.status_code == 400
        assert "end_page" in response.text

    await manager.stop()
