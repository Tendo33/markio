<img src="assets/image.png" alt="Markio Logo"  height="250" style="display:block;margin:auto;">

> **High-Performance Document Conversion API Platform**  
> *Parse, convert, and structure your documents with one command.*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Based%20on-MinerU-orange.svg)](https://github.com/opendatalab/MinerU)
[![docling](https://img.shields.io/badge/Based%20on-docling-purple.svg)](https://github.com/docling-project/docling)
[![pandoc](https://img.shields.io/badge/Based%20on-pandoc-green.svg)](https://pandoc.org)
[![LibreOffice](https://img.shields.io/badge/Based%20on-LibreOffice-blue.svg)](https://www.libreoffice.org)

---

## 🚀 Why Markio?
- **All-in-One**: Parse PDF, Office, HTML, EPUB, Images, and more.
- **Intelligent Engine**: Auto-selects best parsing (OCR/VLM/Text).
- **Batch & Real-time**: Supports batch conversion and web preview.
- **CLI, SDK, API**: Flexible integration for any workflow.
- **GPU & Docker Ready**: High performance, easy deployment.

| Use Case         | Description                        |
|------------------|------------------------------------|
| API Integration  | Unified REST API for all formats   |
| CLI Automation   | Batch convert docs in one command  |
| Web Preview      | Gradio UI for instant feedback     |
| ...              | ...                                |

---

## ⚡ Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/Tendo33/markio.git
cd markio
docker compose up -d
# Access: http://localhost:8000/docs  (API)
#         http://localhost:7860       (Web UI)
```

### Local Install
```bash
# System dependencies
sudo apt install libreoffice pandoc
# Python 3.11+ & uv
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/Tendo33/markio.git
cd markio
uv venv && uv pip install -e .
```

---

## 🛠️ Typical Usage

### REST API Example
```python
import httpx
resp = httpx.post("http://localhost:8000/v1/parse_pdf_file", files={"file": open("test.pdf", "rb")})
print(resp.json())
```

#### Request Parameters
| Name                | Type         | Required | Description                                      |
|---------------------|--------------|----------|--------------------------------------------------|
| file                | file         | Yes      | The PDF file to be parsed                        |
| save_parsed_content | bool         | No       | Whether to save parsed content (default: false)  |
| output_dir          | str          | No       | Directory to save parsed content (default: outputs) |
| parse_method        | str          | No       | Parsing method (auto/ocr/txt, default: auto)     |
| lang                | str          | No       | Document language (ch/en/korean/japan..., default: ch) |
| start_page          | int          | No       | Start page (default: 0)                          |
| end_page            | int/None     | No       | End page (default: None, parse to last page)     |

#### Response Format
Example JSON:
```json
{
  "parsed_content": "# Markdown content ...",
  "status_code": 200
}
```

### CLI Example
```bash
markio pdf test.pdf -o result.md
markio docx test.docx --save --output result.md
```

### Python SDK Example
```python
from markio.sdk.markio_sdk import MarkioSDK
sdk = MarkioSDK()
result = await sdk.parse_document(file_path="test.pdf", save_parsed_content=True)
print(result["content"])
```

---

<details>
<summary>📄 Supported Formats & Engines</summary>

| Format   | Engine(s)         | Features                |
|----------|-------------------|-------------------------|
| PDF      | MinerU, VLM, OCR  | Layout, OCR, Table, ... |
| DOCX     | docling           | ...                     |
| PPTX     | docling           | ...                     |
| DOC      | LibreOffice+docling | ...                   |
| PPT      | LibreOffice+docling | ...                   |
| XLSX     | docling           | ...                     |
| HTML     | docling           | ...                     |
| URL      | jina              | ...                     |
| EPUB     | pandoc            | ...                     |
| Images   | MinerU            | OCR                     |

</details>

<details>
<summary>⚙️ Configuration & Project Structure</summary>

### Configuration Guide

| Parameter           | Default   | Description                                 |
|---------------------|-----------|---------------------------------------------|
| `log_level`         | INFO      | Log level (DEBUG/INFO/WARNING/ERROR)        |
| `log_dir`           | logs      | Log output directory                        |
| `output_dir`        | outputs   | Output directory for parsed content         |
| `pdf_parse_engine`  | pipeline  | PDF parsing engine (pipeline/vlm-sglang)    |
| `enable_mcp`        | false     | Enable MCP server integration               |

### Project Structure

```
markio/
├── markio/           # Main package
│   ├── main.py       # FastAPI application entry point
│   ├── routers/      # API route definitions
│   ├── parsers/      # Document parsing modules
│   ├── schemas/      # Data models and validation
│   ├── utils/        # Utility functions
│   ├── web/          # Web interface (Gradio)
│   ├── sdk/          # Python SDK
│   └── mcps/         # MCP server integration
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── tests/            # Test files
├── Dockerfile        # Docker configuration
├── compose.yaml      # Docker Compose configuration
├── pyproject.toml    # Project configuration
```

### Environment Variables

| Variable             | Default   | Description                |
|----------------------|-----------|----------------------------|
| `LOG_LEVEL`          | INFO      | Log level                  |
| `LOG_DIR`            | logs      | Log directory              |
| `OUTPUT_DIR`         | outputs   | Output directory           |
| `PDF_PARSE_ENGINE`   | pipeline  | PDF parsing engine         |
| `ENABLE_MCP`         | false     | Enable MCP integration     |
| `HOST`               | 0.0.0.0   | Server listen address      |
| `PORT`               | 8000      | Server port                |

</details>

---

## 🤝 Community & Support

- [Contributing Guide](CONTRIBUTING.md)
- [Issues](https://github.com/Tendo33/markio/issues)
- [Discussions](https://github.com/Tendo33/markio/discussions)
- [Wiki/Docs](https://github.com/Tendo33/markio/wiki)
- [Roadmap/Changelog](#)
- [FAQ](#)

---

**Made with ❤️ by the Markio Team**

---

> 中文文档：[README_zh.md](README_zh.md)
