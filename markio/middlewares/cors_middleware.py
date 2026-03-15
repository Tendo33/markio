from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from markio.settings import settings


def _parse_origins(raw_origins: str) -> list[str]:
    values = []
    for item in (raw_origins or "").split(","):
        normalized = item.strip()
        if normalized:
            values.append(normalized.rstrip("/"))
    return values


def add_cors_middleware(app: FastAPI):
    """
    Add CORS middleware to FastAPI application.

    Args:
        app: FastAPI application instance
    """
    origins = _parse_origins(getattr(settings, "cors_allow_origins", ""))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=bool(getattr(settings, "cors_allow_credentials", True)),
        allow_methods=["*"],
        allow_headers=["*"],
    )
