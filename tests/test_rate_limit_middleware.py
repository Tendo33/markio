from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from markio.middlewares.rate_limit_middleware import _RateLimitMiddleware, add_rate_limit_middleware


def _dummy_app():
    async def app(scope, receive, send):
        return None

    return app


def _build_request(path: str, client_ip: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": (client_ip, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_rate_limit_uses_route_template_dimension_for_dynamic_paths():
    app = FastAPI()
    add_rate_limit_middleware(
        app,
        enabled=True,
        max_requests=1,
        window_seconds=60,
        max_buckets=100,
    )

    @app.get("/items/{item_id}")
    async def get_item(item_id: str):
        return {"item_id": item_id}

    client = TestClient(app)
    first = client.get("/items/100")
    second = client.get("/items/200")

    assert first.status_code == 200
    assert second.status_code == 429


def test_rate_limit_bucket_count_is_capped_for_high_cardinality_paths():
    middleware = _RateLimitMiddleware(
        _dummy_app(),
        max_requests=100,
        window_seconds=60,
        max_buckets=5,
    )

    for index in range(50):
        request = _build_request(f"/search/value-{index}")
        allowed = middleware._check(request)
        assert allowed is True

    assert len(middleware._buckets) <= 5
