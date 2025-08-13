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

from fastapi import APIRouter, Body, FastAPI, File, UploadFile
from fastapi_mcp import FastApiMCP

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
from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


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

    async def _parse_document(
        self, file_path: str, file_extension: str, config: BaseParserConfig
    ) -> str:
        """Parse document using the appropriate parser with configuration."""
        if file_extension == ".pdf":
            # For PDF files, select parser based on environment variables
            pdf_parse_engine = settings.pdf_parse_engine
            logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

            if pdf_parse_engine == "pipeline":
                # Use pipeline parser
                return await pdf_parser.pdf_parse_main(
                    resource_path=file_path,
                    save_parsed_content=config.save_parsed_content,
                    output_dir=config.output_dir,
                )
            elif pdf_parse_engine == "vlm-sglang-engine":
                # Use VLM parser
                return await pdf_parser_vlm.pdf_parse_vlm_main(
                    resource_path=file_path,
                    save_parsed_content=config.save_parsed_content,
                    output_dir=config.output_dir,
                )
            else:
                error_msg = f"Invalid PDF_PARSE_ENGINE value: {pdf_parse_engine}. Must be 'pipeline' or 'vlm-sglang-engine'"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            # For other file types, use default parser
            parser_func = self._get_parser_function(file_extension)
            return await parser_func(file_path, config)

    def setup_mcp(self):
        """Setup MCP endpoints and tools for document parsing (Best Practice)."""
        router = APIRouter()

        @router.post(
            "/mcp/convert_document",
            operation_id="convert_document",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def convert_document(
            file: UploadFile = File(
                ...,
                description="将上传的文档文件（支持 PDF, DOC, DOCX, EPUB, PPT, PPTX, XLSX, HTML, HTM, PNG, JPG, JPEG）转换为Markdown",
            ),
        ):
            """
            上传文档并自动转换为 Markdown。

            参数:
                file (UploadFile): 上传的文档文件。
            返回:
                status (str): "success" 或 "error"
                result (str, optional): 解析后的 Markdown 内容
                message (str, optional): 错误信息
                file_type (str): 检测到的文件类型
                parsed_at (str): 解析完成时间戳
            示例:
                >>> multipart/form-data 上传 PDF 文件
            """
            import shutil
            import tempfile

            try:
                # 1. 保存上传文件到临时目录
                suffix = os.path.splitext(file.filename)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    shutil.copyfileobj(file.file, tmp)
                    tmp_path = tmp.name
                # 2. 校验文件类型
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
            except ValueError as ve:
                logger.error(
                    f"Validation error for uploaded file {file.filename}: {str(ve)}"
                )
                return {
                    "status": "error",
                    "message": str(ve),
                    "file_type": suffix if "suffix" in locals() else "unknown",
                    "parsed_at": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error parsing uploaded file {file.filename}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Parsing failed: {str(e)}",
                    "file_type": suffix if "suffix" in locals() else "unknown",
                    "parsed_at": datetime.now().isoformat(),
                }
            finally:
                # 3. 清理临时文件
                try:
                    if "tmp_path" in locals() and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass

        @router.post(
            "/mcp/parse_url",
            operation_id="parse_url",
            tags=["MCP Tools"],
            response_model=dict[str, Any],
        )
        async def parse_url(
            url: str = Body(
                ...,
                embed=True,
                description="将网页URL转换为Markdown",
            ),
        ):
            """
            解析网页内容并转换为 Markdown。

            参数:
                url (str): 目标网页 URL。
            返回:
                status (str): "success" 或 "error"
                result (str, optional): 解析后的 Markdown 内容
                message (str, optional): 错误信息
                file_type (str): 固定为 "url"
                parsed_at (str): 解析完成时间戳
            示例:
                >>> POST /mcp/parse_url {"url": "https://example.com/article"}
            """
            try:
                from markio.parsers.url_parser import url_parse_main

                if not url.startswith(("http://", "https://")):
                    raise ValueError("URL must start with http:// or https://")
                logger.info(f"Starting to parse URL: {url}")
                result = await url_parse_main(
                    url=url, save_parsed_content=False, output_dir="outputs"
                )
                if isinstance(result, str):
                    logger.info(f"Successfully parsed URL: {url}")
                    return {
                        "status": "success",
                        "result": result,
                        "file_type": "url",
                        "parsed_at": datetime.now().isoformat(),
                    }
                else:
                    error_detail = (
                        result.body.decode() if hasattr(result, "body") else str(result)
                    )
                    logger.error(f"Failed to parse URL {url}: {error_detail}")
                    return {
                        "status": "error",
                        "message": f"URL parsing failed: {error_detail}",
                        "file_type": "url",
                        "parsed_at": datetime.now().isoformat(),
                    }
            except ValueError as ve:
                logger.error(f"Validation error for URL {url}: {str(ve)}")
                return {
                    "status": "error",
                    "message": str(ve),
                    "file_type": "url",
                    "parsed_at": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error parsing URL {url}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"URL parsing failed: {str(e)}",
                    "file_type": "url",
                    "parsed_at": datetime.now().isoformat(),
                }

        self.app.include_router(router)
        self.mcp.setup_server()
        logger.info("Markio MCP server mounted successfully")
