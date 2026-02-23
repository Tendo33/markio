from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR

from markio.middlewares.trace_middleware.ctx import TraceCtx


def _request_id() -> str:
    return TraceCtx.get_id() or uuid4().hex


def _error_payload(
    *,
    code: str,
    message: str,
    details: object | None = None,
) -> dict:
    request_id = _request_id()
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details,
        },
        "detail": message,
        "request_id": request_id,
    }


def add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, str):
            message = exc.detail
            details: object | None = None
        else:
            message = "Request failed"
            details = exc.detail
        code = f"http_{exc.status_code}"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code=code, message=message, details=details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_payload(
                code="validation_error",
                message="Request validation failed",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                code="internal_error",
                message="Internal server error",
            ),
        )
