<img src="assets/image.png" alt="Markio Logo"  height="350" style="display:block;margin:auto;">

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
- **🎯 All-in-One Solution**: Parse PDF, Office (DOC/DOCX/PPT/PPTX/XLSX), HTML, EPUB, Images, and more in a unified platform
- **⚡ High Performance**: Async processing, GPU acceleration, and concurrent request handling
- **🔧 Flexible Integration**: CLI, Python SDK, and REST API for any workflow
- **🐳 Production Ready**: Docker support, health checks, and monitoring capabilities
- **🌐 Multi-Format Output**: Consistent Markdown output with metadata preservation

| Use Case         | Description                        | Best For                          |
|------------------|------------------------------------|-----------------------------------|
| API Integration  | Unified REST API for all formats   | Microservices, Web Apps          |
| CLI Automation   | Batch convert docs in one command  | CI/CD, Data Processing Pipelines |
| Web Preview      | Gradio UI for instant feedback     | Prototyping, User Testing         |
| SDK Integration  | Python library for custom apps     | Data Science, ML Workflows       |

---

## ⚡ Quick Start

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

# Install Python package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal

# Clone and install
git clone https://github.com/Tendo33/markio.git
cd markio
uv venv && source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
uv pip install -e .

# Start services
./start_services.sh  # or run separately:
# python markio/main.py          # API server
# python markio/web/gradio_frontend.py  # Web UI
```

---

## 🛠️ Usage Examples

### REST API

#### PDF Parsing with Advanced Options
```python
import httpx
import asyncio

async def parse_pdf():
    async with httpx.AsyncClient() as client:
        # Basic parsing
        files = {"file": open("document.pdf", "rb")}
        resp = await client.post("http://localhost:8000/v1/parse_pdf_file", files=files)
        result = resp.json()
        print(f"Status: {result['status_code']}")
        print(f"Content length: {len(result['parsed_content'])} chars")
        
        # Advanced parsing with options
        data = {
            "save_parsed_content": True,
            "output_dir": "./results",
            "parse_method": "auto",  # auto/ocr/txt
            "lang": "en",
            "start_page": 0,
            "end_page": 10
        }
        resp = await client.post(
            "http://localhost:8000/v1/parse_pdf_file", 
            files=files, 
            data=data
        )
        return resp.json()

# Run the function
result = asyncio.run(parse_pdf())
```

#### Batch Processing
```python
import os
import httpx
from pathlib import Path

def batch_convert_documents(directory: str, output_dir: str):
    """Convert all PDFs in a directory"""
    Path(output_dir).mkdir(exist_ok=True)
    
    with httpx.Client() as client:
        for pdf_file in Path(directory).glob("*.pdf"):
            files = {"file": open(pdf_file, "rb")}
            data = {"save_parsed_content": True, "output_dir": output_dir}
            
            response = client.post(
                "http://localhost:8000/v1/parse_pdf_file", 
                files=files, 
                data=data
            )
            
            if response.status_code == 200:
                print(f"✅ Converted: {pdf_file.name}")
            else:
                print(f"❌ Failed: {pdf_file.name}")

# Usage
batch_convert_documents("./input_pdfs", "./converted_md")
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

### CLI Examples

#### Basic Usage
```bash
# Simple PDF conversion
markio pdf document.pdf

# Save output with custom filename
markio pdf document.pdf -o my_document.md

# Batch convert multiple files
markio pdf *.pdf --save --output ./results/
```

#### Advanced CLI Options
```bash
# Convert with specific language and page range
markio pdf document.pdf \
  --lang en \
  --start-page 5 \
  --end-page 15 \
  --save \
  --output ./results/

# Convert Office documents
markio docx report.docx --save
markio pptx presentation.pptx --save --output ./slides/
markio xlsx data.xlsx --save

# Convert web content
markio url https://example.com --save
markio html page.html --save

# Convert images with OCR
markio image screenshot.png --save --lang en

# Convert EPUB to markdown
markio epub book.epub --save --output ./books/
```

#### CLI Configuration
```bash
# Check configuration
markio config

# Set default output directory
markio config set output_dir ~/Documents/markio_output

# Set default language
markio config set lang en

# Reset to defaults
markio config reset
```

### Python SDK Examples

#### Basic SDK Usage
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def basic_sdk_example():
    # Initialize SDK
    sdk = MarkioSDK(base_url="http://localhost:8000")
    
    # Parse a document
    result = await sdk.parse_document(
        file_path="document.pdf",
        save_parsed_content=True,
        output_dir="./results"
    )
    
    print(f"Content: {result['content'][:200]}...")
    print(f"Metadata: {result['metadata']}")
    
    return result

# Run
result = asyncio.run(basic_sdk_example())
```

#### Advanced SDK Features
```python
from markio.sdk.markio_sdk import MarkioSDK
from markio.sdk.schemas import ParseOptions

async def advanced_sdk_example():
    sdk = MarkioSDK()
    
    # Configure parsing options
    options = ParseOptions(
        parse_method="auto",
        language="en",
        start_page=0,
        end_page=None,
        save_parsed_content=True,
        output_dir="./results"
    )
    
    # Parse multiple documents concurrently
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    tasks = [sdk.parse_document(file_path=f, options=options) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ {files[i]} failed: {result}")
        else:
            print(f"✅ {files[i]}: {len(result['content'])} chars")
    
    return results

# Run
results = asyncio.run(advanced_sdk_example())
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

#### Environment Variables

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `LOG_LEVEL` | INFO | Log verbosity level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_DIR` | logs | Log file directory | `/var/log/markio` |
| `OUTPUT_DIR` | outputs | Parsed content output directory | `/data/outputs` |
| `PDF_PARSE_ENGINE` | pipeline | PDF parsing method | `pipeline`, `vlm-sglang-engine` |
| `MINERU_DEVICE_MODE` | auto | MinerU device selection | `cuda`, `cpu`, `mps` |
| `VLM_SERVER_URL` | - | VLM server endpoint | `http://localhost:30000` |
| `ENABLE_MCP` | false | Enable MCP server | `true`, `false` |
| `HOST` | 0.0.0.0 | Server bind address | `127.0.0.1` |
| `PORT` | 8000 | Server port | `8080` |

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

**VLM Engine**
```bash
# Requires external VLM server
PDF_PARSE_ENGINE=vlm-sglang-engine
VLM_SERVER_URL=http://localhost:30000
```

#### Performance Tuning

```bash
# Memory optimization
MINERU_DEVICE_MODE=cpu  # For systems without GPU

# Batch processing
PDF_PARSE_ENGINE=pipeline
MINERU_BATCH_SIZE=4

# Logging for debugging
LOG_LEVEL=DEBUG
LOG_DIR=./debug_logs
```

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
