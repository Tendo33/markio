<img src="assets/image.png" alt="Markio Logo"  height="350" style="display:block;margin:auto;">

> **高性能文档转换API平台**  
> 一行命令，解析、转换、结构化你的文档。

<div align="center">

### 🌍 Language / 语言

[English](README.md) | **中文**

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

## 为什么选择 Markio？
- **多格式支持**：PDF、Office文档、HTML、EPUB、图片、生物数据（FASTA/GenBank）等
- **高性能**：异步处理、GPU加速、并发请求
- **灵活集成**：CLI、Python SDK、REST API适配任何工作流
- **生产就绪**：Docker支持、健康检查、监控
- **统一输出**：Markdown格式，保留元数据
- **开发友好**：简洁API、完整文档、类型提示
- **BioPython内置**：专业级生物序列分析能力，开箱即用

| 应用场景        | 说明                           | 适用场景                         |
|-----------------|--------------------------------|----------------------------------|
| API集成         | 统一REST API支持所有格式        | 微服务、Web应用                   |
| CLI自动化       | 一行命令批量转换文档            | CI/CD、数据处理流水线             |
| Web预览         | Gradio界面即时反馈              | 原型设计、用户测试                |
| SDK集成         | Python库用于自定义应用          | 数据科学、机器学习工作流          |
| 企业应用        | 可扩展的文档处理                | 文档管理系统                     |

---

## 快速上手

### Docker（推荐）
```bash
# 克隆并启动服务
git clone https://github.com/Tendo33/markio.git
cd markio
docker compose up -d

# 访问服务
# API文档: http://localhost:8000/docs
# Web界面:    http://localhost:7860
# 健康检查:   http://localhost:8000/health
```

### 本地安装
```bash
# 系统依赖（Ubuntu/Debian）
sudo apt update && sudo apt install -y libreoffice pandoc

# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或重启终端

# 克隆并安装
 git clone https://github.com/Tendo33/markio.git
 cd markio
 uv sync
 uv pip install -e .

# 启动服务
export CUDA_VISIBLE_DEVICES=0
./start_services.sh  # 或分别运行：
# python markio/main.py          # API服务
# python markio/web/gradio_frontend.py  # Web界面
```

---

## 使用方式

Markio 提供三种灵活的使用方式，满足不同场景需求：

### 🌐 REST API

适合微服务集成和Web应用开发。启动服务后访问 `http://localhost:8000/docs` 查看完整的API文档。

**快速示例**：
```python
import httpx
import asyncio

async def parse_pdf():
    async with httpx.AsyncClient() as client:
        files = {"file": open("document.pdf", "rb")}
        resp = await client.post("http://localhost:8000/v1/parse_pdf_file", files=files)
        result = resp.json()
        print(f"解析内容: {result['parsed_content'][:200]}...")
        return result

asyncio.run(parse_pdf())
```

**核心API端点**：

| 文件格式 | 端点 | 说明 |
|----------|------|------|
| PDF | `/v1/parse_pdf_file` | 解析PDF，支持OCR/VLM |
| DOCX/DOC | `/v1/parse_docx_file`, `/v1/parse_doc_file` | Word文档解析 |
| PPTX/PPT | `/v1/parse_pptx_file`, `/v1/parse_ppt_file` | PowerPoint解析 |
| XLSX | `/v1/parse_xlsx_file` | Excel表格解析 |
| HTML/URL | `/v1/parse_html_file`, `/v1/parse_url_file` | 网页内容解析 |
| 图片 | `/v1/parse_image_file` | OCR图片识别 |
| FASTA | `/v1/parse_fasta_file` | 生物序列解析（DNA/蛋白质） |
| GenBank | `/v1/parse_genbank_file` | GenBank记录解析（含注释） |

### ⌨️ CLI 命令行

适合批量处理、自动化脚本和CI/CD集成。

**快速示例**：
```bash
# PDF转换
markio pdf document.pdf --save

# 批量处理
markio pdf *.pdf --save --output ./results/

# Office文档
markio docx report.docx --save
```

📖 **详细文档**：[CLI使用指南](docs/cli_usage_zh.md)

### 🐍 Python SDK

适合自定义应用开发和数据处理工作流。

**快速示例**：
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def main():
    sdk = MarkioSDK(output_dir="./parsed_docs")
    result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    print(f"解析完成: {result['file_name']}")

asyncio.run(main())
```

📖 **详细文档**：[SDK使用指南](docs/sdk_usage_zh.md)

---

<details>
<summary>📄 支持格式与引擎</summary>

| 格式   | 引擎             | 特性                |
|--------|------------------|---------------------|
| PDF    | MinerU, VLM, OCR | 布局、OCR、表格等   |
| DOCX   | docling          | ...                 |
| PPTX   | docling          | ...                 |
| DOC    | LibreOffice+docling | ...              |
| PPT    | LibreOffice+docling | ...              |
| XLSX   | docling          | ...                 |
| HTML   | docling          | ...                 |
| URL    | jina             | ...                 |
| EPUB   | pandoc           | ...                 |
| 图片   | MinerU           | OCR                 |
| FASTA  | 自定义解析器      | 序列解析、统计、GC含量 |
| GenBank| 自定义解析器      | 元数据、特征、注释   |

</details>

<details>
<summary>⚙️ 配置与项目结构</summary>

### 配置指南

#### 环境变量

| 变量名 | 默认值 | 说明 | 示例 |
|--------|--------|------|------|
| `LOG_LEVEL` | INFO | 日志详细级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_DIR` | logs | 日志文件目录 | `/var/log/markio` |
| `OUTPUT_DIR` | outputs | 解析内容输出目录 | `/data/outputs` |
| `PDF_PARSE_ENGINE` | pipeline | PDF解析方法 | `pipeline`, `vlm-vllm-engine`, `vlm-vllm-client` |
| `MINERU_DEVICE_MODE` | cuda | MinerU设备选择 | `cuda`, `cpu`, `mps` |
| `VLM_SERVER_URL` | - | VLM服务器端点 | `http://localhost:30000` |
| `VLM_GPU_MEMORY_UTILIZATION` | 0.9 | vLLM GPU内存利用率 | `0.0-1.0` |
| `ENABLE_MCP` | false | 启用MCP服务器 | `true`, `false` |
| `HOST` | 0.0.0.0 | 服务器绑定地址 | `127.0.0.1` |
| `PORT` | 8000 | 服务器端口 | `8080` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU最小批量推理大小 | `128`, `256`, `512` |
| `MINERU_MODEL_SOURCE` | local | MinerU模型源 | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | MinerU虚拟显存大小（MB） | `8192`, `16384` |

#### 配置文件

在项目根目录创建 `.env` 文件：
```bash
# 基本配置
LOG_LEVEL=INFO
OUTPUT_DIR=./parsed_documents
PDF_PARSE_ENGINE=pipeline

# GPU配置（如有）
MINERU_DEVICE_MODE=cuda

# VLM配置（如使用VLM引擎）
VLM_SERVER_URL=http://localhost:30000

# 服务配置
HOST=0.0.0.0
PORT=8000
```

#### PDF引擎配置

**Pipeline引擎（默认）**
```bash
# 使用MinerU自动选择OCR/VLM
PDF_PARSE_ENGINE=pipeline
```

**VLM引擎（vLLM）**
```bash
# 使用vLLM引擎（MinerU 2.5.0+）
PDF_PARSE_ENGINE=vlm-vllm-engine

# 或使用vLLM客户端模式（需外部vLLM服务）
PDF_PARSE_ENGINE=vlm-vllm-client
VLM_SERVER_URL=http://localhost:30000
```

#### 完整配置参考

##### 核心设置
| 变量 | 默认值 | 说明 | 可选值 |
|------|--------|------|--------|
| `LOG_LEVEL` | INFO | 日志详细级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_DIR` | logs | 日志文件目录 | 任意有效路径 |
| `OUTPUT_DIR` | outputs | 默认输出目录 | 任意有效路径 |
| `HOST` | 0.0.0.0 | 服务器绑定地址 | IP地址或主机名 |
| `PORT` | 8000 | 服务器端口 | 1-65535 |

##### PDF处理配置
| 变量 | 默认值 | 说明 | 可选值 |
|------|--------|------|--------|
| `PDF_PARSE_ENGINE` | pipeline | PDF解析方法 | `pipeline`, `vlm-vllm-engine`, `vlm-vllm-client` |
| `MINERU_DEVICE_MODE` | cuda | MinerU设备选择 | `cuda`, `cpu`, `mps` |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU批量大小 | 1-1024 |
| `MINERU_MODEL_SOURCE` | local | MinerU模型源 | `local`, `remote` |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | 虚拟显存大小（MB） | 1024-65536 |

##### VLM配置
| 变量 | 默认值 | 说明 | 可选值 |
|------|--------|------|--------|
| `VLM_SERVER_URL` | - | VLM服务器端点 | 有效URL |
| `VLM_GPU_MEMORY_UTILIZATION` | 0.9 | vLLM GPU内存利用率 | 0.1-1.0 |

##### 高级设置
| 变量 | 默认值 | 说明 | 可选值 |
|------|--------|------|--------|
| `ENABLE_MCP` | false | 启用MCP服务器 | `true`, `false` |


### 项目结构

```
markio/
├── markio/           # 主包
│   ├── main.py       # FastAPI应用入口点
│   ├── routers/      # API路由定义
│   ├── parsers/      # 文档解析模块
│   ├── schemas/      # 数据模型和验证
│   ├── utils/        # 工具函数
│   ├── web/          # Web界面（Gradio）
│   ├── sdk/          # Python SDK
│   └── mcps/         # MCP服务器集成
├── docs/             # 文档
├── scripts/          # 工具脚本
├── tests/            # 测试文件
├── Dockerfile        # Docker配置
├── compose.yaml      # Docker Compose配置
├── pyproject.toml    # 项目配置
```


#### 社区支持
- [GitHub Issues](https://github.com/Tendo33/markio/issues) - 错误报告和功能请求
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions) - 一般问题和帮助
- [Wiki文档](https://github.com/Tendo33/markio/wiki) - 详细指南和教程

#### 报告问题
报告问题时，请包含：
1. 操作系统和版本
2. Python版本（`python --version`）
3. Markio版本（`pip show markio`）
4. 错误消息和堆栈跟踪
5. 重现问题的步骤
6. 示例文件（如适用且非机密）

---

## 🤝 社区与支持

- [贡献指南](CONTRIBUTING.md)
- [问题反馈](https://github.com/Tendo33/markio/issues)
- [讨论区](https://github.com/Tendo33/markio/discussions)
- [Wiki/文档](https://github.com/Tendo33/markio/wiki)
- [路线图/更新日志](#)
- [常见问题](#故障排除与常见问题)

### 文档链接

- **CLI使用指南**: [docs/cli_usage_zh.md](docs/cli_usage_zh.md)
- **SDK使用指南**: [docs/sdk_usage_zh.md](docs/sdk_usage_zh.md)

---

**由 Markio 团队用心制作 ❤️** 