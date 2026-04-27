from __future__ import annotations

import threading
import time
from collections import deque
from ipaddress import ip_address
from re import compile as re_compile
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from markio.middlewares.trace_middleware.ctx import TraceCtx
from markio.settings import settings


class _RateLimitMiddleware(BaseHTTPMiddleware):
    _UUID_SEGMENT = re_compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    )
    _HEX_SEGMENT = re_compile(r"^[0-9a-fA-F]{16,}$")

    def __init__(
        self,
        app,
        *,
        max_requests: int,
        window_seconds: int,
        max_buckets: int,
        trust_proxy_headers: bool,
    ) -> None:
        super().__init__(app)
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self.max_buckets = max(1, int(max_buckets))
        self.trust_proxy_headers = bool(trust_proxy_headers)
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, str], deque[float]] = {}
        self._bucket_last_seen: dict[tuple[str, str], float] = {}
        self._last_gc_monotonic = 0.0

    def _request_id(self, request: Request) -> str:
        trace_request_id = TraceCtx.get_id().strip()
        if trace_request_id:
            return trace_request_id
        incoming = request.headers.get("x-request-id") or request.headers.get("request-id")
        if incoming:
            return incoming
        return uuid4().hex

    def _route_bucket_key(self, request: Request) -> str:
        route = request.scope.get("route")
        route_path = getattr(route, "path", "")
        if route_path:
            return route_path
        return self._normalize_path(request.url.path)

    def _normalize_path(self, path: str) -> str:
        normalized_segments: list[str] = []
        for segment in path.split("/"):
            if not segment:
                continue
            if segment.isdigit():
                normalized_segments.append("{int}")
                continue
            if self._UUID_SEGMENT.match(segment):
                normalized_segments.append("{uuid}")
                continue
            if self._HEX_SEGMENT.match(segment):
                normalized_segments.append("{id}")
                continue
            normalized_segments.append(segment)
        return "/" + "/".join(normalized_segments)

    @staticmethod
    def _normalize_forwarded_for(value: str) -> str:
        candidate = value.strip().strip('"')
        if not candidate or candidate.lower() == "unknown":
            return ""
        if candidate.startswith("[") and "]" in candidate:
            return candidate[1 : candidate.index("]")]
        if candidate.count(":") == 1 and "." in candidate:
            host, _, _ = candidate.partition(":")
            return host.strip()
        return candidate

    def _proxy_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("forwarded", "")
        if forwarded:
            for item in forwarded.split(","):
                for part in item.split(";"):
                    key, _, value = part.strip().partition("=")
                    if key.lower() != "for":
                        continue
                    normalized = self._normalize_forwarded_for(value)
                    if normalized:
                        return normalized

        x_forwarded_for = request.headers.get("x-forwarded-for", "")
        if x_forwarded_for:
            for item in x_forwarded_for.split(","):
                normalized = self._normalize_forwarded_for(item)
                if normalized:
                    return normalized

        return ""

    def _client_ip(self, request: Request) -> str:
        if self.trust_proxy_headers:
            proxied_ip = self._proxy_client_ip(request)
            if proxied_ip:
                try:
                    return ip_address(proxied_ip).compressed
                except ValueError:
                    return proxied_ip

        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _prune_buckets(
        self,
        *,
        now: float,
        window_start: float,
        protected_key: tuple[str, str],
    ) -> None:
        should_gc = (
            len(self._buckets) > self.max_buckets
            or now - self._last_gc_monotonic >= 1.0
        )
        if not should_gc:
            return

        self._last_gc_monotonic = now
        stale_keys = [
            key
            for key, timestamps in self._buckets.items()
            if key != protected_key
            and (not timestamps or self._bucket_last_seen.get(key, 0.0) < window_start)
        ]
        for key in stale_keys:
            self._buckets.pop(key, None)
            self._bucket_last_seen.pop(key, None)

        overflow = len(self._buckets) - self.max_buckets
        if overflow <= 0:
            return

        sortable = sorted(
            (
                (key, seen_at)
                for key, seen_at in self._bucket_last_seen.items()
                if key != protected_key
            ),
            key=lambda item: item[1],
        )
        for key, _ in sortable[:overflow]:
            self._buckets.pop(key, None)
            self._bucket_last_seen.pop(key, None)

    def _check(self, request: Request) -> bool:
        client_ip = self._client_ip(request)
        bucket_key = (client_ip, self._route_bucket_key(request))
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(bucket_key, deque())
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            self._bucket_last_seen[bucket_key] = now
            self._prune_buckets(
                now=now,
                window_start=window_start,
                protected_key=bucket_key,
            )
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
    max_buckets: int | None = None,
    trust_proxy_headers: bool | None = None,
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
        max_buckets=(
            max_buckets
            if max_buckets is not None
            else settings.rate_limit_max_buckets
        ),
        trust_proxy_headers=(
            trust_proxy_headers
            if trust_proxy_headers is not None
            else getattr(settings, "rate_limit_trust_proxy_headers", False)
        ),
    )
