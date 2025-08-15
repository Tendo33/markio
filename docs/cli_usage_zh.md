# 🚀 Markio CLI 使用指南

> **一行命令，解析一切文档，极致开发者体验。**

[返回主README](../README_zh.md)

---

## ✨ 为什么用Markio CLI？
- **一行命令，解析多格式：** PDF、Office、HTML、EPUB、图片等
- **批量与自动化：** 轻松处理文件夹、脚本集成
- **灵活输出：** Markdown、目录控制、脚本友好
- **智能引擎：** OCR、VLM、文本提取，自动识别

---

## ⚡ 快速上手

```bash
# 解析PDF为Markdown
markio pdf document.pdf -o result.md

# 解析DOCX文件
markio docx document.docx --save --output result.md

# 批量处理文件夹下所有PDF
for file in *.pdf; do markio pdf "$file" -s -o "${file%.pdf}.md"; done
```

---

## 🛠️ 典型场景

| 场景         | 命令示例                                         |
|--------------|--------------------------------------------------|
| PDF OCR      | markio pdf document.pdf -m ocr                   |
| VLM引擎      | markio pdf-vlm document.pdf                      |
| 指定页码     | markio pdf document.pdf -st 0 -e 5               |
| HTML/URL     | markio html page.html / markio url https://...   |
| 图片OCR      | markio image screenshot.png                      |
| 输出到目录   | markio pdf document.pdf -s -o output_dir/file.md |

---

## 🔧 进阶用法

- **并行处理：**
  ```bash
  parallel markio pdf {} -s -o "{.}.md" ::: *.pdf
  ```
- **Python SDK集成：**
  ```python
  from markio.sdk.markio_sdk import MarkioSDK
  sdk = MarkioSDK()
  result = await sdk.parse_document(file_path="document.pdf", save_parsed_content=True)
  print(result["content"])
  ```
- **调试模式：**
  ```bash
  export MARKIO_LOG_LEVEL=DEBUG
  markio pdf document.pdf -s -o debug_output.md
  ```

---

## ⚙️ 环境变量

| 变量名              | 默认值   | 说明                 |
|---------------------|----------|----------------------|
| MARKIO_OUTPUT_DIR   | outputs  | 默认输出目录         |
| MARKIO_LOG_LEVEL    | INFO     | 日志级别             |
| MARKIO_PDF_ENGINE   | pipeline | PDF解析引擎          |

---

## ❓ FAQ与常见问题

- [项目Wiki与FAQ](https://github.com/Tendo33/markio/wiki)
- 常见问题：文件格式、OCR质量、引擎连接、日志查看等
- 更多内容见[主README](../README_zh.md) 或 [英文CLI指南](cli_usage.md)

---

**更多信息请参考 [Markio 项目文档](https://github.com/Tendo33/markio)**