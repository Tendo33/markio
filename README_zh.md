<img src="assets/image.png" alt="Markio Logo"  height="350" style="display:block;margin:auto;">

> **高性能文档转换API平台**  
> *一行命令，解析、转换、结构化你的文档。*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![MinerU](https://img.shields.io/badge/Based%20on-MinerU-orange.svg)](https://github.com/opendatalab/MinerU)
[![docling](https://img.shields.io/badge/Based%20on-docling-purple.svg)](https://github.com/docling-project/docling)
[![pandoc](https://img.shields.io/badge/Based%20on-pandoc-green.svg)](https://pandoc.org)
[![LibreOffice](https://img.shields.io/badge/Based%20on-LibreOffice-blue.svg)](https://www.libreoffice.org)

![演示动画/截图](assets/demo.gif)

---

## 🚀 为什么选择 Markio？
- **一站式**：支持PDF、Office（DOC/DOCX/PPT/PPTX/XLSX）、HTML、EPUB、图片等多格式解析，统一平台。
- **高性能**：异步处理、GPU加速、并发请求。
- **灵活集成**：CLI、Python SDK、REST API，适配任意工作流。
- **生产级**：Docker支持、健康检查、监控能力。
- **多格式输出**：一致的Markdown输出，保留元数据。

| 应用场景     | 说明                       |
|--------------|----------------------------|
| API集成      | 统一REST接口，支持多格式   |
| CLI自动化    | 一行命令批量转换文档       |
| Web预览      | Gradio界面实时反馈         |
| ...          | ...                        |

---

## ⚡ 快速上手

### Docker（推荐）
```bash
git clone https://github.com/Tendo33/markio.git
cd markio
docker compose up -d

# 访问服务
# API文档: http://localhost:8000/docs
# Web界面: http://localhost:7860
# 健康检查: http://localhost:8000/health
```

### 本地安装
```bash
# 系统依赖（Ubuntu/Debian）
sudo apt update && sudo apt install -y libreoffice pandoc

# 安装Python包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或重启终端

# 克隆并安装
 git clone https://github.com/Tendo33/markio.git
 cd markio
 uv venv && source .venv/bin/activate  # Windows下用 .venv\Scripts\activate
 uv pip install -e .

# 启动服务
./start_services.sh  # 或分别运行：
# python markio/main.py          # API服务
# python markio/web/gradio_frontend.py  # Web界面
```

---

## 🛠️ 用法示例

### REST API

#### PDF解析（高级选项）
```python
import httpx
import asyncio

async def parse_pdf():
    async with httpx.AsyncClient() as client:
        # 基础解析
        files = {"file": open("document.pdf", "rb")}
        resp = await client.post("http://localhost:8000/v1/parse_pdf_file", files=files)
        result = resp.json()
        print(f"Status: {result['status_code']}")
        print(f"Content length: {len(result['parsed_content'])} 字符")
        
        # 高级解析选项
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

# 运行
result = asyncio.run(parse_pdf())
```

#### 批量处理
```python
import os
import httpx
from pathlib import Path

def batch_convert_documents(directory: str, output_dir: str):
    """批量转换目录下所有PDF"""
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
                print(f"✅ 已转换: {pdf_file.name}")
            else:
                print(f"❌ 失败: {pdf_file.name}")

# 用法
batch_convert_documents("./input_pdfs", "./converted_md")
```

#### 请求参数
| 参数名              | 类型         | 必填 | 说明                                   |
|---------------------|--------------|------|----------------------------------------|
| file                | 文件         | 是   | 需要解析的 PDF 文件                    |
| save_parsed_content | bool         | 否   | 是否保存解析内容到本地（默认 false）   |
| output_dir          | str          | 否   | 解析内容保存目录（默认 outputs）       |
| parse_method        | str          | 否   | 解析方式（auto/ocr/txt，默认 auto）    |
| lang                | str          | 否   | 文档语言（ch/en/korean/japan...，默认 ch）|
| start_page          | int          | 否   | 起始页码（默认 0）                     |
| end_page            | int/None     | 否   | 结束页码（默认 None，解析到末页）      |

#### 返回格式
JSON示例：
```json
{
  "parsed_content": "# Markdown内容 ...",
  "status_code": 200
}
```

### CLI 示例
```bash
# 简单PDF转换
markio pdf document.pdf

# 自定义文件名保存
markio pdf document.pdf -o my_document.md

# 批量转换
markio pdf *.pdf --save --output ./results/
```

#### 高级CLI选项
```bash
# 指定语言和页码范围
markio pdf document.pdf \
  --lang en \
  --start-page 5 \
  --end-page 15 \
  --save \
  --output ./results/

# Office文档转换
markio docx report.docx --save
markio pptx presentation.pptx --save --output ./slides/
markio xlsx data.xlsx --save

# 网页内容转换
markio url https://example.com --save
markio html page.html --save

# 图片OCR
markio image screenshot.png --save --lang en

# EPUB转Markdown
markio epub book.epub --save --output ./books/
```

#### CLI配置
```bash
# 查看配置
markio config

# 设置默认输出目录
markio config set output_dir ~/Documents/markio_output

# 设置默认语言
markio config set lang en

# 恢复默认
markio config reset
```

### Python SDK 示例

#### 基础用法
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def basic_sdk_example():
    # 初始化SDK
    sdk = MarkioSDK(base_url="http://localhost:8000")
    
    # 解析文档
    result = await sdk.parse_document(
        file_path="document.pdf",
        save_parsed_content=True,
        output_dir="./results"
    )
    
    print(f"内容: {result['content'][:200]}...")
    print(f"元数据: {result['metadata']}")
    
    return result

# 运行
result = asyncio.run(basic_sdk_example())
```

#### 高级SDK特性
```python
from markio.sdk.markio_sdk import MarkioSDK
from markio.sdk.schemas import ParseOptions

async def advanced_sdk_example():
    sdk = MarkioSDK()
    
    # 配置解析选项
    options = ParseOptions(
        parse_method="auto",
        language="en",
        start_page=0,
        end_page=None,
        save_parsed_content=True,
        output_dir="./results"
    )
    
    # 并发解析多个文档
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    tasks = [sdk.parse_document(file_path=f, options=options) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ {files[i]} 失败: {result}")
        else:
            print(f"✅ {files[i]}: {len(result['content'])} 字符")
    
    return results

# 运行
results = asyncio.run(advanced_sdk_example())
```

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

</details>

<details>
<summary>⚙️ 配置与项目结构</summary>

### 配置指南

#### 环境变量

| 变量名 | 默认值 | 说明 | 示例 |
|--------|--------|------|------|
| `LOG_LEVEL` | INFO | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_DIR` | logs | 日志目录 | `/var/log/markio` |
| `OUTPUT_DIR` | outputs | 解析输出目录 | `/data/outputs` |
| `PDF_PARSE_ENGINE` | pipeline | PDF解析引擎 | `pipeline`, `vlm-sglang-engine` |
| `MINERU_DEVICE_MODE` | auto | MinerU设备选择 | `cuda`, `cpu`, `mps` |
| `VLM_SERVER_URL` | - | VLM服务端点 | `http://localhost:30000` |
| `ENABLE_MCP` | false | 启用MCP服务 | `true`, `false` |
| `HOST` | 0.0.0.0 | 服务监听地址 | `127.0.0.1` |
| `PORT` | 8000 | 服务端口 | `8080` |

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

**VLM引擎**
```bash
# 需外部VLM服务
PDF_PARSE_ENGINE=vlm-sglang-engine
VLM_SERVER_URL=http://localhost:30000
```

#### 性能调优
```bash
# 内存优化
MINERU_DEVICE_MODE=cpu  # 无GPU时

# 批量处理
PDF_PARSE_ENGINE=pipeline
MINERU_BATCH_SIZE=4

# 调试日志
LOG_LEVEL=DEBUG
LOG_DIR=./debug_logs
```

### 项目结构
```
markio/
├── markio/           # 主包
│   ├── main.py       # FastAPI应用入口
│   ├── routers/      # API路由
│   ├── parsers/      # 各类文档解析器
│   ├── schemas/      # 数据模型
│   ├── utils/        # 工具函数
│   ├── web/          # Gradio前端
│   ├── sdk/          # Python SDK
│   └── mcps/         # MCP集成
├── docs/             # 文档
├── scripts/          # 工具脚本
├── tests/            # 测试
├── Dockerfile        # Docker配置
├── compose.yaml      # Docker Compose配置
├── pyproject.toml    # 项目配置
```

</details>

---

## 🤝 社区与支持

- [贡献指南](CONTRIBUTING.md)
- [问题反馈](https://github.com/Tendo33/markio/issues)
- [讨论区](https://github.com/Tendo33/markio/discussions)
- [Wiki/文档](https://github.com/Tendo33/markio/wiki)
- [路线图/更新日志](#)
- [FAQ](#)

---

**由 Markio 团队用心制作 ❤️**

---

> English: [README.md](README.md) 