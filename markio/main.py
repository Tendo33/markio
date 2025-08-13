import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from markio.markio_mcp.markio_mcp_server import MarkioMCP
from markio.middlewares.handle import handle_middleware
from markio.routers.doc_router import router as doc_router
from markio.routers.docx_router import router as docx_router
from markio.routers.epub_router import router as epub_router
from markio.routers.file_router import router as file_router
from markio.routers.html_router import router as html_router
from markio.routers.image_router import router as image_router
from markio.routers.pdf_router import router as pdf_router
from markio.routers.ppt_router import router as ppt_router
from markio.routers.pptx_router import router as pptx_router
from markio.routers.url_router import router as url_router
from markio.routers.xlsx_router import router as xlsx_router
from markio.settings import settings
from markio.utils.logger_config import get_logger, setup_logger
from markio.utils.model_manager import get_model_manager

# Initialize logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup project logging
LOG_DIR = settings.log_dir
API_PREFIX = "/v1"
LOG_LEVEL = settings.log_level
PROJECT_NAME = "Markio"

setup_logger(project_name=PROJECT_NAME, log_dir=LOG_DIR, log_level=LOG_LEVEL)
logger = get_logger(__name__)


def initialize_models_safely():
    """Safely initialize models with error handling"""
    model_manager = get_model_manager()

    if model_manager.is_initialized():
        logger.info(
            f"Models already initialized with engine: {model_manager.get_current_engine()}"
        )
        return True

    logger.info("Starting model initialization...")
    if model_manager.initialize_models():
        logger.info(
            f"Models initialized successfully with engine: {model_manager.get_current_engine()}"
        )
        return True
    else:
        error_msg = model_manager.get_initialization_error()
        logger.error(f"Model initialization failed: {error_msg}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting MarkioApi server")

    if not initialize_models_safely():
        logger.error("Failed to initialize models, server may not function properly")

    yield

    logger.info("Shutting down MarkioApi server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance"""
    app = FastAPI(
        title=PROJECT_NAME,
        description="API for converting various file formats to Markdown using different parsers and converters.",
        lifespan=lifespan,
    )
    handle_middleware(app)
    logger.info("Global middleware initialized")
    return app


def register_routers(app: FastAPI):
    """Register all routers with logging"""
    routers = [
        (file_router, "FILE"),
        (pdf_router, "PDF"),
        (docx_router, "DOCX"),
        (doc_router, "DOC"),
        (xlsx_router, "XLSX"),
        (html_router, "HTML"),
        (epub_router, "EPUB"),
        (url_router, "URL"),
        (pptx_router, "PPTX"),
        (ppt_router, "PPT"),
        (image_router, "IMAGE"),
    ]
    for router, name in routers:
        app.include_router(router, prefix=API_PREFIX)
        logger.debug(f"Registered router for {name} conversion")


def mount_mcp_server(app: FastAPI):
    """Initialize and mount MCP server"""
    mcp_server = MarkioMCP(app)
    logger.info("MCP server mounted")
    return mcp_server


app = create_app()
mount_mcp_server(app)


@app.get("/")
async def welcome():
    """Welcome endpoint that redirects to API documentation"""
    logger.info("Welcome endpoint accessed")
    return RedirectResponse(url="/docs")


def main():
    """Main application entry point"""
    if not initialize_models_safely():
        logger.error("Failed to initialize models, server may not function properly")

    register_routers(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
