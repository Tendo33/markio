from pathlib import Path

from markio.schemas.task_schemas import SubmitTaskRequest
from markio.services.redis_task_manager import RedisTaskManager
from markio.services.task_manager import AsyncTaskManager
from markio.services.task_manager_base import BaseTaskManager


def test_task_managers_inherit_shared_base():
    assert issubclass(AsyncTaskManager, BaseTaskManager)
    assert issubclass(RedisTaskManager, BaseTaskManager)


def test_shared_cache_key_builder_matches_between_managers(tmp_path: Path):
    file_path = tmp_path / "cache.pdf"
    file_path.write_text("same-content", encoding="utf-8")

    request = SubmitTaskRequest(filename="cache.pdf", file_path=str(file_path))

    memory_manager = AsyncTaskManager(worker_count=1, parser_func=None)
    redis_manager = RedisTaskManager(worker_count=1, parser_func=None)

    assert memory_manager._build_cache_key(request) == redis_manager._build_cache_key(
        request
    )


def test_cache_key_includes_owner_id(tmp_path: Path):
    file_path = tmp_path / "cache-owner.pdf"
    file_path.write_text("same-content", encoding="utf-8")

    manager = AsyncTaskManager(worker_count=1, parser_func=None)
    request_a = SubmitTaskRequest(
        filename="cache-owner.pdf",
        file_path=str(file_path),
        owner_id="owner-a",
    )
    request_b = SubmitTaskRequest(
        filename="cache-owner.pdf",
        file_path=str(file_path),
        owner_id="owner-b",
    )

    assert manager._build_cache_key(request_a) != manager._build_cache_key(request_b)
