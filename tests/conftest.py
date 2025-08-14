"""
Pytest configuration file for markio API tests
"""

from pathlib import Path

import httpx
import pytest

# Test configuration
BASE_URL = "http://0.0.0.0:8000"
API_PREFIX = "/v1"


@pytest.fixture
def client():
    """HTTP client for testing API endpoints"""
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        yield client


@pytest.fixture
def test_files_dir():
    """Path to test documents directory"""
    return Path(__file__).parent / "test_docs"


@pytest.fixture
def test_files():
    """Mapping of file types to test files"""
    return {
        "pdf": "test_pdf1.pdf",
        "doc": "test_doc.doc",
        "docx": "test_docx.docx",
        "ppt": "test_ppt.ppt",
        "pptx": "test_pptx.pptx",
        "xlsx": "test_xlsx.xlsx",
        "html": "test_html.html",
        "epub": "test_epub.epub",
        "image": "test_pdf1.pdf",  # Using PDF as image test for now
    }


@pytest.fixture
def api_endpoints():
    """Mapping of file types to API endpoints"""
    return {
        "pdf": f"{API_PREFIX}/parse_pdf_file",
        "doc": f"{API_PREFIX}/parse_doc_file",
        "docx": f"{API_PREFIX}/parse_docx_file",
        "ppt": f"{API_PREFIX}/parse_ppt_file",
        "pptx": f"{API_PREFIX}/parse_pptx_file",
        "xlsx": f"{API_PREFIX}/parse_xlsx_file",
        "html": f"{API_PREFIX}/parse_html_file",
        "epub": f"{API_PREFIX}/parse_epub_file",
        "image": f"{API_PREFIX}/parse_image_file",
    }


@pytest.fixture
def parser_config():
    """Default parser configuration"""
    return {"save_parsed_content": False, "output_dir": None}
