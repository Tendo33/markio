# Markio CLI 使用指南

## 概述

Markio CLI 是一个强大的命令行工具，用于将各种文档格式解析为 Markdown。支持以下格式：

- **PDF**: 支持 OCR、VLM 和文本提取
- **Word**: DOC 和 DOCX 格式
- **PowerPoint**: PPT 和 PPTX 格式
- **Excel**: XLSX 格式
- **Web**: HTML 文件和 URL
- **E-book**: EPUB 格式
- **Images**: 支持 OCR 文本提取

## 基本语法

```bash
markio <命令> <文件路径> [选项]
```

## 命令参考

### PDF 解析

```bash
# 基本 PDF 解析
markio pdf document.pdf

# 使用 VLM 引擎解析
markio pdf-vlm document.pdf

# 指定解析方法
markio pdf document.pdf --method auto
```

### Word 文档解析

```bash
# 解析 DOCX 文件
markio docx document.docx

# 解析 DOC 文件（旧格式）
markio doc document.doc
```

### PowerPoint 解析

```bash
# 解析 PPTX 文件
markio pptx presentation.pptx

# 解析 PPT 文件（旧格式）
markio ppt presentation.ppt
```

### Excel 解析

```bash
# 解析 XLSX 文件
markio xlsx spreadsheet.xlsx
```

### Web 内容解析

```bash
# 解析 HTML 文件
markio html page.html

# 解析网页 URL
markio url https://example.com/article
```

### E-book 解析

```bash
# 解析 EPUB 文件
markio epub book.epub
```

### 图片解析

```bash
# 解析图片文件（OCR）
markio image screenshot.png
```

## 常用选项

### 输出控制

```bash
# 保存到指定文件
markio pdf document.pdf -o output.md
markio pdf document.pdf --output output.md

# 保存解析内容
markio pdf document.pdf -s
markio pdf document.pdf --save

# 组合使用
markio pdf document.pdf -s -o result.md
markio docx document.docx --save --output content.md
```

### PDF 特定选项

```bash
# 指定解析方法
markio pdf document.pdf -m auto    # 自动选择
markio pdf document.pdf -m ocr     # OCR 方法
markio pdf document.pdf -m txt     # 文本提取
markio pdf document.pdf --method auto

# 页面范围
markio pdf document.pdf -st 0 -e 5
markio pdf document.pdf --start 0 --end 5

# 只指定开始页
markio pdf document.pdf -st 10
markio pdf document.pdf --start 10

# 保存中间内容
markio pdf document.pdf -sm
markio pdf document.pdf --save-middle
```

### VLM 引擎选项

```bash
# 使用 VLM 引擎
markio pdf-vlm document.pdf

# 指定服务器地址
markio pdf-vlm document.pdf -sv http://127.0.0.1:30000
markio pdf-vlm document.pdf --server http://127.0.0.1:30000
```

## 高级用法

### 批量处理

```bash
# 处理目录中的所有文件
for file in *.pdf; do
    markio pdf "$file" -s -o "${file%.pdf}.md"
done

# 处理多种格式
for file in *; do
    case "${file##*.}" in
        pdf) markio pdf "$file" -s -o "${file%.*}.md" ;;
        docx) markio docx "$file" -s -o "${file%.*}.md" ;;
        pptx) markio pptx "$file" -s -o "${file%.*}.md" ;;
        ppt) markio ppt "$file" -s -o "${file%.*}.md" ;;
        xlsx) markio xlsx "$file" -s -o "${file%.*}.md" ;;
        html) markio html "$file" -s -o "${file%.*}.md" ;;
        epub) markio epub "$file" -s -o "${file%.*}.md" ;;
    esac
done
```

### 分页处理

```bash
# 处理大文档的分页
document="large_document.pdf"
total_pages=$(pdfinfo "$document" | grep Pages | awk '{print $2}')
page_size=10

for ((i=0; i<total_pages; i+=page_size)); do
    end_page=$((i + page_size - 1))
    if [ $end_page -gt $total_pages ]; then
        end_page=$total_pages
    fi
    markio pdf "$document" -st $i -e $end_page -s -o "part_${i}_${end_page}.md"
done
```

### 输出目录管理

```bash
# 创建输出目录
mkdir -p output_dir

# 保存到指定目录
markio pdf document.pdf -s -o output_dir/result.md

# 使用环境变量
export MARKIO_OUTPUT_DIR="./outputs"
markio pdf document.pdf -s -o result.md
```

### 调试模式

```bash
# 启用详细日志
export MARKIO_LOG_LEVEL=DEBUG
markio pdf document.pdf -s -o debug_output.md

# 保存中间处理结果
markio pdf document.pdf -s -sm -o debug_output.md
```

## Python SDK 使用

如果您需要在 Python 代码中使用 Markio，请参考以下示例：

```python
from markio.sdk.markio_sdk import MarkioSDK

# 初始化 SDK
sdk = MarkioSDK()

# 解析文档
result = await sdk.parse_document(
    file_path="document.pdf",
    save_parsed_content=True,
    output_dir="outputs"
)

print(f"解析结果: {result['content']}")
```

## 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MARKIO_OUTPUT_DIR` | `outputs` | 默认输出目录 |
| `MARKIO_LOG_LEVEL` | `INFO` | 日志级别 |
| `MARKIO_PDF_ENGINE` | `pipeline` | PDF 解析引擎 |

## 故障排除

### 常见问题

1. **文件格式不支持**
   - 检查文件扩展名是否正确
   - 确认文件未损坏

2. **OCR 失败**
   - 确保图片质量足够清晰
   - 检查是否有足够的系统内存

3. **VLM 引擎连接失败**
   - 确认服务器地址正确
   - 检查网络连接

### 日志查看

```bash
# 查看详细日志
export MARKIO_LOG_LEVEL=DEBUG
markio pdf document.pdf

# 保存日志到文件
markio pdf document.pdf 2>&1 | tee markio.log
```

## 性能优化

### 批量处理优化

```bash
# 并行处理多个文件
parallel markio pdf {} -s -o "{.}.md" ::: *.pdf

# 使用后台任务
for file in *.pdf; do
    (markio pdf "$file" -s -o "${file%.pdf}.md" &)
done
wait
```

### 内存优化

```bash
# 限制并发处理数量
sem --jobs 2 markio pdf {} -s -o "{.}.md" ::: *.pdf
```

## 更新和维护

```bash
# 检查版本
markio --version

# 更新工具
pip install --upgrade markio

# 查看帮助
markio --help
markio pdf --help
```

---

**更多信息请参考 [Markio 项目文档](https://github.com/Tendo33/markio)**