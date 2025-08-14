# 🚀 Markio

> Powerful Document Conversion Service - High-quality document parsing API based on MinerU, docling, pandoc and LibreOffice

TODO：添加file path or url

中文文档：[README_zh.md](docs/README_zh.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![MinerU](https://img.shields.io/badge/Based%20on-MinerU-orange.svg)](https://github.com/opendatalab/MinerU)
[![docling](https://img.shields.io/badge/Based%20on-docling-purple.svg)](https://github.com/docling-project/docling)
[![pandoc](https://img.shields.io/badge/Based%20on-pandoc-green.svg)](https://pandoc.org)
[![LibreOffice](https://img.shields.io/badge/Based%20on-LibreOffice-blue.svg)](https://www.libreoffice.org)

Markio is a high-performance document conversion service based on FastAPI, **built on [MinerU](https://github.com/opendatalab/MinerU), [docling](https://github.com/docling-project/docling), [pandoc](https://pandoc.org) and [LibreOffice](https://www.libreoffice.org)**, providing a unified API interface to convert various document formats to structured Markdown. Supports REST API, CLI tools, SDK and **MCP integration (TODO: Under Development)** with GPU acceleration capabilities.

## 🏗️ Technical Architecture

### Core Dependencies
- **[MinerU](https://github.com/opendatalab/MinerU)**: High-quality PDF document parsing engine with OCR, VLM models and layout analysis
- **[docling](https://github.com/docling-project/docling)**: Multi-format document parsing library supporting Office documents, HTML and other formats
- **[pandoc](https://pandoc.org)**: Universal document conversion tool for EPUB and other formats
- **[LibreOffice](https://www.libreoffice.org)**: Open-source office suite for converting old DOC/PPT formats
- **FastAPI**: High-performance web framework providing REST API and automatic documentation generation
- **Gradio**: Provides web interface for real-time preview of conversion results

## ✨ Core Features

### 📄 Supported Formats
| Format | Support | Parser Engine | Description |
|--------|---------|---------------|-------------|
| **PDF** | ✅ | MinerU | OCR, VLM, text extraction, layout analysis |
| **DOC/DOCX** | ✅ | docling + LibreOffice | Microsoft Word documents |
| **PPT/PPTX** | ✅ | docling + LibreOffice | Microsoft PowerPoint presentations |
| **XLSX** | ✅ | docling | Microsoft Excel spreadsheets |
| **HTML** | ✅ | docling | Web files and content |
| **URL** | ✅ | jina | Web scraping and parsing |
| **EPUB** | ✅ | pandoc | E-book format |
| **Images** | ✅ | MinerU | OCR text extraction |

### 🔄 Conversion Pipeline
- **PDF**: MinerU → Direct parsing to Markdown
- **DOCX/PPTX/XLSX**: docling → Direct parsing to Markdown  
- **DOC/PPT**: LibreOffice → Convert to DOCX/PPTX → docling → Markdown
- **EPUB**: pandoc → Direct conversion to Markdown
- **HTML/URL**: docling → Direct parsing to Markdown
- **Images**: MinerU → OCR text extraction to Markdown

### 🚀 Advanced Features
- **Intelligent Parsing**: Automatically select the best parsing method (OCR/VLM/text extraction)
- **Layout Preservation**: Maintain original document layout and structure
- **Table Recognition**: Intelligent recognition and conversion of table content
- **Formula Processing**: Support for mathematical formula recognition and conversion
- **Multi-language Support**: Support for Chinese, English and other languages
- **Batch Processing**: Support for batch document conversion
- **Real-time Preview**: Provide web interface for real-time preview of conversion results
- **Format Compatibility**: Support automatic conversion of old and new Office formats

## 🧪 Testing

### Quick Test Run
```bash
# Run the interactive test suite
python tests/run_tests.py

# Or run tests directly
pytest tests/ -v
```

### Test Coverage
```bash
# Generate coverage report
pytest tests/ --cov=markio --cov-report=html

# View coverage report
open htmlcov/index.html
```

For detailed testing information, see [tests/README.md](tests/README.md).

## 🚀 Quick Start

### Method 1: Docker (Recommended)

```bash
# Clone the project
git clone https://github.com/Tendo33/markio.git
cd markio
docker build -t markio:latest .
# Start the service
docker-compose up -d
```

```
Access: http://localhost:8000/docs

Gradio frontend access: http://localhost:7860
```

### Method 2: Local Installation

```bash
# 1. Install system dependencies
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libreoffice pandoc

# CentOS/RHEL
sudo yum install -y libreoffice pandoc

# macOS
brew install libreoffice pandoc

# 2. Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone and install
git clone https://github.com/Tendo33/markio.git
cd markio
```

## 📚 Documentation

### API Documentation
- [Markio API Documentation](http://localhost:8000/docs) - Complete API reference and examples
- [Markio CLI Usage Guide (English)](docs/cli_usage.md) - Complete command reference and examples
- [Markio CLI 使用指南 (中文)](docs/cli_usage_zh.md) - 完整命令参考和示例

### Configuration
- [Markio API core configuration parameters](#markio-api-core-configuration-parameters)
- [Environment Variables](#environment-variables)
- [Docker Configuration](#docker-configuration)

## 🔧 Configuration

### Markio API core configuration parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `log_level` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `log_dir` | `logs` | Log directory |
| `output_dir` | `outputs` | Output directory for parsed content |
| `pdf_parse_engine` | `pipeline` | PDF parsing engine (pipeline, vlm-sglang-engine) |
| `enable_mcp` | `false` | Enable MCP server integration |

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Output
OUTPUT_DIR=outputs

# PDF Parsing Engine
PDF_PARSE_ENGINE=pipeline  # or vlm-sglang-engine

# MCP Integration
ENABLE_MCP=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Docker Configuration

```yaml
version: '3.8'
services:
  markio:
    build: .
    container_name: markio
    ports:
      - "8000:8000"
      - "7860:7860"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
```

## 🏗️ Project Structure

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
│   └── markio_mcp/  # MCP server integration
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── tests/            # Test files
├── Dockerfile        # Docker configuration
├── compose.yaml      # Docker Compose configuration
└── pyproject.toml    # Project configuration
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MinerU](https://github.com/opendatalab/MinerU) - High-quality PDF parsing engine
- [docling](https://github.com/docling-project/docling) - Multi-format document parsing
- [pandoc](https://pandoc.org) - Universal document converter
- [LibreOffice](https://www.libreoffice.org) - Open-source office suite
- [FastAPI](https://fastapi.tiangolo.com) - Modern web framework
- [Gradio](https://gradio.app) - Web interface framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Tendo33/markio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- **Documentation**: [Project Wiki](https://github.com/Tendo33/markio/wiki)

---

**Made with ❤️ by the Markio Team**
