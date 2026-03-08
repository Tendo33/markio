from markio.main import app
import pytest
from httpx import ASGITransport, AsyncClient


def test_task_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/v1/tasks/submit" in paths
    assert "/v1/tasks/stats" in paths
    assert "/v1/tasks/dashboard" in paths
    assert "/v1/tasks/queue/pause" in paths
    assert "/v1/tasks/queue/resume" in paths
    assert "/v1/tasks/{task_id}/cancel" in paths
    assert "/v1/tasks/{task_id}/retry" in paths
    assert "/v1/tasks/{task_id}" in paths


def test_health_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/healthz" in paths
    assert "/readyz" in paths


@pytest.mark.asyncio
async def test_v1_routes_require_bearer_auth():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )
    assert response.status_code == 401
