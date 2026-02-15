import importlib

from markio.services.task_manager import AsyncTaskManager
from markio.settings import settings


def test_runtime_falls_back_to_memory_when_redis_backend_without_redis(monkeypatch):
    monkeypatch.setattr(settings, "task_queue_backend", "redis")
    monkeypatch.setattr(settings, "redis_enabled", False)

    from markio.services import runtime

    reloaded = importlib.reload(runtime)
    manager = reloaded.get_task_manager()
    assert isinstance(manager, AsyncTaskManager)
