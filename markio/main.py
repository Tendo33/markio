from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from markio.auth import require_auth_user
from markio.mcps.mcp_server import MarkioMCP
from markio.middlewares.error_handlers import add_error_handlers
from markio.middlewares.handle import handle_middleware
from markio.routers.doc_router import router as doc_router
from markio.routers.docx_router import router as docx_router
from markio.routers.epub_router import router as epub_router
from markio.routers.fasta_router import router as fasta_router
from markio.routers.file_router import router as file_router
from markio.routers.genbank_router import router as genbank_router
from markio.routers.html_router import router as html_router
from markio.routers.image_router import router as image_router
from markio.routers.pdf_router import router as pdf_router
from markio.routers.ppt_router import router as ppt_router
from markio.routers.pptx_router import router as pptx_router
from markio.routers.task_router import router as task_router
from markio.routers.url_router import router as url_router
from markio.routers.xlsx_router import router as xlsx_router
from markio.services.runtime import get_task_manager
from markio.settings import settings
from markio.utils.logger_config import get_logger, setup_logger
from markio.utils.model_manager import get_model_manager
from markio.utils.redis_utils import redis_manager

# Initialize logger
logger = get_logger(__name__)

# Setup project logging
LOG_DIR = settings.log_dir
API_PREFIX = "/v1"
LOG_LEVEL = settings.log_level
PROJECT_NAME = "Markio"

setup_logger(project_name=PROJECT_NAME, log_dir=LOG_DIR, log_level=LOG_LEVEL)


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
    task_manager = get_task_manager()
    if settings.redis_enabled:
        try:
            await redis_manager.initialize()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Redis initialization failed: {exc}")
    await task_manager.start()

    if not initialize_models_safely():
        logger.error("Failed to initialize models, server may not function properly")

    yield

    if settings.redis_enabled:
        await redis_manager.close()
    await task_manager.stop()
    logger.info("Shutting down MarkioApi server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance"""
    app = FastAPI(
        title=PROJECT_NAME,
        description="API for converting various file formats to Markdown using different parsers and converters.",
        lifespan=lifespan,
    )
    handle_middleware(app)
    add_error_handlers(app)
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
        (fasta_router, "FASTA"),
        (genbank_router, "GENBANK"),
        (task_router, "TASK"),
    ]
    for router, name in routers:
        app.include_router(
            router,
            prefix=API_PREFIX,
            dependencies=[Depends(require_auth_user)],
        )
        logger.debug(f"Registered router for {name} conversion")


def mount_mcp_server(app: FastAPI):
    """Initialize and mount MCP server"""
    mcp_server = MarkioMCP(app)
    logger.info("MCP server mounted")
    return mcp_server


def _build_console_fallback_html(web_console_dir: Path) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Markio Console</title>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f7f8; color: #202123; margin: 0; }}
      .container {{ max-width: 760px; margin: 8vh auto; background: #fff; border: 1px solid #e5e5eb; border-radius: 16px; padding: 28px; box-shadow: 0 1px 2px rgba(16,24,40,.06); }}
      h1 {{ margin: 0 0 8px; font-size: 24px; }}
      p {{ color: #4a4a62; line-height: 1.5; margin: 10px 0; }}
      code {{ background: #f4f4f5; padding: 2px 6px; border-radius: 6px; }}
      pre {{ background: #111827; color: #e5e7eb; border-radius: 10px; padding: 14px; overflow-x: auto; }}
    </style>
  </head>
  <body>
    <main class="container">
      <h1>Markio Console frontend is not built yet</h1>
      <p>The backend is running normally, but console static assets are missing.</p>
      <p>Expected build directory: <code>{web_console_dir}</code></p>
      <p>Build the frontend and restart the service:</p>
      <pre>cd frontend
npm install
npm run build</pre>
    </main>
  </body>
</html>
"""


def mount_web_console(app: FastAPI, web_console_dir: Path | None = None):
    web_console_dir = web_console_dir or (Path(__file__).resolve().parent / "webapp")
    index_file = web_console_dir / "index.html"
    if web_console_dir.exists() and index_file.exists():
        app.mount(
            "/console",
            StaticFiles(directory=str(web_console_dir), html=True),
            name="web_console",
        )
        logger.info(f"Web console mounted at /console from {web_console_dir}")
    else:
        logger.warning(
            f"Web console assets not found (expected {index_file}). Falling back to helper page."
        )
        html = _build_console_fallback_html(web_console_dir)

        @app.get("/console", include_in_schema=False)
        @app.get("/console/", include_in_schema=False)
        @app.get("/console/{path:path}", include_in_schema=False)
        async def console_fallback(path: str = "") -> HTMLResponse:
            return HTMLResponse(content=html, status_code=200)


app = create_app()
register_routers(app)
mount_web_console(app)

# Only mount MCP server if enabled in settings
if settings.enable_mcp:
    mount_mcp_server(app)
    logger.info("MCP server is enabled and mounted")
else:
    logger.info("MCP server is disabled")


@app.get("/")
async def welcome():
    """Welcome endpoint that redirects to API documentation"""
    logger.info("Welcome endpoint accessed")
    return RedirectResponse(url="/docs")


@app.get("/healthz", include_in_schema=False)
async def healthz() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        status_code=200,
    )


@app.get("/readyz", include_in_schema=False)
async def readyz() -> JSONResponse:
    task_manager = get_task_manager()
    model_manager = get_model_manager()

    checks = {
        "task_manager_started": getattr(task_manager, "_started", False),
        "models_initialized": model_manager.is_initialized(),
    }

    if settings.redis_enabled:
        checks["redis_available"] = redis_manager.is_available

    ready = all(checks.values())
    status_code = 200 if ready else 503
    return JSONResponse(
        {
            "status": "ready" if ready else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        status_code=status_code,
    )


def main():
    """Main application entry point"""
    if not initialize_models_safely():
        logger.error("Failed to initialize models, server may not function properly")

    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
