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
- **多格式支持**：PDF、Office文档、HTML、EPUB、图片等
- **高性能**：异步处理、GPU加速、并发请求
- **灵活集成**：CLI、Python SDK、REST API适配任何工作流
- **生产就绪**：Docker支持、健康检查、监控
- **统一输出**：Markdown格式，保留元数据
- **开发友好**：简洁API、完整文档、类型提示

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

## 用法示例

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
| 参数名              | 类型         | 必填 | 说明                                          |
|---------------------|--------------|------|-----------------------------------------------|
| file                | 文件         | 是   | 需要解析的 PDF 文件                           |
| save_parsed_content | bool         | 否   | 是否保存解析内容（默认：false）               |
| save_middle_content | bool         | 否   | 保存中间处理文件（默认：false）               |
| output_dir          | str          | 否   | 解析内容保存目录（默认：outputs）             |
| parse_method        | str          | 否   | 解析方式（auto/ocr/txt，默认：auto）          |
| lang                | str          | 否   | 文档语言（ch/en/korean/japan...，默认：ch）   |
| start_page          | int          | 否   | 起始页码（默认：0）                           |
| end_page            | int/None     | 否   | 结束页码（默认：None，解析到末页）            |

#### 返回格式
JSON示例：
```json
{
  "parsed_content": "# Markdown内容 ...",
  "status_code": 200
}
```

### 完整API端点参考

| 文件格式 | 端点 | 方法 | 说明 |
|----------|------|------|------|
| PDF | `/v1/parse_pdf_file` | POST | 解析PDF文件，支持OCR/VLM |
| PDF VLM | `/v1/parse_pdf_vlm_file` | POST | 使用视觉语言模型解析PDF |
| DOCX | `/v1/parse_docx_file` | POST | 解析DOCX（Word）文件 |
| DOC | `/v1/parse_doc_file` | POST | 解析旧版DOC文件（自动转换） |
| PPTX | `/v1/parse_pptx_file` | POST | 解析PPTX（PowerPoint）文件 |
| PPT | `/v1/parse_ppt_file` | POST | 解析旧版PPT文件（自动转换） |
| XLSX | `/v1/parse_xlsx_file` | POST | 解析XLSX（Excel）文件 |
| HTML | `/v1/parse_html_file` | POST | 解析HTML文件 |
| URL | `/v1/parse_url_file` | POST | 从URL解析网页 |
| EPUB | `/v1/parse_epub_file` | POST | 解析EPUB电子书文件 |
| 图片 | `/v1/parse_image_file` | POST | 使用OCR解析图片 |

#### 通用请求参数
所有端点都接受以下通用参数：
- `file` (UploadFile)：要解析的文档文件
- `save_parsed_content` (bool)：保存解析内容到磁盘
- `save_middle_content` (bool)：保存中间处理文件
- `output_dir` (str)：自定义输出目录路径

#### PDF专用参数
- `parse_method` (str)：`auto`、`ocr` 或 `txt`
- `lang` (str)：文档语言代码
- `start_page` (int)：起始页码（从0开始）
- `end_page` (int)：结束页码（包含）

#### VLM专用参数
- `server_url` (str)：VLM服务器端点

### CLI 示例

#### 基础用法
```bash
# 简单PDF转换
markio pdf document.pdf

# 自定义文件名保存
markio pdf document.pdf -o my_document.md

# 批量转换多个文件
markio pdf *.pdf --save --output ./results/
```

#### 高级CLI选项
```bash
# 指定语言和页码范围转换
markio pdf document.pdf \
  --lang en \
  --start-page 5 \
  --end-page 15 \
  --save \
  --output ./results/

# 使用VLM引擎解析PDF（视觉语言模型）
markio pdf-vlm document.pdf --save --server http://localhost:30000

# 转换Office文档
markio docx report.docx --save
markio pptx presentation.pptx --save --output ./slides/
markio xlsx data.xlsx --save

# 转换旧版Office格式（自动转换为现代格式）
markio doc legacy.doc --save
markio ppt legacy.ppt --save --output ./presentations/

# 转换网页内容
markio url https://example.com --save
markio html page.html --save

# 使用OCR转换图片
markio image screenshot.png --save --lang en

# 转换EPUB为Markdown
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

#### CLI文档
详细的CLI使用指南、命令和示例，请查看 [CLI使用指南](docs/cli_usage_zh.md)

### Python SDK 示例

#### 基础SDK用法
```python
from markio.sdk.markio_sdk import MarkioSDK
import asyncio

async def basic_sdk_example():
    # 初始化SDK
    sdk = MarkioSDK(output_dir="./parsed_docs")
    
    # 解析PDF文档
    result = await sdk.parse_pdf(
        file_path="document.pdf",
        parse_method="auto",
        save_parsed_content=True,
        start_page=0,
        end_page=10
    )
    
    print(f"内容: {result['content'][:200]}...")
    print(f"文件名: {result['file_name']}")
    print(f"输出路径: {result['output_path']}")
    
    return result

# 运行
result = asyncio.run(basic_sdk_example())
```

#### SDK文档
完整的SDK文档，包括所有方法、示例和高级模式，请查看 [SDK使用指南](docs/sdk_usage_zh.md)

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

#### 性能调优配置

##### 高性能（GPU）
```bash
# GPU最大性能
MINERU_DEVICE_MODE=cuda
MINERU_MIN_BATCH_INFERENCE_SIZE=512
MINERU_VIRTUAL_VRAM_SIZE=16384
VLM_GPU_MEMORY_UTILIZATION=0.9
PDF_PARSE_ENGINE=pipeline
```

##### 平衡模式（混合GPU/CPU）
```bash
# 平衡性能和内存使用
MINERU_DEVICE_MODE=cuda
MINERU_MIN_BATCH_INFERENCE_SIZE=256
MINERU_VIRTUAL_VRAM_SIZE=8192
VLM_GPU_MEMORY_UTILIZATION=0.9
```

##### 内存受限（CPU）
```bash
# 保守内存使用
MINERU_DEVICE_MODE=cpu
MINERU_MIN_BATCH_INFERENCE_SIZE=128
MINERU_VIRTUAL_VRAM_SIZE=4096
VLM_GPU_MEMORY_UTILIZATION=0.7
```

##### 开发/调试
```bash
# 开发详细日志
LOG_LEVEL=DEBUG
LOG_DIR=./debug_logs
MINERU_MIN_BATCH_INFERENCE_SIZE=64  # 较小批量用于调试
```

#### 环境特定配置

##### 开发环境 (.env.development)
```bash
# 开发环境
LOG_LEVEL=DEBUG
OUTPUT_DIR=./dev_outputs
PDF_PARSE_ENGINE=pipeline
MINERU_DEVICE_MODE=cpu  # 使用CPU节省GPU资源
MINERU_MIN_BATCH_INFERENCE_SIZE=64
LOG_DIR=./dev_logs
```

##### 生产环境 (.env.production)
```bash
# 生产环境
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

##### 测试环境 (.env.test)
```bash
# 测试环境
LOG_LEVEL=WARNING
OUTPUT_DIR=./test_outputs
PDF_PARSE_ENGINE=pipeline
MINERU_DEVICE_MODE=cpu
MINERU_MIN_BATCH_INFERENCE_SIZE=32
LOG_DIR=./test_logs
```

#### 配置验证

验证您的配置：
```bash
# 检查环境变量是否加载
python -c "
from markio.settings import settings
print('输出目录:', settings.output_dir)
print('日志级别:', settings.log_level)
print('PDF引擎:', settings.pdf_parse_engine)
print('设备模式:', settings.mineru_device_mode)
"

# 使用样例文件测试配置
markio pdf test.pdf -s -o ./config_test/
```

#### 配置最佳实践

1. **使用 .env 文件进行环境特定设置**
2. **永远不要将敏感信息提交到版本控制**
3. **根据硬件使用适当的内存设置**
4. **监控日志以查看配置相关警告**
5. **先在开发环境测试配置更改**

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


</details>

---

## 🔧 故障排除与常见问题

### 常见问题

#### 安装问题
**问题**：找不到 `libreoffice` 或 `pandoc`
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y libreoffice pandoc

# macOS
brew install libreoffice pandoc

# Windows
# 从官方网站下载并添加到PATH
```

**问题**：Python依赖安装失败
```bash
# 使用uv代替pip
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e .
```

#### 服务启动问题
**问题**：服务无法在端口8000启动
```bash
# 检查端口是否可用
netstat -tulpn | grep :8000

# 使用不同端口
export PORT=8080
python markio/main.py
```

**问题**：MinerU无法检测到GPU
```bash
# 检查GPU可用性
nvidia-smi

# 强制使用CPU模式
export MINERU_DEVICE_MODE=cpu
python markio/main.py
```

#### PDF处理问题
**问题**：PDF解析出现内存错误
```bash
# 减少批量大小
export MINERU_MIN_BATCH_INFERENCE_SIZE=128
export MINERU_VIRTUAL_VRAM_SIZE=4096

# 使用CPU模式
export MINERU_DEVICE_MODE=cpu
```

**问题**：VLM引擎连接失败
```bash
# 检查VLM服务器状态
curl http://localhost:30000/health

# 验证服务器URL
export VLM_SERVER_URL=http://localhost:30000
```

#### 性能问题
**问题**：处理速度慢
```bash
# 启用GPU加速
export MINERU_DEVICE_MODE=cuda

# 增加批量大小以提高吞吐量
export MINERU_MIN_BATCH_INFERENCE_SIZE=512

# 使用pipeline引擎以获得更好性能
export PDF_PARSE_ENGINE=pipeline
```

**问题**：内存使用过高
```bash
# 减少内存分配
export VLM_GPU_MEMORY_UTILIZATION=0.7
export MINERU_VIRTUAL_VRAM_SIZE=4096

# 顺序处理文件而不是并行处理
```

### API集成问题

#### 文件上传问题
**问题**：大文件上传失败
```bash
# 检查文件大小限制
# FastAPI默认：约100MB，可在应用设置中增加

# 分块处理大文件
# 对于非常大的文件使用CLI
markio pdf large_file.pdf --save --output ./results/
```

**问题**：不支持的文件格式
```bash
# 首先转换旧格式
# DOC → DOCX, PPT → PPTX 使用LibreOffice
# 或使用markio的自动转换：
markio doc legacy.doc --save
```

### CLI问题

#### 命令未找到
**问题**：`markio` 命令不可用
```bash
# 检查安装
pip list | grep markio

# 以开发模式重新安装
uv pip install -e .

# 如需要添加到PATH
export PATH=$PATH:/path/to/markio
```

#### 配置问题
**问题**：环境变量未加载
```bash
# 在项目根目录创建.env文件
echo "OUTPUT_DIR=./my_outputs" > .env
echo "LOG_LEVEL=DEBUG" >> .env

# 验证变量已加载
python -c "from markio.settings import settings; print(settings.output_dir)"
```

### 性能优化

#### GPU加速
```bash
# 为MinerU启用GPU
export MINERU_DEVICE_MODE=cuda
export MINERU_VIRTUAL_VRAM_SIZE=16384  # 16GB

# 优化vLLM内存使用
export VLM_GPU_MEMORY_UTILIZATION=0.9
```

#### 批量处理
```bash
# 高效处理多个文件
find ./input_dir -name "*.pdf" -exec markio pdf {} --save --output ./output_dir/ \;

# 使用parallel进行大批量并行处理
parallel markio pdf {} --save --output ./output_dir/ ::: *.pdf
```

#### 内存管理
```bash
# 监控内存使用
htop 或 glances

# 根据可用内存调整
export MINERU_VIRTUAL_VRAM_SIZE=8192  # 16GB内存系统使用8GB
export VLM_GPU_MEMORY_UTILIZATION=0.7   # 保守内存使用
```

### 获取帮助

#### 调试模式
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
export LOG_DIR=./debug_logs

# 检查服务健康
curl http://localhost:8000/health

# 查看日志
tail -f logs/markio.log
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
- **CLI使用指南**: [docs/cli_usage.md](docs/cli_usage.md)
- **中文CLI指南**: [docs/cli_usage_zh.md](docs/cli_usage_zh.md)
- **SDK使用指南**: [docs/sdk_usage.md](docs/sdk_usage.md)
- **中文SDK指南**: [docs/sdk_usage_zh.md](docs/sdk_usage_zh.md)

---

**由 Markio 团队用心制作 ❤️** 