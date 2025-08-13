# Markio CLI Usage Guide

## Overview

Markio CLI is a powerful command-line tool for parsing various document formats to Markdown. Supports the following formats:

- **PDF**: Supports OCR, VLM and text extraction
- **Word**: DOC and DOCX formats
- **PowerPoint**: PPT and PPTX formats
- **Excel**: XLSX format
- **Web**: HTML files and URLs
- **E-book**: EPUB format
- **Images**: Supports OCR text extraction

## Basic Syntax

```bash
markio <command> <file_path> [options]
```

## Command Reference

### PDF Parsing

```bash
# Basic PDF parsing
markio pdf document.pdf

# Parse using VLM engine
markio pdf-vlm document.pdf

# Specify parsing method
markio pdf document.pdf --method auto
```

### Word Document Parsing

```bash
# Parse DOCX file
markio docx document.docx

# Parse DOC file (old format)
markio doc document.doc
```

### PowerPoint Parsing

```bash
# Parse PPTX file
markio pptx presentation.pptx

# Parse PPT file (old format)
markio ppt presentation.ppt
```

### Excel Parsing

```bash
# Parse XLSX file
markio xlsx spreadsheet.xlsx
```

### Web Content Parsing

```bash
# Parse HTML file
markio html page.html

# Parse webpage URL
markio url https://example.com/article
```

### E-book Parsing

```bash
# Parse EPUB file
markio epub book.epub
```

### Image Parsing

```bash
# Parse image file (OCR)
markio image screenshot.png
```

## Common Options

### Output Control

```bash
# Save to specified file
markio pdf document.pdf -o output.md
markio pdf document.pdf --output output.md

# Save parsed content
markio pdf document.pdf -s
markio pdf document.pdf --save

# Combine options
markio pdf document.pdf -s -o result.md
markio docx document.docx --save --output content.md
```

### PDF Specific Options

```bash
# Specify parsing method
markio pdf document.pdf -m auto    # Auto select
markio pdf document.pdf -m ocr     # OCR method
markio pdf document.pdf -m txt     # Text extraction
markio pdf document.pdf --method auto

# Page range
markio pdf document.pdf -st 0 -e 5
markio pdf document.pdf --start 0 --end 5

# Only specify start page
markio pdf document.pdf -st 10
markio pdf document.pdf --start 10

# Save middle content
markio pdf document.pdf -sm
markio pdf document.pdf --save-middle
```

### VLM Engine Options

```bash
# Use VLM engine
markio pdf-vlm document.pdf

# Specify server address
markio pdf-vlm document.pdf -sv http://127.0.0.1:30000
markio pdf-vlm document.pdf --server http://127.0.0.1:30000
```

## Advanced Usage

### Batch Processing

```bash
# Process all files in directory
for file in *.pdf; do
    markio pdf "$file" -s -o "${file%.pdf}.md"
done

# Process multiple formats
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

### Page-by-Page Processing

```bash
# Process large documents by pages
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

### Output Directory Management

```bash
# Create output directory
mkdir -p output_dir

# Save to specified directory
markio pdf document.pdf -s -o output_dir/result.md

# Use environment variable
export MARKIO_OUTPUT_DIR="./outputs"
markio pdf document.pdf -s -o result.md
```

### Debug Mode

```bash
# Enable verbose logging
export MARKIO_LOG_LEVEL=DEBUG
markio pdf document.pdf -s -o debug_output.md

# Save intermediate processing results
markio pdf document.pdf -s -sm -o debug_output.md
```

## Python SDK Usage

If you need to use Markio in Python code, please refer to the following example:

```python
from markio.sdk.markio_sdk import MarkioSDK

# Initialize SDK
sdk = MarkioSDK()

# Parse document
result = await sdk.parse_document(
    file_path="document.pdf",
    save_parsed_content=True,
    output_dir="outputs"
)

print(f"Parsing result: {result['content']}")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MARKIO_OUTPUT_DIR` | `outputs` | Default output directory |
| `MARKIO_LOG_LEVEL` | `INFO` | Log level |
| `MARKIO_PDF_ENGINE` | `pipeline` | PDF parsing engine |

## Troubleshooting

### Common Issues

1. **Unsupported file format**
   - Check if file extension is correct
   - Confirm file is not corrupted

2. **OCR failure**
   - Ensure image quality is clear enough
   - Check if there's sufficient system memory

3. **VLM engine connection failure**
   - Confirm server address is correct
   - Check network connection

### Log Viewing

```bash
# View detailed logs
export MARKIO_LOG_LEVEL=DEBUG
markio pdf document.pdf

# Save logs to file
markio pdf document.pdf 2>&1 | tee markio.log
```

## Performance Optimization

### Batch Processing Optimization

```bash
# Process multiple files in parallel
parallel markio pdf {} -s -o "{.}.md" ::: *.pdf

# Use background tasks
for file in *.pdf; do
    (markio pdf "$file" -s -o "${file%.pdf}.md" &)
done
wait
```

### Memory Optimization

```bash
# Limit concurrent processing count
sem --jobs 2 markio pdf {} -s -o "{.}.md" ::: *.pdf
```

## Updates and Maintenance

```bash
# Check version
markio --version

# Update tool
pip install --upgrade markio

# View help
markio --help
markio pdf --help
```

---

**For more information, please refer to [Markio Project Documentation](https://github.com/Tendo33/markio)** 