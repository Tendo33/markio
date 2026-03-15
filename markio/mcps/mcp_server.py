"""
markio MCP Server Module - Simplified Version

This module provides a Model Context Protocol (MCP) server for the markio API,
enabling seamless integration with AI assistants and other MCP-compatible clients.
The server offers unified document parsing capabilities with automatic file type
detection and routing.

Key Features:
- Unified document parsing interface via MCP
- Automatic file type detection and parser routing
- Support for multiple document formats (PDF, DOC, DOCX, PPT, PPTX, XLSX, HTML, EPUB, images)
- URL parsing tool for web content
- Simplified interface with minimal configuration

Supported File Types:
- Documents: .doc, .docx, .pdf, .epub
- Presentations: .ppt, .pptx
- Spreadsheets: .xlsx
- Web content: .html, .htm
- Images: .png, .jpg, .jpeg
"""

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi_mcp import FastApiMCP

from markio.auth import require_auth_user
from markio.parsers import (
    doc_parser,
    docx_parser,
    epub_parser,
    html_parser,
    image_parser,
    pdf_parser,
    pdf_parser_vlm,
    ppt_parser,
    pptx_parser,
    xlsx_parser,
)
from markio.schemas.parser_base import BaseParserConfig
from markio.schemas.parsers_schemas import (
    DOCXParserConfig,
    EPUBParserConfig,
    HTMLParserConfig,
    ImageParserConfig,
    PDFParserConfig,
    PPTParserConfig,
    PPTXParserConfig,
    XLSXParserConfig,
)
from markio.routers._request_guards import enforce_upload_size
from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


DEPRECATION_HEADERS = {
    "Deprecation": "true",
    "Sunset": "Wed, 30 Jun 2027 00:00:00 GMT",
    "Link": '</v1/mcp>; rel="successor-version"',
    "X-Markio-Deprecated": "Use /v1/mcp/* endpoints",
}


class MarkioMCP:
    """
    Markio MCP Server - Model Context Protocol implementation for document parsing.

    This class provides a unified MCP interface for the Markio document parsing
    capabilities. It supports various document formats with automatic file type
    detection and routing to appropriate parsers.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize the Markio MCP server.

        Args:
            app: The FastAPI application instance to mount the MCP server to
        """
        self.app = app
        self.mcp = FastApiMCP(app)
        self.mcp.mount()

        # File extension to parser mapping
        # Format: (parser_function, config_class)
        self.FILE_PARSERS: Dict[str, tuple] = {
            ".doc": (doc_parser.doc_parse_main, DOCXParserConfig),
            ".docx": (docx_parser.docx_parse_main, DOCXParserConfig),
            ".pdf": (pdf_parser.pdf_parse_main, PDFParserConfig),
            ".ppt": (ppt_parser.ppt_parse_main, PPTParserConfig),
            ".pptx": (pptx_parser.pptx_parse_main, PPTXParserConfig),
            ".xlsx": (xlsx_parser.xlsx_parse_main, XLSXParserConfig),
            ".html": (html_parser.html_parse_main, HTMLParserConfig),
            ".htm": (html_parser.html_parse_main, HTMLParserConfig),
            ".epub": (epub_parser.epub_parse_main, EPUBParserConfig),
            ".png": (image_parser.image_parse_main, ImageParserConfig),
            ".jpg": (image_parser.image_parse_main, ImageParserConfig),
            ".jpeg": (image_parser.image_parse_main, ImageParserConfig),
        }

        self.setup_mcp()

    def _get_file_extension(self, file_path: str) -> str:
        """Extract file extension from file path"""
        return os.path.splitext(file_path)[1].lower()

    def _validate_file_type(self, file_path: str) -> str:
        """Validate file type and return the file extension."""
        file_extension = self._get_file_extension(file_path)

        if file_extension not in self.FILE_PARSERS:
            supported_types = ", ".join(self.FILE_PARSERS.keys())
            raise ValueError(
                f"Unsupported file type '{file_extension}'. "
                f"Supported types are: {supported_types}"
            )

        return file_extension

    def _create_parser_config(self, file_extension: str) -> BaseParserConfig:
        """Create appropriate parser configuration with default values."""
        _, config_class = self.FILE_PARSERS[file_extension]

        # Use default values for all parameters
        config_kwargs = {
            "save_parsed_content": False,
            "output_dir": settings.output_dir,
        }

        # Add PDF-specific default configuration
        if file_extension == ".pdf":
            config_kwargs.update(
                {
                    "parse_method": "auto",
                    "save_middle_content": False,
                    "start_page": 0,
                    "end_page": None,
                }
            )

        return config_class(**config_kwargs)

    def _get_parser_function(self, file_extension: str):
        """Get the appropriate parser function for the file type."""
        parser_func, _ = self.FILE_PARSERS[file_extension]
        return parser_func

    @staticmethod
    def _mark_legacy_endpoint(response: Response) -> None:
        for key, value in DEPRECATION_HEADERS.items():
            response.headers[key] = value

    async def _parse_document(
        self, file_path: str, file_extension: str, config: BaseParserConfig
    ) -> str:
        """Parse document using the appropriate parser with configuration."""
        parser_kwargs = config.model_dump(exclude_none=True)

        if file_extension == ".pdf":
            # For PDF files, select parser based on environment variables
            pdf_parse_engine = settings.pdf_parse_engine
            logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

            if pdf_parse_engine == "pipeline":
                # Use pipeline parser
                return await pdf_parser.pdf_parse_main(
                    resource_path=file_path,
                    **parser_kwargs,
                )
            elif pdf_parse_engine in ["vlm-vllm-engine", "vlm-vllm-client"]:
                # Use VLM parser with vLLM backend
                return await pdf_parser_vlm.pdf_parse_vlm_main(
                    resource_path=file_path,
                    **parser_kwargs,
                )
            else:
                error_msg = f"Invalid PDF_PARSE_ENGINE value: {pdf_parse_engine}. Must be 'pipeline', 'vlm-vllm-engine', or 'vlm-vllm-client'"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            # For other file types, use default parser
            parser_func = self._get_parser_function(file_extension)
            return await parser_func(
                resource_path=file_path,
                **parser_kwargs,
            )

    def setup_mcp(self):
        """Setup MCP endpoints and tools for document parsing (Best Practice)."""
        secure_router = APIRouter(
            prefix="/v1",
            dependencies=[Depends(require_auth_user)],
        )
        legacy_router = APIRouter(dependencies=[Depends(require_auth_user)])

        async def _convert_document_core(file: UploadFile) -> dict[str, Any]:
            import tempfile

            max_upload_size = int(settings.task_max_upload_size_bytes)
            try:
                # 1. Save uploaded file to temporary directory
                suffix = os.path.splitext(file.filename or "")[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    bytes_written = 0
                    while True:
                        chunk = await file.read(1024 * 1024)
                        if not chunk:
                            break
                        bytes_written += len(chunk)
                        enforce_upload_size(
                            bytes_written=bytes_written,
                            max_bytes=max_upload_size,
                        )
                        tmp.write(chunk)
                    tmp_path = tmp.name
                # 2. Validate file type
                file_extension = self._validate_file_type(tmp_path)
                config = self._create_parser_config(file_extension)
                logger.info(
                    f"Starting to parse uploaded file {file.filename} as {file_extension}"
                )
                markdown_content = await self._parse_document(
                    tmp_path, file_extension, config
                )
                logger.info(
                    f"Successfully parsed uploaded file {file.filename} to markdown"
                )
                return {
                    "status": "success",
                    "result": markdown_content,
                    "file_type": file_extension,
                    "parsed_at": datetime.now().isoformat(),
                }
            except ValueError as exc:
                logger.error(
                    f"Validation error for uploaded file {file.filename}: {exc}"
                )
                return {
                    "status": "error",
                    "message": str(exc),
                    "file_type": suffix if "suffix" in locals() else "unknown",
                    "parsed_at": datetime.now().isoformat(),
                }
            except HTTPException:
                logger.warning(f"Uploaded file {file.filename} rejected by request guard")
                raise
            except Exception:
                logger.exception(f"Error parsing uploaded file {file.filename}")
                return {
                    "status": "error",
                    "message": "Parsing failed",
                    "file_type": suffix if "suffix" in locals() else "unknown",
                    "parsed_at": datetime.now().isoformat(),
                }
            finally:
                # 3. Clean up temporary files
                try:
                    if "tmp_path" in locals() and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass

        @secure_router.post(
            "/mcp/convert_document",
            operation_id="v1_convert_document",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def convert_document(
            file: UploadFile = File(
                ...,
                description="Convert uploaded document files (supports PDF, DOC, DOCX, EPUB, PPT, PPTX, XLSX, HTML, HTM, PNG, JPG, JPEG) to Markdown",
            ),
        ):
            return await _convert_document_core(file)

        @legacy_router.post(
            "/mcp/convert_document",
            operation_id="legacy_convert_document",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def legacy_convert_document(
            response: Response,
            file: UploadFile = File(
                ...,
                description="Convert uploaded document files (supports PDF, DOC, DOCX, EPUB, PPT, PPTX, XLSX, HTML, HTM, PNG, JPG, JPEG) to Markdown",
            ),
        ):
            self._mark_legacy_endpoint(response)
            return await _convert_document_core(file)

        async def _parse_url_core(url: str) -> dict[str, Any]:
            """
            Parse web content and convert to Markdown.

            Parameters:
                url (str): Target webpage URL.
            Returns:
                status (str): "success" or "error"
                result (str, optional): Parsed Markdown content
                message (str, optional): Error message
                file_type (str): Fixed as "url"
                parsed_at (str): Parsing completion timestamp
            Example:
                >>> POST /mcp/parse_url {"url": "https://example.com/article"}
            """
            try:
                from markio.parsers.url_parser import url_parse_main

                if not url.startswith(("http://", "https://")):
                    raise ValueError("URL must start with http:// or https://")
                logger.info(f"Starting to parse URL: {url}")
                result = await url_parse_main(
                    url=url,
                    save_parsed_content=False,
                    output_dir=settings.output_dir,
                )
                if isinstance(result, str):
                    logger.info(f"Successfully parsed URL: {url}")
                    return {
                        "status": "success",
                        "result": result,
                        "file_type": "url",
                        "parsed_at": datetime.now().isoformat(),
                    }

                logger.error(f"Failed to parse URL {url}: parser returned non-string")
                return {
                    "status": "error",
                    "message": "URL parsing failed",
                    "file_type": "url",
                    "parsed_at": datetime.now().isoformat(),
                }
            except ValueError as exc:
                logger.error(f"Validation error for URL {url}: {exc}")
                return {
                    "status": "error",
                    "message": str(exc),
                    "file_type": "url",
                    "parsed_at": datetime.now().isoformat(),
                }
            except Exception:
                logger.exception(f"Error parsing URL {url}")
                return {
                    "status": "error",
                    "message": "URL parsing failed",
                    "file_type": "url",
                    "parsed_at": datetime.now().isoformat(),
                }

        @secure_router.post(
            "/mcp/parse_url",
            operation_id="v1_parse_url",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def parse_url(
            url: str = Body(
                ...,
                embed=True,
                description="Convert web URL to Markdown",
            ),
        ):
            return await _parse_url_core(url)

        @legacy_router.post(
            "/mcp/parse_url",
            operation_id="legacy_parse_url",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def legacy_parse_url(
            response: Response,
            url: str = Body(
                ...,
                embed=True,
                description="Convert web URL to Markdown",
            ),
        ):
            self._mark_legacy_endpoint(response)
            return await _parse_url_core(url)

        self.app.include_router(secure_router)
        self.app.include_router(legacy_router)
        self.mcp.setup_server()
        logger.info("Markio MCP server mounted successfully")
