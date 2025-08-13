from fastapi import FastAPI

from markio.middlewares.cors_middleware import add_cors_middleware
from markio.middlewares.gzip_middleware import add_gzip_middleware
from markio.middlewares.trace_middleware import add_trace_middleware
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


def handle_middleware(app: FastAPI):
    """Initialize and configure all global middleware for the FastAPI application"""
    logger.info("Initializing global middleware")

    add_cors_middleware(app)
    logger.debug("CORS middleware added")

    add_gzip_middleware(app)
    logger.debug("Gzip middleware added")

    add_trace_middleware(app)
    logger.debug("Trace middleware added")

    logger.info("All middleware initialized successfully")
