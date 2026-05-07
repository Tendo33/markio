import markio.main as main_module
import pytest
from httpx import ASGITransport, AsyncClient


def test_task_routes_registered():
    paths = {route.path for route in main_module.app.routes}
    assert "/v1/tasks/submit" in paths
    assert "/v1/tasks/stats" in paths
    assert "/v1/tasks/dashboard" in paths
    assert "/v1/tasks/queue/pause" in paths
    assert "/v1/tasks/queue/resume" in paths
    assert "/v1/tasks/{task_id}/cancel" in paths
    assert "/v1/tasks/{task_id}/retry" in paths
    assert "/v1/tasks/{task_id}" in paths


def test_health_routes_registered():
    paths = {route.path for route in main_module.app.routes}
    assert "/healthz" in paths
    assert "/readyz" in paths


@pytest.mark.asyncio
async def test_v1_routes_require_bearer_auth():
    async with AsyncClient(
        transport=ASGITransport(app=main_module.app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/v1/parse_url",
            params={"url": "https://example.com"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_default_security_headers_are_applied():
    async with AsyncClient(
        transport=ASGITransport(app=main_module.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    csp = response.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" not in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


def test_main_entrypoint_relies_on_lifespan_for_model_initialization(monkeypatch):
    calls = {"init": 0, "run": None}

    def fake_initialize_models_safely():
        calls["init"] += 1
        return True

    def fake_run(app, host, port):
        calls["run"] = (app, host, port)

    monkeypatch.setattr(main_module, "initialize_models_safely", fake_initialize_models_safely)
    monkeypatch.setattr(main_module.uvicorn, "run", fake_run)
    monkeypatch.setattr(main_module.settings, "host", "127.0.0.1", raising=False)
    monkeypatch.setattr(main_module.settings, "port", 8765, raising=False)

    main_module.main()

    assert calls["init"] == 0
    assert calls["run"] == (main_module.app, "127.0.0.1", 8765)
