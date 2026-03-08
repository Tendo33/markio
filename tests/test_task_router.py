import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio import routers
from markio.auth import AuthUser, require_admin_user, require_auth_user
from markio.routers.task_router import router as task_router
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services import runtime
from markio.services.task_manager import AsyncTaskManager


def _build_app(*, user_id: str = "user-a", role: str = "admin") -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[require_auth_user] = lambda: AuthUser(
        user_id=user_id,
        role=role,
        claims={"sub": user_id, "role": role},
    )
    app.dependency_overrides[require_admin_user] = lambda: AuthUser(
        user_id=user_id,
        role="admin",
        claims={"sub": user_id, "role": "admin"},
    )
    app.include_router(task_router, prefix="/v1")
    return app


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

    app = _build_app()

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

    app = _build_app()

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

    app = _build_app()

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

    app = _build_app()

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


@pytest.mark.asyncio
async def test_submit_task_rejects_unsupported_extension(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "invalid.txt"
    file_path.write_text("demo", encoding="utf-8")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("invalid.txt", file_path.read_bytes(), "text/plain")},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_rejects_invalid_parse_method_for_pdf(
    monkeypatch,
    tmp_path: Path,
):
    file_path = tmp_path / "invalid-method.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={
                "file": (
                    "invalid-method.pdf",
                    file_path.read_bytes(),
                    "application/pdf",
                )
            },
            data={"parse_method": "invalid"},
        )
        assert response.status_code == 400
        assert "parse_method" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_rejects_invalid_lang_for_pdf(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "invalid-lang.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={
                "file": (
                    "invalid-lang.pdf",
                    file_path.read_bytes(),
                    "application/pdf",
                )
            },
            data={"lang": "invalid-lang"},
        )
        assert response.status_code == 400
        assert "lang" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_rejects_output_dir_outside_default_root(
    monkeypatch,
    tmp_path: Path,
):
    file_path = tmp_path / "outside-output.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={
                "file": (
                    "outside-output.pdf",
                    file_path.read_bytes(),
                    "application/pdf",
                )
            },
            data={"output_dir": "/tmp/markio-outside"},
        )
        assert response.status_code == 400
        assert "output_dir" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_rejects_too_large_file(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "large.pdf"
    file_path.write_bytes(b"abcdef")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)
    monkeypatch.setattr(
        routers.task_router.settings,
        "task_max_upload_size_bytes",
        4,
        raising=False,
    )

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("large.pdf", file_path.read_bytes(), "application/pdf")},
        )
        assert response.status_code == 413
        assert "too large" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_task_routes_reject_invalid_task_id(monkeypatch):
    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        for endpoint in (
            "/v1/tasks/invalid-id",
            "/v1/tasks/invalid-id/cancel",
            "/v1/tasks/invalid-id/retry",
        ):
            response = await client.post(endpoint) if endpoint.endswith(
                ("/cancel", "/retry")
            ) else await client.get(endpoint)
            assert response.status_code == 400
            assert "task_id" in response.text

    await manager.stop()


@pytest.mark.asyncio
async def test_cancel_retry_return_semantic_status(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "semantic.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        missing_task_id = "f" * 32
        cancel_missing = await client.post(f"/v1/tasks/{missing_task_id}/cancel")
        assert cancel_missing.status_code == 404

        retry_missing = await client.post(f"/v1/tasks/{missing_task_id}/retry")
        assert retry_missing.status_code == 404

        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("semantic.pdf", file_path.read_bytes(), "application/pdf")},
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        for _ in range(40):
            detail = await client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            if detail.json()["status"] == "completed":
                break
            await asyncio.sleep(0.05)

        cancel_completed = await client.post(f"/v1/tasks/{task_id}/cancel")
        assert cancel_completed.status_code == 409

        retry_completed = await client.post(f"/v1/tasks/{task_id}/retry")
        assert retry_completed.status_code == 409

    await manager.stop()


@pytest.mark.asyncio
async def test_list_and_dashboard_hide_large_result_field(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "result.pdf"
    file_path.write_bytes(b"demo")

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("result.pdf", file_path.read_bytes(), "application/pdf")},
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        for _ in range(40):
            detail = await client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            if detail.json()["status"] == "completed":
                break
            await asyncio.sleep(0.05)

        task_list = await client.get("/v1/tasks?page=1&page_size=10")
        assert task_list.status_code == 200
        list_item = task_list.json()["items"][0]
        assert "result" not in list_item

        dashboard = await client.get("/v1/tasks/dashboard?recent_limit=10")
        assert dashboard.status_code == 200
        recent_item = dashboard.json()["recent_tasks"][0]
        assert "result" not in recent_item

    await manager.stop()


@pytest.mark.asyncio
async def test_task_detail_supports_result_projection_and_truncation(
    monkeypatch,
    tmp_path: Path,
):
    file_path = tmp_path / "detail.pdf"
    file_path.write_bytes(b"demo")
    full_result = "x" * 32

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return full_result

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={"file": ("detail.pdf", file_path.read_bytes(), "application/pdf")},
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        for _ in range(40):
            detail = await client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            if detail.json()["status"] == "completed":
                break
            await asyncio.sleep(0.05)

        hidden_result = await client.get(
            f"/v1/tasks/{task_id}",
            params={"include_result": "false"},
        )
        assert hidden_result.status_code == 200
        hidden_payload = hidden_result.json()
        assert "result" not in hidden_payload
        assert hidden_payload["result_truncated"] is False

        truncated = await client.get(
            f"/v1/tasks/{task_id}",
            params={"max_result_chars": 5},
        )
        assert truncated.status_code == 200
        truncated_payload = truncated.json()
        assert truncated_payload["result"] == full_result[:5]
        assert truncated_payload["result_truncated"] is True

    await manager.stop()


@pytest.mark.asyncio
async def test_submit_task_sanitizes_malicious_filename(monkeypatch, tmp_path: Path):
    captured: dict[str, str] = {}

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        captured["file_path"] = path
        captured["filename"] = request.filename
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = _build_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/tasks/submit",
            files={
                "file": (
                    "..\\../evil/../../demo?.pdf",
                    b"demo",
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        for _ in range(40):
            detail = await client.get(f"/v1/tasks/{task_id}")
            if detail.status_code == 200 and detail.json()["status"] == "completed":
                break
            await asyncio.sleep(0.05)

    await manager.stop()

    assert captured["filename"].endswith(".pdf")
    assert "?" not in captured["filename"]
    assert "/" not in captured["filename"]
    assert "\\" not in captured["filename"]
    assert Path(captured["file_path"]).resolve().is_relative_to(
        Path(routers.task_router.settings.task_upload_dir).resolve()
    )
