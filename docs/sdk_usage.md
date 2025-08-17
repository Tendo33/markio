# Markio SDK Usage Guide

Python SDK for document parsing and conversion with async support.

[Back to Main README](../README.md) | [中文SDK指南](sdk_usage_zh.md)

---

## Features

- **Type-safe**: Full type hints and Pydantic models
- **Async support**: Native async/await for high performance
- **Multi-format**: Support for all document formats with consistent API
- **Error handling**: Comprehensive error handling and retry mechanisms
- **Metadata extraction**: Rich metadata and processing information
- **Easy integration**: Simple initialization and intuitive methods

---

## Quick Start

### Installation
```bash
pip install markio

# Or install in development mode
git clone https://github.com/Tendo33/markio.git
cd markio
pip install -e .
```

### Basic Usage
```python
import asyncio
from markio.sdk.markio_sdk import MarkioSDK

async def quick_start():
    # Initialize SDK
    sdk = MarkioSDK(base_url="http://localhost:8000")
    
    # Parse a PDF document
    result = await sdk.parse_pdf(
        file_path="document.pdf",
        save_parsed_content=True
    )
    
    print(f"Content: {result['content'][:200]}...")
    print(f"File: {result['file_name']}")
    print(f"Status: {result['status_code']}")
    
    return result

# Run
result = asyncio.run(quick_start())
```

---

## SDK Features

### Supported Formats
| Format | Methods | Features |
|--------|---------|----------|
| PDF | `parse_pdf()`, `parse_pdf_vlm()` | OCR, VLM, page ranges |
| DOCX | `parse_docx()` | Modern Word documents |
| DOC | `parse_doc()` | Legacy Word (auto-convert) |
| PPTX | `parse_pptx()` | Modern PowerPoint |
| PPT | `parse_ppt()` | Legacy PowerPoint (auto-convert) |
| XLSX | `parse_xlsx()` | Excel spreadsheets |
| HTML | `parse_html()` | HTML files |
| URL | `parse_url()` | Web pages |
| EPUB | `parse_epub()` | Ebooks |
| Image | `parse_image()` | OCR for images |

### Core Methods

#### PDF Processing
```python
# Standard PDF parsing
result = await sdk.parse_pdf(
    file_path="document.pdf",
    parse_method="auto",  # auto, ocr, txt
    save_parsed_content=True,
    save_middle_content=False,
    start_page=0,
    end_page=None
)

# VLM (Vision Language Model) processing
result = await sdk.parse_pdf_vlm(
    file_path="complex.pdf",
    save_parsed_content=True,
    save_middle_content=True,
    start_page=0,
    end_page=10,
    server_url="http://localhost:30000"
)
```

#### Office Documents
```python
# Modern Office formats
docx_result = await sdk.parse_docx("report.docx", save_parsed_content=True)
pptx_result = await sdk.parse_pptx("presentation.pptx", save_parsed_content=True)
xlsx_result = await sdk.parse_xlsx("spreadsheet.xlsx", save_parsed_content=True)

# Legacy Office formats (auto-conversion)
doc_result = await sdk.parse_doc("legacy.doc", save_parsed_content=True)
ppt_result = await sdk.parse_ppt("legacy.ppt", save_parsed_content=True)
```

#### Web Content
```python
# HTML files
html_result = await sdk.parse_html("page.html", save_parsed_content=True)

# URLs (web pages)
url_result = await sdk.parse_url("https://example.com", save_parsed_content=True)
```

#### Other Formats
```python
# EPUB ebooks
epub_result = await sdk.parse_epub("book.epub", save_parsed_content=True)

# Images with OCR
image_result = await sdk.parse_image("screenshot.png", save_parsed_content=True)
```

---

## Advanced Usage

### Configuration Options
```python
from markio.sdk.markio_sdk import MarkioSDK

# Initialize with custom settings
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./processed_documents",
    timeout=300  # 5 minutes timeout
)

# Configure per-request settings
result = await sdk.parse_pdf(
    file_path="document.pdf",
    parse_method="auto",
    save_parsed_content=True,
    output_dir="./custom_output",
    start_page=0,
    end_page=10
)
```

### Batch Processing
```python
import asyncio
from pathlib import Path

async def batch_process():
    sdk = MarkioSDK(output_dir="./batch_results")
    
    # Define files to process
    files = [
        ("docs/contract.pdf", "pdf"),
        ("docs/invoice.docx", "docx"),
        ("docs/presentation.pptx", "pptx"),
        ("docs/screenshot.png", "image"),
        ("https://company.com/about", "url")
    ]
    
    # Create tasks for each file
    tasks = []
    for file_path, file_type in files:
        if file_type == "pdf":
            task = sdk.parse_pdf(file_path, save_parsed_content=True)
        elif file_type == "docx":
            task = sdk.parse_docx(file_path, save_parsed_content=True)
        elif file_type == "pptx":
            task = sdk.parse_pptx(file_path, save_parsed_content=True)
        elif file_type == "image":
            task = sdk.parse_image(file_path, save_parsed_content=True)
        elif file_type == "url":
            task = sdk.parse_url(file_path, save_parsed_content=True)
        tasks.append(task)
    
    # Process all files concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = 0
    failed = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ {files[i][0]} failed: {result}")
            failed += 1
        else:
            print(f"✅ {files[i][0]}: {len(result['content'])} chars")
            successful += 1
    
    print(f"Batch complete: {successful} successful, {failed} failed")
    return results

results = asyncio.run(batch_process())
```

### Error Handling and Retry Logic
```python
import asyncio
from typing import Dict, Any

async def robust_processing():
    sdk = MarkioSDK(output_dir="./robust_results")
    
    async def parse_with_retry(method, file_path: str, max_retries: int = 3) -> Dict[Any]:
        """Parse with retry logic"""
        for attempt in range(max_retries):
            try:
                if method == "pdf":
                    return await sdk.parse_pdf(file_path, save_parsed_content=True)
                elif method == "docx":
                    return await sdk.parse_docx(file_path, save_parsed_content=True)
                # Add other methods as needed
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed for {file_path}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Process files with retry logic
    files = ["doc1.pdf", "doc2.docx", "doc3.pptx"]
    results = []
    
    for file_path in files:
        try:
            method = file_path.split('.')[-1]
            result = await parse_with_retry(method, file_path)
            results.append(result)
            print(f"✅ Successfully processed: {file_path}")
        except Exception as e:
            print(f"❌ Failed to process {file_path} after retries: {e}")
    
    return results
```

### Memory-Efficient Processing
```python
import asyncio
from pathlib import Path

async def process_large_file():
    """Process large files in chunks"""
    sdk = MarkioSDK(output_dir="./chunked_results")
    
    # Process large PDF in chunks
    large_pdf = "large_document.pdf"
    total_pages = 100  # Assume we know total pages
    chunk_size = 20
    
    all_content = []
    
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size - 1, total_pages - 1)
        
        print(f"Processing pages {start_page}-{end_page}...")
        
        result = await sdk.parse_pdf(
            file_path=large_pdf,
            start_page=start_page,
            end_page=end_page,
            save_parsed_content=True
        )
        
        all_content.append(result['content'])
        
        # Save intermediate chunk
        chunk_filename = f"{Path(large_pdf).stem}_pages_{start_page}-{end_page}.md"
        with open(f"./chunks/{chunk_filename}", "w", encoding="utf-8") as f:
            f.write(result['content'])
    
    # Combine all chunks
    combined_content = "\n\n".join(all_content)
    
    # Save final result
    with open(f"./final/{Path(large_pdf).stem}_complete.md", "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    print(f"✅ Processed {len(all_content)} chunks successfully")
    return combined_content
```

### Working with Results
```python
async def process_results():
    sdk = MarkioSDK()
    
    result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    
    # Access different parts of the result
    content = result['content']  # Markdown content
    file_name = result['file_name']  # Original filename
    output_path = result['output_path']  # Path to saved file
    status_code = result['status_code']  # HTTP status code
    
    # Print summary
    print(f"File: {file_name}")
    print(f"Content length: {len(content)} characters")
    print(f"Output saved to: {output_path}")
    print(f"Status: {status_code}")
    
    # Save content to custom location
    custom_path = f"./custom/{file_name}.md"
    with open(custom_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Custom copy saved to: {custom_path}")
```

---

## Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `MARKIO_BASE_URL` | `http://localhost:8000` | Markio server URL |
| `MARKIO_OUTPUT_DIR` | `outputs` | Default output directory |
| `MARKIO_TIMEOUT` | `300` | Request timeout in seconds |
| `MARKIO_LOG_LEVEL` | `INFO` | Logging level |

### SDK Configuration
```python
from markio.sdk.markio_sdk import MarkioSDK

# Basic configuration
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./my_outputs"
)

# Advanced configuration
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./processed",
    timeout=600,  # 10 minutes
    headers={"Custom-Header": "value"}
)
```

---

## Error Handling

### Common Exceptions
```python
import asyncio
from markio.sdk.markio_sdk import MarkioSDK
from markio.sdk.exceptions import MarkioAPIError, MarkioTimeoutError

async def error_handling_example():
    sdk = MarkioSDK()
    
    try:
        result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
        return result
    except MarkioTimeoutError as e:
        print(f"Request timed out: {e}")
        # Retry with longer timeout
        sdk.timeout = 600
        return await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    except MarkioAPIError as e:
        print(f"API error: {e.status_code} - {e.message}")
        # Handle specific API errors
        if e.status_code == 413:
            print("File too large, consider processing in chunks")
        elif e.status_code == 422:
            print("Invalid file format or parameters")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
```

### Validation
```python
from pathlib import Path

def validate_file(file_path: str) -> bool:
    """Validate file before processing"""
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check if file is readable
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Check file size (optional)
    file_size = path.stat().st_size
    if file_size > 100 * 1024 * 1024:  # 100MB
        print(f"Warning: Large file ({file_size / 1024 / 1024:.1f}MB)")
    
    return True

async def safe_processing():
    sdk = MarkioSDK()
    
    try:
        # Validate file first
        validate_file("document.pdf")
        
        # Process file
        result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
        return result
    except (FileNotFoundError, ValueError) as e:
        print(f"Validation error: {e}")
        return None
```

---

## Performance Tips

### Concurrent Processing
```python
import asyncio
from typing import List, Dict

async def concurrent_processing():
    sdk = MarkioSDK(output_dir="./concurrent_results")
    
    # Process multiple files concurrently
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    
    # Create all tasks
    tasks = [
        sdk.parse_pdf(file, save_parsed_content=True)
        for file in files
    ]
    
    # Run concurrently with controlled concurrency
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
    
    async def process_with_limit(task):
        async with semaphore:
            return await task
    
    results = await asyncio.gather(*[process_with_limit(task) for task in tasks])
    
    # Process results
    for file, result in zip(files, results):
        if isinstance(result, Exception):
            print(f"❌ {file} failed: {result}")
        else:
            print(f"✅ {file}: {len(result['content'])} chars")
    
    return results
```

### Memory Management
```python
async def memory_efficient_batch():
    sdk = MarkioSDK(output_dir="./memory_efficient")
    
    # Process files in small batches to manage memory
    all_files = [f"doc_{i}.pdf" for i in range(100)]
    batch_size = 5
    
    all_results = []
    
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(all_files)-1)//batch_size + 1}")
        
        # Process batch
        tasks = [sdk.parse_pdf(file, save_parsed_content=True) for file in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results.extend(batch_results)
        
        # Optional: add small delay between batches
        await asyncio.sleep(1)
    
    return all_results
```

---

## Debugging

### Enable Debug Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger("markio.sdk")
logger.setLevel(logging.DEBUG)

# Create handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Debug Information
```python
async def debug_example():
    sdk = MarkioSDK()
    
    # Check SDK configuration
    print(f"Base URL: {sdk.base_url}")
    print(f"Output directory: {sdk.output_dir}")
    print(f"Timeout: {sdk.timeout}")
    
    # Test connection
    try:
        result = await sdk.parse_pdf("test.pdf", save_parsed_content=True)
        print(f"Connection successful: {result['status_code']}")
    except Exception as e:
        print(f"Connection failed: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
```

---

## FAQ & Troubleshooting

### Common Issues

#### Import Errors
**Issue**: `ModuleNotFoundError: No module named 'markio'`
```bash
# Check installation
pip list | grep markio

# Reinstall
pip install markio

# Or install in development mode
pip install -e /path/to/markio
```

#### Connection Errors
**Issue**: Failed to connect to Markio server
```python
# Check server status
import httpx

async def check_server():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"Server status: {response.status_code}")
        except Exception as e:
            print(f"Server not reachable: {e}")

# Verify SDK configuration
sdk = MarkioSDK(base_url="http://localhost:8000")
print(f"SDK will connect to: {sdk.base_url}")
```

#### Timeout Issues
**Issue**: Requests timing out for large files
```python
# Increase timeout
sdk = MarkioSDK(timeout=600)  # 10 minutes

# Or process in smaller chunks
result = await sdk.parse_pdf(
    "large_file.pdf",
    start_page=0,
    end_page=50,
    save_parsed_content=True
)
```

#### Memory Issues
**Issue**: High memory usage during processing
```python
# Process files sequentially instead of concurrently
for file in files:
    result = await sdk.parse_pdf(file, save_parsed_content=True)
    # Process result immediately, don't store all in memory

# Use smaller batch sizes
batch_size = 2  # Reduce from default
```

### Getting Help

#### Debug Information
When reporting issues, provide:
1. Python version (`python --version`)
2. Markio version (`pip show markio`)
3. Server status and logs
4. Sample code that reproduces the issue
5. Error messages and stack traces

#### Resources
- [Project Wiki & FAQ](https://github.com/Tendo33/markio/wiki)
- [GitHub Issues](https://github.com/Tendo33/markio/issues)
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- [Main README](../README.md) for comprehensive documentation
- [中文SDK指南](sdk_usage_zh.md) for Chinese documentation

**For more information, visit the [Markio Project Documentation](https://github.com/Tendo33/markio)**