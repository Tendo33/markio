import asyncio
from pathlib import Path

import pytest

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.redis_task_manager import RedisTaskManager
from markio.services.redis_task_store import RedisTaskStore
from markio.services.task_manager import AsyncTaskManager
from tests.test_redis_task_manager import FakeRedis


async def _wait_status(manager, task_id: str, expected: TaskStatus, timeout: float = 3.0):
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        task = await manager.get_task(task_id)
        if task is not None and task.status == expected:
            return task
        await asyncio.sleep(0.02)
    raise AssertionError(f"task {task_id} did not reach {expected}")


def _backend_factory(backend: str, tmp_path: Path, parser):
    if backend == "memory":
        state_file = tmp_path / "task-state.json"

        def build_manager():
            return AsyncTaskManager(
                worker_count=1,
                parser_func=parser,
                state_file_path=str(state_file),
                state_result_max_chars=4096,
            )

        return build_manager

    redis = FakeRedis()
    store = RedisTaskStore(redis, use_lua=False)

    def build_manager():
        return RedisTaskManager(
            worker_count=1,
            parser_func=parser,
            store=store,
            processing_timeout_seconds=0.01,
        )

    return build_manager


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["memory", "redis"])
async def test_task_backends_expose_owner_scoped_dashboard_contract(
    backend: str, tmp_path: Path
):
    async def parser(path: str, request: SubmitTaskRequest) -> str:
        if request.filename.startswith("fail"):
            raise RuntimeError("expected failure")
        return f"# parsed for {request.owner_id}"

    build_manager = _backend_factory(backend, tmp_path, parser)
    manager = build_manager()
    await manager.start()

    owner_a_ok = tmp_path / f"{backend}-owner-a-ok.pdf"
    owner_a_ok.write_text("demo", encoding="utf-8")
    owner_a_fail = tmp_path / f"{backend}-owner-a-fail.pdf"
    owner_a_fail.write_text("demo", encoding="utf-8")
    owner_b_ok = tmp_path / f"{backend}-owner-b-ok.pdf"
    owner_b_ok.write_text("demo", encoding="utf-8")

    task_a_ok = await manager.submit(
        SubmitTaskRequest(
            filename="owner-a-ok.pdf",
            file_path=str(owner_a_ok),
            owner_id="owner-a",
        )
    )
    task_a_fail = await manager.submit(
        SubmitTaskRequest(
            filename="fail-owner-a.pdf",
            file_path=str(owner_a_fail),
            owner_id="owner-a",
        )
    )
    task_b_ok = await manager.submit(
        SubmitTaskRequest(
            filename="owner-b-ok.pdf",
            file_path=str(owner_b_ok),
            owner_id="owner-b",
        )
    )

    await _wait_status(manager, task_a_ok.task_id, TaskStatus.completed)
    await _wait_status(manager, task_a_fail.task_id, TaskStatus.failed)
    await _wait_status(manager, task_b_ok.task_id, TaskStatus.completed)

    dashboard = await manager.get_dashboard(recent_limit=10, owner_id="owner-a")
    assert dashboard["stats"]["completed"] == 1
    assert dashboard["stats"]["failed"] == 1
    assert dashboard["stats"]["pending"] == 0
    assert dashboard["queue"]["queued"] == 0
    assert dashboard["queue"]["processing"] == 0
    assert dashboard["success_rate"] == 0.5
    assert len(dashboard["recent_tasks"]) == 2
    assert all(item["owner_id"] == "owner-a" for item in dashboard["recent_tasks"])

    await manager.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["memory", "redis"])
async def test_task_backends_cancel_retry_and_resume_contract(backend: str, tmp_path: Path):
    async def parser(path: str, request: SubmitTaskRequest) -> str:
        return "# parsed"

    build_manager = _backend_factory(backend, tmp_path, parser)
    manager = build_manager()
    await manager.start()
    await manager.pause_queue()

    file_path = tmp_path / f"{backend}-cancel-retry.pdf"
    file_path.write_text("demo", encoding="utf-8")

    task = await manager.submit(
        SubmitTaskRequest(
            filename="cancel-retry.pdf",
            file_path=str(file_path),
            owner_id="owner-a",
        )
    )

    assert await manager.cancel_task(task.task_id, owner_id="owner-a") is True
    canceled = await manager.get_task(task.task_id, owner_id="owner-a")
    assert canceled is not None
    assert canceled.status == TaskStatus.canceled

    assert await manager.retry_task(task.task_id, owner_id="owner-a") is True
    await manager.resume_queue()
    completed = await _wait_status(manager, task.task_id, TaskStatus.completed)
    assert completed.result == "# parsed"
    assert completed.retry_count == 1

    await manager.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["memory", "redis"])
async def test_task_backends_recover_pending_work_after_restart(
    backend: str, tmp_path: Path
):
    async def parser(path: str, request: SubmitTaskRequest) -> str:
        return f"# resumed {request.owner_id}"

    build_manager = _backend_factory(backend, tmp_path, parser)

    file_path = tmp_path / f"{backend}-restart.pdf"
    file_path.write_text("demo", encoding="utf-8")

    manager1 = build_manager()
    await manager1.start()
    await manager1.pause_queue()
    task = await manager1.submit(
        SubmitTaskRequest(
            filename="restart.pdf",
            file_path=str(file_path),
            owner_id="owner-a",
        )
    )
    health_before_stop = await manager1.get_queue_health(owner_id="owner-a")
    assert health_before_stop.queued == 1
    await manager1.stop()

    manager2 = build_manager()
    await manager2.start()
    await manager2.resume_queue()
    completed = await _wait_status(manager2, task.task_id, TaskStatus.completed, timeout=4.0)
    assert completed.result == "# resumed owner-a"
    await manager2.stop()


@pytest.mark.asyncio
async def test_redis_task_manager_requeues_stale_processing_tasks(tmp_path: Path):
    redis = FakeRedis()
    store = RedisTaskStore(redis, use_lua=False)

    async def parser(path: str, request: SubmitTaskRequest) -> str:
        return "# recovered"

    manager = RedisTaskManager(
        worker_count=1,
        parser_func=parser,
        store=store,
        processing_timeout_seconds=0.01,
        max_auto_retries=1,
    )
    await manager.start()
    await manager.pause_queue()

    file_path = tmp_path / "redis-timeout.pdf"
    file_path.write_text("demo", encoding="utf-8")
    task = await manager.submit(
        SubmitTaskRequest(
            filename="redis-timeout.pdf",
            file_path=str(file_path),
            owner_id="owner-a",
        )
    )

    claimed = await store.claim_next_task()
    assert claimed is not None
    assert claimed.task_id == task.task_id

    redis.zsets["queue:processing"][task.task_id] = 0.0
    manager._last_timeout_check = 0.0
    await manager._maybe_requeue_timeouts()

    requeued = await manager.get_task(task.task_id)
    assert requeued is not None
    assert requeued.status == TaskStatus.pending
    assert requeued.retry_count == 1

    await manager.resume_queue()
    completed = await _wait_status(manager, task.task_id, TaskStatus.completed, timeout=4.0)
    assert completed.result == "# recovered"
    await manager.stop()
