<img src="assets/image.png" alt="Markio Logo"  height="350" style="display:block;margin:auto;">

> **High-Performance Document Conversion API Platform**  
> Parse, convert, and structure your documents with one command.

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

## Usage Examples

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
| save_middle_content | bool         | No       | Save intermediate processing files (default: false) |
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

### Complete API Endpoints Reference

| File Format | Endpoint | Method | Description |
|-------------|----------|--------|-------------|
| PDF | `/v1/parse_pdf_file` | POST | Parse PDF files with OCR/VLM support |
| PDF VLM | `/v1/parse_pdf_vlm_file` | POST | Parse PDF using Vision Language Model |
| DOCX | `/v1/parse_docx_file` | POST | Parse DOCX (Word) files |
| DOC | `/v1/parse_doc_file` | POST | Parse legacy DOC files (auto-converts) |
| PPTX | `/v1/parse_pptx_file` | POST | Parse PPTX (PowerPoint) files |
| PPT | `/v1/parse_ppt_file` | POST | Parse legacy PPT files (auto-converts) |
| XLSX | `/v1/parse_xlsx_file` | POST | Parse XLSX (Excel) files |
| HTML | `/v1/parse_html_file` | POST | Parse HTML files |
| URL | `/v1/parse_url_file` | POST | Parse web pages from URL |
| EPUB | `/v1/parse_epub_file` | POST | Parse EPUB ebook files |
| Image | `/v1/parse_image_file` | POST | Parse images with OCR |

#### Universal Request Parameters
All endpoints accept these common parameters:
- `file` (UploadFile): The document file to parse
- `save_parsed_content` (bool): Save parsed content to disk
- `save_middle_content` (bool): Save intermediate processing files
- `output_dir` (str): Custom output directory path

#### PDF-Specific Parameters
- `parse_method` (str): `auto`, `ocr`, or `txt`
- `lang` (str): Document language code
- `start_page` (int): Starting page number (0-based)
- `end_page` (int): Ending page number (inclusive)

#### VLM-Specific Parameters
- `server_url` (str): VLM server endpoint for processing

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

# PDF with VLM engine (Vision Language Model)
markio pdf-vlm document.pdf --save --server http://localhost:30000

# Convert Office documents
markio docx report.docx --save
markio pptx presentation.pptx --save --output ./slides/
markio xlsx data.xlsx --save

# Convert legacy Office formats (auto-converts to modern formats)
markio doc legacy.doc --save
markio ppt legacy.ppt --save --output ./presentations/

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

#### CLI Documentation
For detailed CLI usage, commands, and examples, see the [CLI Usage Guide](docs/cli_usage.md)

### Python SDK Examples

#### Basic SDK Usage
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def basic_sdk_example():
    # Initialize SDK
    sdk = MarkioSDK(output_dir="./parsed_docs")
    
    # Parse a PDF document
    result = await sdk.parse_pdf(
        file_path="document.pdf",
        parse_method="auto",
        save_parsed_content=True,
        start_page=0,
        end_page=10
    )
    
    print(f"Content: {result['content'][:200]}...")
    print(f"File name: {result['file_name']}")
    print(f"Output path: {result['output_path']}")
    
    return result

# Run
result = asyncio.run(basic_sdk_example())
```

#### SDK Documentation
For comprehensive SDK documentation, including all methods, examples, and advanced patterns, see the [SDK Usage Guide](docs/sdk_usage.md)

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
| `MINERU_DEVICE_MODE` | cuda | MinerU device selection | `cuda`, `cpu`, `mps` |
| `VLM_SERVER_URL` | - | VLM server endpoint | `http://localhost:30000` |
| `ENABLE_MCP` | false | Enable MCP server | `true`, `false` |
| `HOST` | 0.0.0.0 | Server bind address | `127.0.0.1` |
| `PORT` | 8000 | Server port | `8080` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU minimum batch inference size | `128`, `256`, `512` |
| `MINERU_MODEL_SOURCE` | local | MinerU model source | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | MinerU virtual VRAM size in MB | `8192`, `16384` |
| `VLM_MEM_FRACTION_STATIC` | 0.5 | VLM memory fraction static | `0.3`, `0.5`, `0.7` |

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
| `PDF_PARSE_ENGINE` | pipeline | PDF parsing method | `pipeline`, `vlm-sglang-engine` |
| `MINERU_DEVICE_MODE` | cuda | MinerU device selection | `cuda`, `cpu`, `mps` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU batch size | 1-1024 |
| `MINERU_MODEL_SOURCE` | local | MinerU model source | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | Virtual VRAM size (MB) | 1024-65536 |

##### VLM Configuration
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `VLM_SERVER_URL` | - | VLM server endpoint | Valid URL |
| `VLM_MEM_FRACTION_STATIC` | 0.5 | VLM memory fraction | 0.1-0.9 |

##### Advanced Settings
| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `ENABLE_MCP` | false | Enable MCP server | `true`, `false` |

#### Performance Tuning Profiles

##### High-Performance (GPU)
```bash
# Maximum performance with GPU
MINERU_DEVICE_MODE=cuda
MINERU_MIN_BATCH_INFERENCE_SIZE=512
MINERU_VIRTUAL_VRAM_SIZE=16384
VLM_MEM_FRACTION_STATIC=0.7
PDF_PARSE_ENGINE=pipeline
```

##### Balanced (Mixed GPU/CPU)
```bash
# Balanced performance and memory usage
MINERU_DEVICE_MODE=cuda
MINERU_MIN_BATCH_INFERENCE_SIZE=256
MINERU_VIRTUAL_VRAM_SIZE=8192
VLM_MEM_FRACTION_STATIC=0.5
```

##### Memory-Constrained (CPU)
```bash
# Conservative memory usage
MINERU_DEVICE_MODE=cpu
MINERU_MIN_BATCH_INFERENCE_SIZE=128
MINERU_VIRTUAL_VRAM_SIZE=4096
VLM_MEM_FRACTION_STATIC=0.3
```

##### Development/Debugging
```bash
# Detailed logging for development
LOG_LEVEL=DEBUG
LOG_DIR=./debug_logs
MINERU_MIN_BATCH_INFERENCE_SIZE=64  # Smaller batches for debugging
```

#### Environment-Specific Configurations

##### Development (.env.development)
```bash
# Development environment
LOG_LEVEL=DEBUG
OUTPUT_DIR=./dev_outputs
PDF_PARSE_ENGINE=pipeline
MINERU_DEVICE_MODE=cpu  # Use CPU for development to save GPU resources
MINERU_MIN_BATCH_INFERENCE_SIZE=64
LOG_DIR=./dev_logs
```

##### Production (.env.production)
```bash
# Production environment
LOG_LEVEL=INFO
OUTPUT_DIR=/var/data/markio_outputs
PDF_PARSE_ENGINE=pipeline
MINERU_DEVICE_MODE=cuda
MINERU_MIN_BATCH_INFERENCE_SIZE=512
MINERU_VIRTUAL_VRAM_SIZE=16384
LOG_DIR=/var/log/markio
HOST=0.0.0.0
PORT=8000
```

##### Testing (.env.test)
```bash
# Testing environment
LOG_LEVEL=WARNING
OUTPUT_DIR=./test_outputs
PDF_PARSE_ENGINE=pipeline
MINERU_DEVICE_MODE=cpu
MINERU_MIN_BATCH_INFERENCE_SIZE=32
LOG_DIR=./test_logs
```

#### Configuration Validation

To validate your configuration:
```bash
# Check if environment variables are loaded
python -c "
from markio.settings import settings
print('Output directory:', settings.output_dir)
print('Log level:', settings.log_level)
print('PDF engine:', settings.pdf_parse_engine)
print('Device mode:', settings.mineru_device_mode)
"

# Test configuration with a sample file
markio pdf test.pdf -s -o ./config_test/
```

#### Configuration Best Practices

1. **Use .env files for environment-specific settings**
2. **Never commit sensitive information to version control**
3. **Use appropriate memory settings for your hardware**
4. **Monitor logs for configuration-related warnings**
5. **Test configuration changes in development first**

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

## 🔧 Troubleshooting & FAQ

### Common Issues

#### Installation Problems
**Issue**: `libreoffice` or `pandoc` not found
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y libreoffice pandoc

# macOS
brew install libreoffice pandoc

# Windows
# Download from official websites and add to PATH
```

**Issue**: Python dependencies fail to install
```bash
# Use uv instead of pip
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e .
```

#### Service Startup Issues
**Issue**: Service fails to start on port 8000
```bash
# Check if port is available
netstat -tulpn | grep :8000

# Use different port
export PORT=8080
python markio/main.py
```

**Issue**: GPU not detected for MinerU
```bash
# Check GPU availability
nvidia-smi

# Force CPU mode
export MINERU_DEVICE_MODE=cpu
python markio/main.py
```

#### PDF Processing Issues
**Issue**: PDF parsing fails with memory errors
```bash
# Reduce batch size
export MINERU_MIN_BATCH_INFERENCE_SIZE=128
export MINERU_VIRTUAL_VRAM_SIZE=4096

# Use CPU mode
export MINERU_DEVICE_MODE=cpu
```

**Issue**: VLM engine connection fails
```bash
# Check VLM server status
curl http://localhost:30000/health

# Verify server URL
export VLM_SERVER_URL=http://localhost:30000
```

#### Performance Issues
**Issue**: Slow processing times
```bash
# Enable GPU acceleration
export MINERU_DEVICE_MODE=cuda

# Increase batch size for better throughput
export MINERU_MIN_BATCH_INFERENCE_SIZE=512

# Use pipeline engine for better performance
export PDF_PARSE_ENGINE=pipeline
```

**Issue**: High memory usage
```bash
# Reduce memory allocation
export VLM_MEM_FRACTION_STATIC=0.3
export MINERU_VIRTUAL_VRAM_SIZE=4096

# Process files sequentially instead of in parallel
```

### API Integration Issues

#### File Upload Problems
**Issue**: Large file uploads fail
```bash
# Check file size limits
# FastAPI default: ~100MB, can be increased in application settings

# Process large files in chunks
# Use CLI for very large files
markio pdf large_file.pdf --save --output ./results/
```

**Issue**: Unsupported file formats
```bash
# Convert legacy formats first
# DOC → DOCX, PPT → PPTX using LibreOffice
# Or use markio's auto-conversion:
markio doc legacy.doc --save
```

### CLI Issues

#### Command Not Found
**Issue**: `markio` command not available
```bash
# Check installation
pip list | grep markio

# Reinstall in development mode
uv pip install -e .

# Add to PATH if needed
export PATH=$PATH:/path/to/markio
```

#### Configuration Issues
**Issue**: Environment variables not loading
```bash
# Create .env file in project root
echo "OUTPUT_DIR=./my_outputs" > .env
echo "LOG_LEVEL=DEBUG" >> .env

# Verify variables are loaded
python -c "from markio.settings import settings; print(settings.output_dir)"
```

### Performance Optimization

#### GPU Acceleration
```bash
# Enable GPU for MinerU
export MINERU_DEVICE_MODE=cuda
export MINERU_VIRTUAL_VRAM_SIZE=16384  # 16GB

# Optimize VLM memory usage
export VLM_MEM_FRACTION_STATIC=0.7
```

#### Batch Processing
```bash
# Process multiple files efficiently
find ./input_dir -name "*.pdf" -exec markio pdf {} --save --output ./output_dir/ \;

# Use parallel processing for large batches
parallel markio pdf {} --save --output ./output_dir/ ::: *.pdf
```

#### Memory Management
```bash
# Monitor memory usage
htop or glances

# Adjust based on available memory
export MINERU_VIRTUAL_VRAM_SIZE=8192  # 8GB for systems with 16GB RAM
export VLM_MEM_FRACTION_STATIC=0.3   # Conservative memory usage
```

### Getting Help

#### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_DIR=./debug_logs

# Check service health
curl http://localhost:8000/health

# View logs
tail -f logs/markio.log
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

---

## 🤝 Community & Support

- [Contributing Guide](CONTRIBUTING.md)
- [Issues](https://github.com/Tendo33/markio/issues)
- [Discussions](https://github.com/Tendo33/markio/discussions)
- [Wiki/Docs](https://github.com/Tendo33/markio/wiki)
- [Roadmap/Changelog](#)
- [FAQ](#troubleshooting--faq)

### Documentation Links
- **Main Documentation**: [README.md](README.md)
- **Chinese Documentation**: [README_zh.md](README_zh.md)
- **CLI Usage Guide**: [docs/cli_usage.md](docs/cli_usage.md)
- **Chinese CLI Guide**: [docs/cli_usage_zh.md](docs/cli_usage_zh.md)
- **SDK Usage Guide**: [docs/sdk_usage.md](docs/sdk_usage.md)
- **Chinese SDK Guide**: [docs/sdk_usage_zh.md](docs/sdk_usage_zh.md)

---

**Made with ❤️ by the Markio Team**
