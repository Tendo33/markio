<img src="assets/image.png" alt="Markio Logo"  height="350" style="display:block;margin:auto;">

> **High-Performance Document Conversion API Platform**  
> Parse, convert, and structure your documents with one command.

<div align="center">

### 🌍 Language / 语言

**English** | [中文](README_zh.md)

---

</div>

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Based%20on-MinerU-orange.svg)](https://github.com/opendatalab/MinerU)
[![docling](https://img.shields.io/badge/Based%20on-docling-purple.svg)](https://github.com/docling-project/docling)
[![pandoc](https://img.shields.io/badge/Based%20on-pandoc-green.svg)](https://pandoc.org)
[![LibreOffice](https://img.shields.io/badge/Based%20on-LibreOffice-blue.svg)](https://www.libreoffice.org)

---

## Why Markio?
- **Multi-format support**: PDF, Office, HTML, EPUB, Images, and more
- **High performance**: Async processing, GPU acceleration, concurrent requests
- **Flexible integration**: CLI, Python SDK, REST API for any workflow
- **Production ready**: Docker support, health checks, monitoring
- **Consistent output**: Markdown format with metadata preservation
- **Developer friendly**: Clean APIs, comprehensive documentation, type hints

| Use Case        | Description                     | Best For                         |
|------------------|----------------------------------|----------------------------------|
| API Integration  | Unified REST API for all formats | Microservices, Web Apps           |
| CLI Automation   | Batch convert docs in one command | CI/CD, Data Processing Pipelines  |
| Web Preview      | Gradio UI for instant feedback    | Prototyping, User Testing         |
| SDK Integration  | Python library for custom apps    | Data Science, ML Workflows       |
| Enterprise      | Scalable document processing      | Document Management Systems      |

---

## Quick Start

### Docker (Recommended)
```bash
# Clone and start services
git clone https://github.com/Tendo33/markio.git
cd markio
docker compose up -d

# Access services
# API Documentation: http://localhost:8000/docs
# Web Interface:    http://localhost:7860
# Health Check:     http://localhost:8000/health
```

### Local Installation
```bash
# System dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y libreoffice pandoc

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal

# Clone and install
git clone https://github.com/Tendo33/markio.git
cd markio
uv sync
uv pip install -e .

# Start services
export CUDA_VISIBLE_DEVICES=0
./start_services.sh  # or run separately:
# python markio/main.py          # API server
# python markio/web/gradio_frontend.py  # Web UI
```

---

## Usage

Markio provides three flexible usage methods to meet different scenario requirements:

### 🌐 REST API

Suitable for microservice integration and web application development. After starting the service, visit `http://localhost:8000/docs` to view complete API documentation.

**Quick Example**:
```python
import httpx
import asyncio

async def parse_pdf():
    async with httpx.AsyncClient() as client:
        files = {"file": open("document.pdf", "rb")}
        resp = await client.post("http://localhost:8000/v1/parse_pdf_file", files=files)
        result = resp.json()
        print(f"Parsed content: {result['parsed_content'][:200]}...")
        return result

asyncio.run(parse_pdf())
```

**Core API Endpoints**:

| File Format | Endpoint | Description |
|-------------|----------|-------------|
| PDF | `/v1/parse_pdf_file` | Parse PDF with OCR/VLM support |
| DOCX/DOC | `/v1/parse_docx_file`, `/v1/parse_doc_file` | Word document parsing |
| PPTX/PPT | `/v1/parse_pptx_file`, `/v1/parse_ppt_file` | PowerPoint parsing |
| XLSX | `/v1/parse_xlsx_file` | Excel spreadsheet parsing |
| HTML/URL | `/v1/parse_html_file`, `/v1/parse_url_file` | Web content parsing |
| Image | `/v1/parse_image_file` | OCR image recognition |

### ⌨️ CLI Command Line

Suitable for batch processing, automation scripts, and CI/CD integration.

**Quick Examples**:
```bash
# PDF conversion
markio pdf document.pdf --save

# Batch processing
markio pdf *.pdf --save --output ./results/

# Office documents
markio docx report.docx --save
```

📖 **Detailed Documentation**: [CLI Usage Guide](docs/cli_usage.md)

### 🐍 Python SDK

Suitable for custom application development and data processing workflows.

**Quick Example**:
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def main():
    sdk = MarkioSDK(output_dir="./parsed_docs")
    result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    print(f"Parsing completed: {result['file_name']}")

asyncio.run(main())
```

📖 **Detailed Documentation**: [SDK Usage Guide](docs/sdk_usage.md)

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

#### Environment Variables

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `LOG_LEVEL` | INFO | Log verbosity level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_DIR` | logs | Log file directory | `/var/log/markio` |
| `OUTPUT_DIR` | outputs | Parsed content output directory | `/data/outputs` |
| `PDF_PARSE_ENGINE` | pipeline | PDF parsing method | `pipeline`, `vlm-vllm-engine`, `vlm-vllm-client` |
| `MINERU_DEVICE_MODE` | cuda | MinerU device selection | `cuda`, `cpu`, `mps` |
| `VLM_SERVER_URL` | - | VLM server endpoint | `http://localhost:30000` |
| `VLM_GPU_MEMORY_UTILIZATION` | 0.9 | vLLM GPU memory utilization | `0.0-1.0` |
| `ENABLE_MCP` | false | Enable MCP server | `true`, `false` |
| `HOST` | 0.0.0.0 | Server bind address | `127.0.0.1` |
| `PORT` | 8000 | Server port | `8080` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU minimum batch inference size | `128`, `256`, `512` |
| `MINERU_MODEL_SOURCE` | local | MinerU model source | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | MinerU virtual VRAM size in MB | `8192`, `16384` |

#### Configuration Files

Create a `.env` file in the project root:

```bash
# Basic configuration
LOG_LEVEL=INFO
OUTPUT_DIR=./parsed_documents
PDF_PARSE_ENGINE=pipeline

# GPU configuration (if available)
MINERU_DEVICE_MODE=cuda

# VLM configuration (if using VLM engine)
VLM_SERVER_URL=http://localhost:30000

# Server configuration
HOST=0.0.0.0
PORT=8000
```

#### PDF Engine Configuration

**Pipeline Engine (Default)**
```bash
# Uses MinerU with automatic OCR/VLM selection
PDF_PARSE_ENGINE=pipeline
```

**VLM Engine (vLLM)**
```bash
# Use vLLM engine (MinerU 2.5.0+)
PDF_PARSE_ENGINE=vlm-vllm-engine

# Or use vLLM client mode (requires external vLLM service)
PDF_PARSE_ENGINE=vlm-vllm-client
VLM_SERVER_URL=http://localhost:30000
```

#### Complete Configuration Reference

##### Core Settings
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `LOG_LEVEL` | INFO | Logging verbosity | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_DIR` | logs | Directory for log files | Any valid path |
| `OUTPUT_DIR` | outputs | Default output directory | Any valid path |
| `HOST` | 0.0.0.0 | Server bind address | IP address or hostname |
| `PORT` | 8000 | Server port | 1-65535 |

##### PDF Processing Configuration
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `PDF_PARSE_ENGINE` | pipeline | PDF parsing method | `pipeline`, `vlm-vllm-engine`, `vlm-vllm-client` |
| `MINERU_DEVICE_MODE` | cuda | MinerU device selection | `cuda`, `cpu`, `mps` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU batch size | 1-1024 |
| `MINERU_MODEL_SOURCE` | local | MinerU model source | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | Virtual VRAM size (MB) | 1024-65536 |

##### VLM Configuration
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `VLM_SERVER_URL` | - | VLM server endpoint | Valid URL |
| `VLM_GPU_MEMORY_UTILIZATION` | 0.9 | vLLM GPU memory utilization | 0.1-1.0 |

##### Advanced Settings
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `ENABLE_MCP` | false | Enable MCP server | `true`, `false` |

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

#### Community Support
- [GitHub Issues](https://github.com/Tendo33/markio/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions) - General questions and help
- [Wiki Documentation](https://github.com/Tendo33/markio/wiki) - Detailed guides and tutorials

#### Reporting Issues
When reporting issues, please include:
1. Operating system and version
2. Python version (`python --version`)
3. Markio version (`pip show markio`)
4. Error messages and stack traces
5. Steps to reproduce the issue
6. Sample files (if applicable and non-confidential)

</details>

---

## 🤝 Community & Support

- [Contributing Guide](CONTRIBUTING.md)
- [Issues](https://github.com/Tendo33/markio/issues)
- [Discussions](https://github.com/Tendo33/markio/discussions)
- [Wiki/Docs](https://github.com/Tendo33/markio/wiki)
- [Roadmap/Changelog](#)
- [FAQ](#)

### Documentation Links

- **CLI Usage Guide**: [docs/cli_usage.md](docs/cli_usage.md)
- **SDK Usage Guide**: [docs/sdk_usage.md](docs/sdk_usage.md)

---

**Made with ❤️ by the Markio Team**
