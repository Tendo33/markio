# <img src="assets/logo.png" alt="Markio Logo" height="48" style="vertical-align:middle;"> Markio

> **高性能文档解析API平台**  
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
- **一站式**：支持PDF、Office、HTML、EPUB、图片等多格式解析。
- **智能引擎**：自动选择最佳解析方式（OCR/VLM/文本提取）。
- **批量与实时**：支持批量转换与Web实时预览。
- **CLI、SDK、API**：灵活集成，适配各种工作流。
- **GPU与Docker就绪**：高性能，易部署。

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
# 访问: http://localhost:8000/docs  (API)
#      http://localhost:7860       (Web界面)
```

### 本地安装
```bash
# 系统依赖
sudo apt install libreoffice pandoc
# Python 3.11+ & uv
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/Tendo33/markio.git
cd markio
uv venv && uv pip install -e .
```

---

## 🛠️ 典型用例

### REST API 示例
```python
import httpx
resp = httpx.post("http://localhost:8000/v1/parse_pdf_file", files={"file": open("test.pdf", "rb")})
print(resp.json())
```

### CLI 示例
```bash
markio pdf test.pdf -o result.md
markio docx test.docx --save --output result.md
```

### Python SDK 示例
```python
from markio.sdk.markio_sdk import MarkioSDK
sdk = MarkioSDK()
result = await sdk.parse_document(file_path="test.pdf", save_parsed_content=True)
print(result["content"])
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

- [详细配置说明](#配置)
- [项目结构](#项目结构)
- [环境变量](#环境变量)
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

> English: [README.md](../README.md) 