import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from markio.routers.task_router import router as task_router
from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services.redis_task_manager import RedisTaskManager
from markio.services.redis_task_store import RedisTaskStore
from markio.services import runtime
from markio.services.task_manager import AsyncTaskManager
from markio.settings import settings
from tests.test_redis_task_manager import FakeRedis


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _build_jwt(
    *,
    secret: str,
    sub: str = "user-a",
    role: str = "user",
    exp_offset_seconds: int | None = 300,
) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, object] = {"sub": sub, "role": role}
    if exp_offset_seconds is not None:
        payload["exp"] = int(time.time()) + exp_offset_seconds

    header_segment = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64url(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_v1_auth_rejects_missing_invalid_and_expired_token(monkeypatch):
    secret = "test-secret-auth"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        missing = await client.get("/v1/tasks/queue")
        assert missing.status_code == 401

        bad_token = _build_jwt(secret="wrong-secret", sub="user-a")
        invalid = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers(bad_token),
        )
        assert invalid.status_code == 401

        malformed_structure = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers("not-a-jwt"),
        )
        assert malformed_structure.status_code == 401

        malformed_base64 = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers("bad.@@@@.sig"),
        )
        assert malformed_base64.status_code == 401

        malformed_json_payload = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers(
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "bm90LWpzb24."
                "2VjDOkHcLhfwfCW0v7m_AelxY8Q9p3fA6zg0CDdAiuQ"
            ),
        )
        assert malformed_json_payload.status_code == 401

        expired_token = _build_jwt(secret=secret, sub="user-a", exp_offset_seconds=-10)
        expired = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers(expired_token),
        )
        assert expired.status_code == 401

        no_exp_token = _build_jwt(
            secret=secret,
            sub="user-a",
            exp_offset_seconds=None,
        )
        no_exp = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers(no_exp_token),
        )
        assert no_exp.status_code == 401


@pytest.mark.asyncio
async def test_non_admin_cannot_pause_or_resume_queue(monkeypatch):
    secret = "test-secret-admin"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)

    user_token = _build_jwt(secret=secret, sub="user-a", role="user")

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        queue = await client.get(
            "/v1/tasks/queue",
            headers=_auth_headers(user_token),
        )
        assert queue.status_code == 403

        pause = await client.post(
            "/v1/tasks/queue/pause",
            headers=_auth_headers(user_token),
        )
        assert pause.status_code == 403

        resume = await client.post(
            "/v1/tasks/queue/resume",
            headers=_auth_headers(user_token),
        )
        assert resume.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_queue_is_owner_scoped_while_global_queue_is_admin_only(
    monkeypatch,
    tmp_path: Path,
):
    secret = "test-secret-dashboard-scope"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=2, parser_func=fake_parser)
    await manager.start()
    await manager.pause_queue()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    admin_headers = _auth_headers(_build_jwt(secret=secret, sub="admin-1", role="admin"))
    user_a_headers = _auth_headers(_build_jwt(secret=secret, sub="user-a", role="user"))
    user_b_headers = _auth_headers(_build_jwt(secret=secret, sub="user-b", role="user"))

    file_a = tmp_path / "owner-a.pdf"
    file_a.write_bytes(b"a")
    file_b = tmp_path / "owner-b.pdf"
    file_b.write_bytes(b"b")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        created_a = await client.post(
            "/v1/tasks/submit",
            files={"file": ("owner-a.pdf", file_a.read_bytes(), "application/pdf")},
            headers=user_a_headers,
        )
        created_b = await client.post(
            "/v1/tasks/submit",
            files={"file": ("owner-b.pdf", file_b.read_bytes(), "application/pdf")},
            headers=user_b_headers,
        )
        assert created_a.status_code == 200
        assert created_b.status_code == 200

        dashboard_a = await client.get(
            "/v1/tasks/dashboard?recent_limit=10",
            headers=user_a_headers,
        )
        dashboard_b = await client.get(
            "/v1/tasks/dashboard?recent_limit=10",
            headers=user_b_headers,
        )
        global_queue = await client.get("/v1/tasks/queue", headers=admin_headers)

        assert dashboard_a.status_code == 200
        assert dashboard_b.status_code == 200
        assert global_queue.status_code == 200

        payload_a = dashboard_a.json()
        payload_b = dashboard_b.json()
        assert payload_a["stats"]["pending"] == 1
        assert payload_b["stats"]["pending"] == 1
        assert payload_a["queue"]["queued"] == 1
        assert payload_b["queue"]["queued"] == 1
        assert payload_a["queue"]["processing"] == 0
        assert payload_b["queue"]["processing"] == 0
        assert global_queue.json()["queued"] == 2

    await manager.stop()


@pytest.mark.asyncio
async def test_admin_queue_pause_persists_in_dashboard_after_redis_manager_restart(monkeypatch):
    secret = "test-secret-redis-dashboard-pause"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)

    redis = FakeRedis()
    store = RedisTaskStore(redis, use_lua=False)

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = RedisTaskManager(worker_count=1, parser_func=fake_parser, store=store)
    await manager.start()
    await manager.pause_queue()
    await manager.stop()

    restarted = RedisTaskManager(worker_count=1, parser_func=fake_parser, store=store)
    await restarted.start()
    monkeypatch.setattr(runtime, "_task_manager", restarted)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")
    user_headers = _auth_headers(_build_jwt(secret=secret, sub="user-a", role="user"))
    admin_headers = _auth_headers(_build_jwt(secret=secret, sub="admin-1", role="admin"))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        dashboard = await client.get("/v1/tasks/dashboard?recent_limit=10", headers=user_headers)
        queue = await client.get("/v1/tasks/queue", headers=admin_headers)

    assert dashboard.status_code == 200
    assert queue.status_code == 200
    assert dashboard.json()["queue"]["paused"] is True
    assert queue.json()["paused"] is True

    await restarted.resume_queue()
    await restarted.stop()


@pytest.mark.asyncio
async def test_task_routes_are_owner_isolated_for_idor(monkeypatch, tmp_path: Path):
    secret = "test-secret-idor"
    monkeypatch.setattr(settings, "auth_jwt_secret", secret, raising=False)
    monkeypatch.setattr(settings, "auth_jwt_algorithm", "HS256", raising=False)

    async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
        return "# done"

    manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
    await manager.start()
    monkeypatch.setattr(runtime, "_task_manager", manager)

    app = FastAPI()
    app.include_router(task_router, prefix="/v1")

    admin_headers = _auth_headers(_build_jwt(secret=secret, sub="admin-1", role="admin"))
    user_a_headers = _auth_headers(_build_jwt(secret=secret, sub="user-a", role="user"))
    user_b_headers = _auth_headers(_build_jwt(secret=secret, sub="user-b", role="user"))

    file_a = tmp_path / "a.pdf"
    file_a.write_bytes(b"a")
    file_b = tmp_path / "b.pdf"
    file_b.write_bytes(b"b")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        paused = await client.post("/v1/tasks/queue/pause", headers=admin_headers)
        assert paused.status_code == 200

        created_a = await client.post(
            "/v1/tasks/submit",
            files={"file": ("a.pdf", file_a.read_bytes(), "application/pdf")},
            headers=user_a_headers,
        )
        created_b = await client.post(
            "/v1/tasks/submit",
            files={"file": ("b.pdf", file_b.read_bytes(), "application/pdf")},
            headers=user_b_headers,
        )
        assert created_a.status_code == 200
        assert created_b.status_code == 200

        task_a = created_a.json()["task_id"]
        task_b = created_b.json()["task_id"]

        listed_a = await client.get("/v1/tasks?page=1&page_size=20", headers=user_a_headers)
        listed_b = await client.get("/v1/tasks?page=1&page_size=20", headers=user_b_headers)
        assert listed_a.status_code == 200
        assert listed_b.status_code == 200
        assert {item["task_id"] for item in listed_a.json()["items"]} == {task_a}
        assert {item["task_id"] for item in listed_b.json()["items"]} == {task_b}

        get_cross = await client.get(f"/v1/tasks/{task_a}", headers=user_b_headers)
        assert get_cross.status_code == 404

        cancel_cross = await client.post(f"/v1/tasks/{task_a}/cancel", headers=user_b_headers)
        assert cancel_cross.status_code == 404

        cancel_own = await client.post(f"/v1/tasks/{task_a}/cancel", headers=user_a_headers)
        assert cancel_own.status_code == 200

        retry_cross = await client.post(f"/v1/tasks/{task_a}/retry", headers=user_b_headers)
        assert retry_cross.status_code == 404

        retry_own = await client.post(f"/v1/tasks/{task_a}/retry", headers=user_a_headers)
        assert retry_own.status_code == 200
        assert retry_own.json()["retried"] is True

    await manager.stop()
