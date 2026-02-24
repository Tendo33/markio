from __future__ import annotations

import threading
import time
from collections import deque
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from markio.middlewares.trace_middleware.ctx import TraceCtx
from markio.settings import settings


class _RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        super().__init__(app)
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, str], deque[float]] = {}

    def _request_id(self, request: Request) -> str:
        trace_request_id = TraceCtx.get_id().strip()
        if trace_request_id:
            return trace_request_id
        incoming = request.headers.get("x-request-id") or request.headers.get("request-id")
        if incoming:
            return incoming
        return uuid4().hex

    def _check(self, request: Request) -> bool:
        client_ip = request.client.host if request.client else "unknown"
        bucket_key = (client_ip, request.url.path)
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(bucket_key, deque())
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._check(request):
            return await call_next(request)

        request_id = self._request_id(request)
        payload = {
            "error": {
                "code": "http_429",
                "message": "Rate limit exceeded",
                "request_id": request_id,
                "details": {
                    "max_requests": self.max_requests,
                    "window_seconds": self.window_seconds,
                },
            },
            "detail": "Rate limit exceeded",
            "request_id": request_id,
        }
        return JSONResponse(
            status_code=429,
            content=payload,
            headers={
                "X-Request-ID": request_id,
                "Retry-After": str(self.window_seconds),
            },
        )


def add_rate_limit_middleware(
    app: FastAPI,
    *,
    enabled: bool | None = None,
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> None:
    if enabled is None:
        enabled = settings.rate_limit_enabled
    if not enabled:
        return

    app.add_middleware(
        _RateLimitMiddleware,
        max_requests=max_requests if max_requests is not None else settings.rate_limit_requests,
        window_seconds=(
            window_seconds
            if window_seconds is not None
            else settings.rate_limit_window_seconds
        ),
    )
