# 🚀 Markio CLI Usage Guide

> **Powerful, developer-friendly CLI for document parsing and conversion.**

[Back to Main README](../README.md)

---

## ✨ Why Use Markio CLI?
- **One command, parse anything:** PDF, Office, HTML, EPUB, Images...
- **Batch & Automation:** Easily process folders or pipelines.
- **Flexible Output:** Save as Markdown, control output location, integrate with scripts.
- **Advanced Engines:** OCR, VLM, text extraction, auto-detection.

---

## ⚡ Quick Start

```bash
# Parse a PDF to Markdown
markio pdf document.pdf -o result.md

# Parse a DOCX file
markio docx document.docx --save --output result.md

# Batch process all PDFs in a folder
for file in *.pdf; do markio pdf "$file" -s -o "${file%.pdf}.md"; done
```

---

## 🛠️ Typical Scenarios

| Scenario         | Command Example                                  |
|------------------|--------------------------------------------------|
| PDF OCR          | markio pdf document.pdf -m ocr                   |
| VLM Engine       | markio pdf-vlm document.pdf                      |
| Page Range       | markio pdf document.pdf -st 0 -e 5               |
| HTML/URL         | markio html page.html / markio url https://...   |
| Image OCR        | markio image screenshot.png                      |
| Save to Dir      | markio pdf document.pdf -s -o output_dir/file.md |

---

## 🔧 Advanced Usage

- **Parallel Processing:**
  ```bash
  parallel markio pdf {} -s -o "{.}.md" ::: *.pdf
  ```
- **Python SDK Integration:**
  ```python
  from markio.sdk.markio_sdk import MarkioSDK
  sdk = MarkioSDK()
  result = await sdk.parse_document(file_path="document.pdf", save_parsed_content=True)
  print(result["content"])
  ```
- **Debugging:**
  ```bash
  export MARKIO_LOG_LEVEL=DEBUG
  markio pdf document.pdf -s -o debug_output.md
  ```

---

## ⚙️ Environment Variables

| Variable             | Default   | Description                |
|----------------------|-----------|----------------------------|
| MARKIO_OUTPUT_DIR    | outputs   | Default output directory   |
| MARKIO_LOG_LEVEL     | INFO      | Log level                  |
| MARKIO_PDF_ENGINE    | pipeline  | PDF parsing engine         |

---

## ❓ FAQ & Troubleshooting

- [Project Wiki & FAQ](https://github.com/Tendo33/markio/wiki)
- Common issues: file format, OCR quality, engine connection, logs.
- For more, see [Main README](../README.md) or [中文CLI指南](cli_usage_zh.md)

---

**For more information, visit the [Markio Project Documentation](https://github.com/Tendo33/markio)** 