# Markio CLI Usage Guide

Developer-friendly CLI for document parsing and conversion.

[Back to Main README](../README.md) | [中文CLI指南](cli_usage_zh.md)

---

## Why Use Markio CLI?
- **One command, parse anything:** PDF, Office, HTML, EPUB, Images
- **Batch & Automation:** Process folders or integrate into pipelines
- **Flexible Output:** Save as Markdown, control output location
- **Advanced Engines:** OCR, VLM, text extraction, auto-detection
- **Production Ready:** Error handling, logging, configuration

---

## Quick Start

```bash
# Parse a PDF to Markdown
markio pdf document.pdf -o result.md

# Parse a DOCX file
markio docx document.docx --save --output result.md

# Batch process all PDFs in a folder
for file in *.pdf; do markio pdf "$file" -s -o "${file%.pdf}.md"; done
```

---

## Typical Scenarios

| Scenario         | Command Example                                  |
|------------------|--------------------------------------------------|
| PDF OCR          | markio pdf document.pdf -m ocr                   |
| VLM Engine       | markio pdf-vlm document.pdf                      |
| Page Range       | markio pdf document.pdf -st 0 -e 5               |
| HTML/URL         | markio html page.html / markio url https://...   |
| Image OCR        | markio image screenshot.png                      |
| Save to Dir      | markio pdf document.pdf -s -o output_dir/file.md |
| Legacy Office    | markio doc old.doc -s / markio ppt old.ppt -s    |
| Batch Processing | markio pdf *.pdf -s -o ./results/               |

---

## Advanced Usage

### Complete Command Reference

#### PDF Commands
```bash
# Standard PDF parsing
markio pdf document.pdf

# With OCR method
markio pdf document.pdf -m ocr

# With page range
markio pdf document.pdf -st 5 -e 15

# Save intermediate files for debugging
markio pdf document.pdf -sm -s -o ./debug/

# VLM engine (Vision Language Model)
markio pdf-vlm document.pdf --save

# VLM with custom server
markio pdf-vlm document.pdf -s --server http://localhost:30000
```

#### Office Document Commands
```bash
# Modern formats
markio docx report.docx -s
markio pptx presentation.pptx -s -o ./slides/
markio xlsx spreadsheet.xlsx -s

# Legacy formats (auto-converts to modern)
markio doc old_document.doc -s
markio ppt old_presentation.ppt -s -o ./converted/
```

#### Web Content Commands
```bash
# HTML files
markio html page.html -s -o ./content/

# URLs (web pages)
markio url https://example.com -s -o ./web_content/
```

#### Other Formats
```bash
# EPUB ebooks
markio epub book.epub -s -o ./books/

# Images with OCR
markio image screenshot.png -s
markio image diagram.png -s -o ./ocr_results/
```

### Advanced Operations

- **Parallel Processing:**
  ```bash
  # Using GNU parallel
  parallel markio pdf {} -s -o "{.}.md" ::: *.pdf
  
  # Using xargs
  ls *.pdf | xargs -I {} markio pdf {} -s -o ./results/
  
  # Using find for complex patterns
  find ./documents -name "*.pdf" -exec markio pdf {} -s -o ./converted/ \;
  ```

- **Batch Processing Scripts:**
  ```bash
  # Process all PDFs in directory
  for file in *.pdf; do
      markio pdf "$file" -s -o "./results/${file%.pdf}.md"
  done
  
  # Process with different settings per file type
  for file in *.{pdf,docx,html}; do
      case "${file##*.}" in
          pdf) markio pdf "$file" -s ;;
          docx) markio docx "$file" -s ;;
          html) markio html "$file" -s ;;
      esac
  done
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
  
  # Save intermediate files for analysis
  markio pdf document.pdf -sm -s -o ./debug_intermediate/
  ```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_DIR` | outputs | Default output directory for parsed files |
| `LOG_LEVEL` | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `LOG_DIR` | logs | Directory for log files |
| `PDF_PARSE_ENGINE` | pipeline | PDF parsing method (pipeline, vlm-sglang-engine) |
| `MINERU_DEVICE_MODE` | cuda | MinerU device selection (cuda, cpu, mps) |
| `VLM_SERVER_URL` | - | VLM server endpoint for remote processing |
| `MINERU_MIN_BATCH_INFERENCE_SIZE` | 256 | MinerU batch size for inference |
| `MINERU_VIRTUAL_VRAM_SIZE` | 8192 | Virtual VRAM size in MB |
| `VLM_MEM_FRACTION_STATIC` | 0.5 | VLM memory allocation fraction |

### Configuration Examples

#### Basic Configuration
```bash
# Set output directory
export OUTPUT_DIR=~/Documents/markio_output

# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_DIR=./debug_logs

# Use CPU mode (no GPU)
export MINERU_DEVICE_MODE=cpu
```

#### Performance Optimization
```bash
# GPU acceleration with high memory
export MINERU_DEVICE_MODE=cuda
export MINERU_VIRTUAL_VRAM_SIZE=16384
export MINERU_MIN_BATCH_INFERENCE_SIZE=512

# VLM server configuration
export PDF_PARSE_ENGINE=vlm-sglang-engine
export VLM_SERVER_URL=http://localhost:30000
export VLM_MEM_FRACTION_STATIC=0.7
```

#### Memory-Constrained Systems
```bash
# Conservative memory usage
export MINERU_DEVICE_MODE=cpu
export MINERU_MIN_BATCH_INFERENCE_SIZE=128
export MINERU_VIRTUAL_VRAM_SIZE=4096
export VLM_MEM_FRACTION_STATIC=0.3
```

---

## FAQ & Troubleshooting

### Common CLI Issues

#### Command Not Found
**Issue**: `markio: command not found`
```bash
# Check if markio is installed
pip list | grep markio

# Reinstall in development mode
uv pip install -e .

# Add to PATH (if needed)
export PATH=$PATH:/path/to/markio/package
```

#### Permission Denied
**Issue**: Permission errors when accessing files
```bash
# Check file permissions
ls -la document.pdf

# Use appropriate permissions
chmod 644 document.pdf

# Or run with appropriate user
sudo -u username markio pdf document.pdf
```

#### Memory Issues
**Issue**: Processing fails with memory errors
```bash
# Reduce memory usage
export MINERU_MIN_BATCH_INFERENCE_SIZE=128
export MINERU_VIRTUAL_VRAM_SIZE=4096

# Use CPU mode
export MINERU_DEVICE_MODE=cpu

# Process smaller files first
markio pdf small_file.pdf -s
```

#### VLM Engine Issues
**Issue**: VLM processing fails
```bash
# Check VLM server status
curl http://localhost:30000/health

# Verify server configuration
export VLM_SERVER_URL=http://localhost:30000
export PDF_PARSE_ENGINE=vlm-sglang-engine

# Test with a simple file first
markio pdf-vlm simple.pdf --save
```

#### Large File Processing
**Issue**: Large files take too long or fail
```bash
# Process with page ranges
markio pdf large_file.pdf -st 0 -e 50 -s
markio pdf large_file.pdf -st 51 -e 100 -s

# Save intermediate files for debugging
markio pdf large_file.pdf -sm -s -o ./debug/

# Use batch processing for multiple large files
for file in large*.pdf; do
    markio pdf "$file" -s -o "./results/${file%.pdf}.md"
done
```

#### Output Directory Issues
**Issue**: Cannot save to specified directory
```bash
# Create output directory first
mkdir -p ./results

# Check directory permissions
ls -la ./results/

# Use absolute path
markio pdf document.pdf -s -o /home/user/results/output.md
```

### Performance Tips

#### Batch Processing
```bash
# Process multiple files efficiently
find ./input -name "*.pdf" -print0 | xargs -0 -I {} -P 4 markio pdf {} -s -o ./results/

# Limit parallel processes to avoid memory issues
parallel -j 2 markio pdf {} -s -o "{.}.md" ::: *.pdf
```

#### File Organization
```bash
# Organize output by file type
markio pdf document.pdf -s -o ./pdfs/document.md
markio docx report.docx -s -o ./docs/report.md
markio html page.html -s -o ./web/page.md
```

### Getting Help

#### Debug Information
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_DIR=./debug_logs

# Show help for specific command
markio pdf --help
markio pdf-vlm --help

# Check environment variables
env | grep MARKIO
env | grep MINERU
```

#### System Information
When reporting issues, provide:
- Operating system and version
- Python version (`python --version`)
- Markio version (`pip show markio`)
- Error messages and stack traces
- Sample commands that reproduce the issue

### Resources
- [Project Wiki & FAQ](https://github.com/Tendo33/markio/wiki)
- [GitHub Issues](https://github.com/Tendo33/markio/issues)
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- [Main README](../README.md) for comprehensive documentation
- [中文CLI指南](cli_usage_zh.md) for Chinese documentation
- [SDK Usage Guide](sdk_usage.md) for Python SDK documentation
- [中文SDK指南](sdk_usage_zh.md) for Chinese SDK documentation

**For more information, visit the [Markio Project Documentation](https://github.com/Tendo33/markio)** 