"""
Markio SDK Module

This module provides a unified interface for parsing various document formats to Markdown.
It supports PDF, DOCX, HTML, EPUB, and image files with automatic format detection.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from markio.parsers.doc_parser import doc_parse_main
from markio.parsers.docx_parser import docx_parse_main
from markio.parsers.epub_parser import epub_parse_main
from markio.parsers.html_parser import html_parse_main
from markio.parsers.image_parser import image_parse_main
from markio.parsers.pdf_parser import pdf_parse_main
from markio.parsers.pdf_parser_vlm import pdf_parse_vlm_main
from markio.parsers.ppt_parser import ppt_parse_main
from markio.parsers.pptx_parser import pptx_parse_main
from markio.parsers.url_parser import url_parse_main
from markio.parsers.xlsx_parser import xlsx_parse_main

logger = logging.getLogger(__name__)


class MarkioSDK:
    """
    Markio SDK - A unified interface for parsing various document formats to Markdown.

    This SDK provides a simple and consistent way to parse different document formats
    into Markdown format. It supports multiple file types including:
    - PDF (with OCR and VLM support)
    - DOCX (Microsoft Word)
    - DOC (Microsoft Word - legacy format)
    - PPTX (Microsoft PowerPoint)
    - PPT (Microsoft PowerPoint - legacy format)
    - XLSX (Microsoft Excel)
    - HTML
    - URLs
    - EPUB
    - Images

    All parsers preserve the document structure, formatting, and content while converting
    to clean, readable Markdown.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Markio SDK.

        Args:
            output_dir (str): Base directory for saving parsed content and extracted assets.
                            Defaults to "output".
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def parse_pdf(
        self,
        file_path: str,
        parse_method: str = "auto",
        save_parsed_content: bool = False,
        save_middle_content: bool = False,
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Parse a PDF file to Markdown format.

        Args:
            file_path (str): Path to the PDF file
            parse_method (str): Parsing method - "auto", "ocr", or "txt"
            save_parsed_content (bool): Whether to save parsed content
            save_middle_content (bool): Whether to save intermediate processing results
            start_page (int): First page to parse (0-based)
            end_page (int): Last page to parse (inclusive)

        Returns:
            Dict containing parsed content and metadata
        """
        output_path = str(self.output_dir / Path(file_path).stem)

        markdown_content = await pdf_parse_main(
            resource_path=file_path,
            parse_method=parse_method,
            save_parsed_content=save_parsed_content,
            save_middle_content=save_middle_content,
            output_dir=str(self.output_dir),
            start_page=start_page,
            end_page=end_page,
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": output_path,
        }

    async def parse_pdf_vlm(
        self,
        file_path: str,
        save_parsed_content: bool = False,
        save_middle_content: bool = False,
        start_page: int = 0,
        end_page: Optional[int] = None,
        server_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse a PDF file to Markdown format using VLM (Vision Language Model) backend.

        This method provides advanced PDF parsing capabilities using VLM technology,
        which is particularly effective for complex document layouts and mixed content.

        Args:
            file_path (str): Path to the PDF file
            save_parsed_content (bool): Whether to save parsed content
            save_middle_content (bool): Whether to save intermediate processing results
            start_page (int): First page to parse (0-based)
            end_page (int): Last page to parse (inclusive)
            server_url (str): Server URL for sglang-client backend.
                If provided, uses sglang-client backend; otherwise uses sglang-engine backend.

        Returns:
            Dict containing parsed content and metadata
        """
        output_path = str(self.output_dir / Path(file_path).stem)

        markdown_content = await pdf_parse_vlm_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            save_middle_content=save_middle_content,
            output_dir=str(self.output_dir),
            start_page=start_page,
            end_page=end_page,
            server_url=server_url,
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": output_path,
        }

    async def parse_docx(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse a DOCX file to Markdown format.

        Args:
            file_path (str): Path to the DOCX file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await docx_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_doc(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse a DOC file to Markdown format.

        This method converts DOC files to DOCX using LibreOffice and then parses them.

        Args:
            file_path (str): Path to the DOC file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await doc_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_pptx(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse a PPTX file to Markdown format.

        Args:
            file_path (str): Path to the PPTX file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await pptx_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_ppt(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse a PPT file to Markdown format.

        This method converts PPT files to PPTX using LibreOffice and then parses them.

        Args:
            file_path (str): Path to the PPT file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await ppt_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_xlsx(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse an XLSX file to Markdown format.

        Args:
            file_path (str): Path to the XLSX file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await xlsx_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_html(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse an HTML file to Markdown format.

        Args:
            file_path (str): Path to the HTML file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await html_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_url(
        self,
        url: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse a URL to Markdown format.

        Args:
            url (str): URL to parse
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await url_parse_main(
            url=url,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": url.replace("://", "_").replace("/", "_"),
            "output_path": str(
                self.output_dir / url.replace("://", "_").replace("/", "_")
            ),
        }

    async def parse_epub(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse an EPUB file to Markdown format.

        Args:
            file_path (str): Path to the EPUB file
            save_parsed_content (bool): Whether to save parsed content (images will be automatically extracted when True)

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await epub_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }

    async def parse_image(
        self,
        file_path: str,
        save_parsed_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Parse an image file to extract text using OCR.

        Args:
            file_path (str): Path to the image file
            save_parsed_content (bool): Whether to save parsed content

        Returns:
            Dict containing parsed content and metadata
        """
        markdown_content = await image_parse_main(
            resource_path=file_path,
            save_parsed_content=save_parsed_content,
            output_dir=str(self.output_dir),
        )

        return {
            "content": markdown_content,
            "file_name": Path(file_path).stem,
            "output_path": str(self.output_dir / Path(file_path).stem),
        }
