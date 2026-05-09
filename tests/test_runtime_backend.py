import importlib
from pathlib import Path

import yaml

from markio.services.task_manager import AsyncTaskManager
from markio.settings import settings


def test_runtime_falls_back_to_memory_when_redis_backend_without_redis(monkeypatch):
    monkeypatch.setattr(settings, "task_queue_backend", "redis")
    monkeypatch.setattr(settings, "redis_enabled", False)

    from markio.services import runtime

    reloaded = importlib.reload(runtime)
    manager = reloaded.get_task_manager()
    assert isinstance(manager, AsyncTaskManager)


def test_compose_redis_service_uses_redis_task_backend():
    compose_path = Path(__file__).resolve().parents[1] / "compose.yaml"
    compose = yaml.safe_load(compose_path.read_text())
    environment = compose["services"]["markio"]["environment"]
    volumes = compose["services"]["markio"]["volumes"]

    assert "PYTHONPATH=/workspace" in environment
    assert "REDIS_ENABLED=true" in environment
    assert "TASK_QUEUE_BACKEND=redis" in environment
    assert "./data:/workspace/data" in volumes
    assert "./outputs:/workspace/outputs" in volumes


def test_dockerfile_builds_console_assets_in_image():
    dockerfile_path = Path(__file__).resolve().parents[1] / "Dockerfile"
    dockerfile = dockerfile_path.read_text(encoding="utf-8")

    assert "FROM node:20-bookworm-slim AS frontend-builder" in dockerfile
    assert "RUN corepack enable && pnpm install --frozen-lockfile" in dockerfile
    assert "RUN pnpm run build" in dockerfile
    assert "COPY --from=frontend-builder /frontend/dist /workspace/markio/webapp" in dockerfile
