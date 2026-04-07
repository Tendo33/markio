from __future__ import annotations

from fastapi import FastAPI, Request


def _security_headers() -> dict[str, str]:
    return {
        "X-Frame-Options": "SAMEORIGIN",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data: https:",
                "connect-src 'self' https:",
                "frame-ancestors 'self'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        ),
    }


def add_security_headers_middleware(app: FastAPI) -> None:
    headers = _security_headers()

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for key, value in headers.items():
            if key not in response.headers:
                response.headers[key] = value
        return response
