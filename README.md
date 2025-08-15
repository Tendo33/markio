# <img src="docs/assets/logo.png" alt="Markio Logo" height="48" style="vertical-align:middle;"> Markio

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

![Demo Screenshot/Animation](docs/assets/demo.gif)

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

- [Configuration Guide](docs/README_zh.md#配置)
- [Project Structure](docs/README_zh.md#项目结构)
- [Environment Variables](docs/README_zh.md#环境变量)
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

> 中文文档：[README_zh.md](docs/README_zh.md)
