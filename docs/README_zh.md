# 🚀 Markio

> 强大的文档转换服务 - 基于 MinerU、docling、pandoc 和 LibreOffice 的高质量文档解析 API

TODO：添加file path or url

English documentation: [README.md](../README.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![MinerU](https://img.shields.io/badge/Based%20on-MinerU-orange.svg)](https://github.com/opendatalab/MinerU)
[![docling](https://img.shields.io/badge/Based%20on-docling-purple.svg)](https://github.com/docling-project/docling)
[![pandoc](https://img.shields.io/badge/Based%20on-pandoc-green.svg)](https://pandoc.org)
[![LibreOffice](https://img.shields.io/badge/Based%20on-LibreOffice-blue.svg)](https://www.libreoffice.org)

Markio 是一个基于 FastAPI 的高性能文档转换服务，**基于 [MinerU](https://github.com/opendatalab/MinerU)、[docling](https://github.com/docling-project/docling)、[pandoc](https://pandoc.org) 和 [LibreOffice](https://www.libreoffice.org)**，提供统一的 API 接口将各种文档格式转换为结构化 Markdown。支持 REST API、CLI 工具、SDK 和 **MCP 集成（开发中）**，具备 GPU 加速能力。

## 🏗️ 技术架构

### 核心依赖
- **[MinerU](https://github.com/opendatalab/MinerU)**: 高质量 PDF 文档解析引擎，支持 OCR、VLM 模型和布局分析
- **[docling](https://github.com/docling-project/docling)**: 多格式文档解析库，支持 Office 文档、HTML 等格式
- **[pandoc](https://pandoc.org)**: 通用文档转换工具，支持 EPUB 等格式
- **[LibreOffice](https://www.libreoffice.org)**: 开源办公套件，用于转换旧版 DOC/PPT 格式
- **FastAPI**: 高性能 Web 框架，提供 REST API 和自动文档生成
- **Gradio**: 提供 Web 界面，实时预览转换结果

## ✨ 核心功能

### 📄 支持的格式
| 格式 | 支持 | 解析引擎 | 描述 |
|------|------|----------|------|
| **PDF** | ✅ | MinerU | OCR、VLM、文本提取、布局分析 |
| **DOC/DOCX** | ✅ | docling + LibreOffice | Microsoft Word 文档 |
| **PPT/PPTX** | ✅ | docling + LibreOffice | Microsoft PowerPoint 演示文稿 |
| **XLSX** | ✅ | docling | Microsoft Excel 电子表格 |
| **HTML** | ✅ | docling | Web 文件和内容 |
| **URL** | ✅ | jina | Web 抓取和解析 |
| **EPUB** | ✅ | pandoc | 电子书格式 |
| **图片** | ✅ | MinerU | OCR 文本提取 |

### 🔄 转换流程
- **PDF**: MinerU → 直接解析为 Markdown
- **DOCX/PPTX/XLSX**: docling → 直接解析为 Markdown  
- **DOC/PPT**: LibreOffice → 转换为 DOCX/PPTX → docling → Markdown
- **EPUB**: pandoc → 直接转换为 Markdown
- **HTML/URL**: docling → 直接解析为 Markdown
- **图片**: MinerU → OCR 文本提取为 Markdown

### 🚀 高级功能
- **智能解析**: 自动选择最佳解析方法（OCR/VLM/文本提取）
- **布局保持**: 保持原始文档布局和结构
- **表格识别**: 智能识别和转换表格内容
- **公式处理**: 支持数学公式识别和转换
- **多语言支持**: 支持中文、英文等语言
- **批量处理**: 支持批量文档转换
- **实时预览**: 提供 Web 界面实时预览转换结果
- **格式兼容**: 支持新旧 Office 格式自动转换

## 🚀 快速开始

### 方法一：Docker（推荐）

```bash
# 克隆项目
git clone https://github.com/Tendo33/markio.git
cd markio
docker build -t markio:latest .
# 启动服务
docker-compose up -d
```

```
访问: http://localhost:8000/docs

Gradio 前端访问: http://localhost:7860
```

### 方法二：本地安装

```bash
# 1. 安装系统依赖
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libreoffice pandoc

# CentOS/RHEL
sudo yum install -y libreoffice pandoc

# macOS
brew install libreoffice pandoc

# 2. 安装 uv（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 克隆并安装
git clone https://github.com/Tendo33/markio.git
cd markio
```

## 📚 文档

### API 文档
- [Markio API 文档](http://localhost:8000/docs) - 完整 API 参考和示例
- [Markio CLI 使用指南（中文）](cli_usage_zh.md) - 完整命令参考和示例
- [Markio CLI Usage Guide (English)](cli_usage.md) - Complete command reference and examples

### 配置
- [Markio API 核心配置参数](#markio-api-核心配置参数)
- [环境变量](#环境变量)
- [Docker 配置](#docker-配置)

## 🔧 配置

### Markio API 核心配置参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `log_level` | `INFO` | 日志级别（DEBUG、INFO、WARNING、ERROR） |
| `log_dir` | `logs` | 日志目录 |
| `output_dir` | `outputs` | 解析内容的输出目录 |
| `pdf_parse_engine` | `pipeline` | PDF 解析引擎（pipeline、vlm-sglang-engine） |
| `enable_mcp` | `false` | 启用 MCP 服务器集成 |

### 环境变量

```bash
# 日志
LOG_LEVEL=INFO
LOG_DIR=logs

# 输出
OUTPUT_DIR=outputs

# PDF 解析引擎
PDF_PARSE_ENGINE=pipeline  # 或 vlm-sglang-engine

# MCP 集成
ENABLE_MCP=false

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### Docker 配置

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

## 🏗️ 项目结构

```
markio/
├── markio/           # 主包
│   ├── main.py       # FastAPI 应用程序入口点
│   ├── routers/      # API 路由定义
│   ├── parsers/      # 文档解析模块
│   ├── schemas/      # 数据模型和验证
│   ├── utils/        # 工具函数
│   ├── web/          # Web 界面（Gradio）
│   ├── sdk/          # Python SDK
│   └── markio_mcp/  # MCP 服务器集成
├── docs/             # 文档
├── scripts/          # 工具脚本
├── tests/            # 测试文件
├── Dockerfile        # Docker 配置
├── compose.yaml      # Docker Compose 配置
└── pyproject.toml    # 项目配置
```

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 🙏 致谢

- [MinerU](https://github.com/opendatalab/MinerU) - 高质量 PDF 解析引擎
- [docling](https://github.com/docling-project/docling) - 多格式文档解析
- [pandoc](https://pandoc.org) - 通用文档转换器
- [LibreOffice](https://www.libreoffice.org) - 开源办公套件
- [FastAPI](https://fastapi.tiangolo.com) - 现代 Web 框架
- [Gradio](https://gradio.app) - Web 界面框架

## 📞 支持

- **问题反馈**: [GitHub Issues](https://github.com/Tendo33/markio/issues)
- **讨论**: [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- **文档**: [项目 Wiki](https://github.com/Tendo33/markio/wiki)

---

**由 Markio 团队用心制作 ❤️** 