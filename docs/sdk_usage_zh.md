# Markio SDK 使用指南

支持异步文档解析和转换的 Python SDK。

[返回主README](../README_zh.md) | [English SDK Guide](sdk_usage.md)

---

## 功能特点

- **类型安全**: 完整的类型提示和 Pydantic 模型
- **异步支持**: 原生 async/await，高性能处理
- **多格式支持**: 支持所有文档格式，API 一致
- **错误处理**: 全面的错误处理和重试机制
- **元数据提取**: 丰富的元数据和处理信息
- **易于集成**: 简单初始化，直观的方法调用

---

## 快速上手

### 安装
```bash
pip install markio

# 或以开发模式安装
git clone https://github.com/Tendo33/markio.git
cd markio
pip install -e .
```

### 基础用法
```python
import asyncio
from markio.sdk.markio_sdk import MarkioSDK

async def quick_start():
    # 初始化SDK
    sdk = MarkioSDK(base_url="http://localhost:8000")
    
    # 解析PDF文档
    result = await sdk.parse_pdf(
        file_path="document.pdf",
        save_parsed_content=True
    )
    
    print(f"内容: {result['content'][:200]}...")
    print(f"文件: {result['file_name']}")
    print(f"状态: {result['status_code']}")
    
    return result

# 运行
result = asyncio.run(quick_start())
```

---

## SDK功能

### 支持的格式
| 格式 | 方法 | 特性 |
|------|------|------|
| PDF | `parse_pdf()`, `parse_pdf_vlm()` | OCR、VLM、页码范围 |
| DOCX | `parse_docx()` | 现代Word文档 |
| DOC | `parse_doc()` | 传统Word（自动转换） |
| PPTX | `parse_pptx()` | 现代PowerPoint |
| PPT | `parse_ppt()` | 传统PowerPoint（自动转换） |
| XLSX | `parse_xlsx()` | Excel电子表格 |
| HTML | `parse_html()` | HTML文件 |
| URL | `parse_url()` | 网页 |
| EPUB | `parse_epub()` | 电子书 |
| 图片 | `parse_image()` | 图片OCR |

### 核心方法

#### PDF处理
```python
# 标准PDF解析
result = await sdk.parse_pdf(
    file_path="document.pdf",
    parse_method="auto",  # auto, ocr, txt
    save_parsed_content=True,
    save_middle_content=False,
    start_page=0,
    end_page=None
)

# VLM（视觉语言模型）处理
result = await sdk.parse_pdf_vlm(
    file_path="complex.pdf",
    save_parsed_content=True,
    save_middle_content=True,
    start_page=0,
    end_page=10,
    server_url="http://localhost:30000"
)
```

#### Office文档
```python
# 现代Office格式
docx_result = await sdk.parse_docx("report.docx", save_parsed_content=True)
pptx_result = await sdk.parse_pptx("presentation.pptx", save_parsed_content=True)
xlsx_result = await sdk.parse_xlsx("spreadsheet.xlsx", save_parsed_content=True)

# 传统Office格式（自动转换）
doc_result = await sdk.parse_doc("legacy.doc", save_parsed_content=True)
ppt_result = await sdk.parse_ppt("legacy.ppt", save_parsed_content=True)
```

#### 网页内容
```python
# HTML文件
html_result = await sdk.parse_html("page.html", save_parsed_content=True)

# URL（网页）
url_result = await sdk.parse_url("https://example.com", save_parsed_content=True)
```

#### 其他格式
```python
# EPUB电子书
epub_result = await sdk.parse_epub("book.epub", save_parsed_content=True)

# 图片OCR
image_result = await sdk.parse_image("screenshot.png", save_parsed_content=True)
```

---

## 高级用法

### 配置选项
```python
from markio.sdk.markio_sdk import MarkioSDK

# 使用自定义设置初始化
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./processed_documents",
    timeout=300  # 5分钟超时
)

# 配置单个请求设置
result = await sdk.parse_pdf(
    file_path="document.pdf",
    parse_method="auto",
    save_parsed_content=True,
    output_dir="./custom_output",
    start_page=0,
    end_page=10
)
```

### 批量处理
```python
import asyncio
from pathlib import Path

async def batch_process():
    sdk = MarkioSDK(output_dir="./batch_results")
    
    # 定义要处理的文件
    files = [
        ("docs/contract.pdf", "pdf"),
        ("docs/invoice.docx", "docx"),
        ("docs/presentation.pptx", "pptx"),
        ("docs/screenshot.png", "image"),
        ("https://company.com/about", "url")
    ]
    
    # 为每个文件创建任务
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
    
    # 并发处理所有文件
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    successful = 0
    failed = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ {files[i][0]} 失败: {result}")
            failed += 1
        else:
            print(f"✅ {files[i][0]}: {len(result['content'])} 字符")
            successful += 1
    
    print(f"批量处理完成: {successful} 成功, {failed} 失败")
    return results

results = asyncio.run(batch_process())
```

### 错误处理和重试逻辑
```python
import asyncio
from typing import Dict, Any

async def robust_processing():
    sdk = MarkioSDK(output_dir="./robust_results")
    
    async def parse_with_retry(method, file_path: str, max_retries: int = 3) -> Dict[Any]:
        """带重试逻辑的解析"""
        for attempt in range(max_retries):
            try:
                if method == "pdf":
                    return await sdk.parse_pdf(file_path, save_parsed_content=True)
                elif method == "docx":
                    return await sdk.parse_docx(file_path, save_parsed_content=True)
                # 根据需要添加其他方法
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"第 {attempt + 1} 次尝试失败 {file_path}: {e}")
                await asyncio.sleep(2 ** attempt)  # 指数退避
    
    # 使用重试逻辑处理文件
    files = ["doc1.pdf", "doc2.docx", "doc3.pptx"]
    results = []
    
    for file_path in files:
        try:
            method = file_path.split('.')[-1]
            result = await parse_with_retry(method, file_path)
            results.append(result)
            print(f"✅ 成功处理: {file_path}")
        except Exception as e:
            print(f"❌ 重试后仍失败 {file_path}: {e}")
    
    return results
```

### 内存高效处理
```python
import asyncio
from pathlib import Path

async def process_large_file():
    """分块处理大文件"""
    sdk = MarkioSDK(output_dir="./chunked_results")
    
    # 分块处理大PDF
    large_pdf = "large_document.pdf"
    total_pages = 100  # 假设我们知道总页数
    chunk_size = 20
    
    all_content = []
    
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size - 1, total_pages - 1)
        
        print(f"正在处理页码 {start_page}-{end_page}...")
        
        result = await sdk.parse_pdf(
            file_path=large_pdf,
            start_page=start_page,
            end_page=end_page,
            save_parsed_content=True
        )
        
        all_content.append(result['content'])
        
        # 保存中间块
        chunk_filename = f"{Path(large_pdf).stem}_pages_{start_page}-{end_page}.md"
        with open(f"./chunks/{chunk_filename}", "w", encoding="utf-8") as f:
            f.write(result['content'])
    
    # 合并所有块
    combined_content = "\n\n".join(all_content)
    
    # 保存最终结果
    with open(f"./final/{Path(large_pdf).stem}_complete.md", "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    print(f"✅ 成功处理 {len(all_content)} 个块")
    return combined_content
```

### 处理结果
```python
async def process_results():
    sdk = MarkioSDK()
    
    result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    
    # 访问结果的不同部分
    content = result['content']  # Markdown内容
    file_name = result['file_name']  # 原始文件名
    output_path = result['output_path']  # 保存文件路径
    status_code = result['status_code']  # HTTP状态码
    
    # 打印摘要
    print(f"文件: {file_name}")
    print(f"内容长度: {len(content)} 字符")
    print(f"输出保存到: {output_path}")
    print(f"状态: {status_code}")
    
    # 保存内容到自定义位置
    custom_path = f"./custom/{file_name}.md"
    with open(custom_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"自定义副本保存到: {custom_path}")
```

---

## 配置

### 环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MARKIO_BASE_URL` | `http://localhost:8000` | Markio服务器URL |
| `MARKIO_OUTPUT_DIR` | `outputs` | 默认输出目录 |
| `MARKIO_TIMEOUT` | `300` | 请求超时时间（秒） |
| `MARKIO_LOG_LEVEL` | `INFO` | 日志级别 |

### SDK配置
```python
from markio.sdk.markio_sdk import MarkioSDK

# 基础配置
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./my_outputs"
)

# 高级配置
sdk = MarkioSDK(
    base_url="http://localhost:8000",
    output_dir="./processed",
    timeout=600,  # 10分钟
    headers={"Custom-Header": "value"}
)
```

---

## 错误处理

### 常见异常
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
        print(f"请求超时: {e}")
        # 使用更长超时重试
        sdk.timeout = 600
        return await sdk.parse_pdf("document.pdf", save_parsed_content=True)
    except MarkioAPIError as e:
        print(f"API错误: {e.status_code} - {e.message}")
        # 处理特定API错误
        if e.status_code == 413:
            print("文件过大，考虑分块处理")
        elif e.status_code == 422:
            print("无效的文件格式或参数")
        raise
    except Exception as e:
        print(f"未知错误: {e}")
        raise
```

### 验证
```python
from pathlib import Path

def validate_file(file_path: str) -> bool:
    """处理前验证文件"""
    path = Path(file_path)
    
    # 检查文件是否存在
    if not path.exists():
        raise FileNotFoundError(f"文件未找到: {file_path}")
    
    # 检查是否为文件
    if not path.is_file():
        raise ValueError(f"路径不是文件: {file_path}")
    
    # 检查文件大小（可选）
    file_size = path.stat().st_size
    if file_size > 100 * 1024 * 1024:  # 100MB
        print(f"警告: 大文件 ({file_size / 1024 / 1024:.1f}MB)")
    
    return True

async def safe_processing():
    sdk = MarkioSDK()
    
    try:
        # 先验证文件
        validate_file("document.pdf")
        
        # 处理文件
        result = await sdk.parse_pdf("document.pdf", save_parsed_content=True)
        return result
    except (FileNotFoundError, ValueError) as e:
        print(f"验证错误: {e}")
        return None
```

---

## 性能技巧

### 并发处理
```python
import asyncio
from typing import List, Dict

async def concurrent_processing():
    sdk = MarkioSDK(output_dir="./concurrent_results")
    
    # 并发处理多个文件
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    
    # 创建所有任务
    tasks = [
        sdk.parse_pdf(file, save_parsed_content=True)
        for file in files
    ]
    
    # 使用受控的并发运行
    semaphore = asyncio.Semaphore(3)  # 限制为3个并发请求
    
    async def process_with_limit(task):
        async with semaphore:
            return await task
    
    results = await asyncio.gather(*[process_with_limit(task) for task in tasks])
    
    # 处理结果
    for file, result in zip(files, results):
        if isinstance(result, Exception):
            print(f"❌ {file} 失败: {result}")
        else:
            print(f"✅ {file}: {len(result['content'])} 字符")
    
    return results
```

### 内存管理
```python
async def memory_efficient_batch():
    sdk = MarkioSDK(output_dir="./memory_efficient")
    
    # 分小批处理文件以管理内存
    all_files = [f"doc_{i}.pdf" for i in range(100)]
    batch_size = 5
    
    all_results = []
    
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i + batch_size]
        print(f"正在处理批次 {i//batch_size + 1}/{(len(all_files)-1)//batch_size + 1}")
        
        # 处理批次
        tasks = [sdk.parse_pdf(file, save_parsed_content=True) for file in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results.extend(batch_results)
        
        # 可选：批次间添加小延迟
        await asyncio.sleep(1)
    
    return all_results
```

---

## 调试

### 启用调试日志
```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 或配置特定记录器
logger = logging.getLogger("markio.sdk")
logger.setLevel(logging.DEBUG)

# 创建处理器
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### 调试信息
```python
async def debug_example():
    sdk = MarkioSDK()
    
    # 检查SDK配置
    print(f"基础URL: {sdk.base_url}")
    print(f"输出目录: {sdk.output_dir}")
    print(f"超时时间: {sdk.timeout}")
    
    # 测试连接
    try:
        result = await sdk.parse_pdf("test.pdf", save_parsed_content=True)
        print(f"连接成功: {result['status_code']}")
    except Exception as e:
        print(f"连接失败: {e}")
        print(f"错误类型: {type(e)}")
        print(f"错误详情: {str(e)}")
```

---

## FAQ与故障排除

### 常见问题

#### 导入错误
**问题**: `ModuleNotFoundError: No module named 'markio'`
```bash
# 检查安装
pip list | grep markio

# 重新安装
pip install markio

# 或以开发模式安装
pip install -e /path/to/markio
```

#### 连接错误
**问题**: 无法连接到Markio服务器
```python
# 检查服务器状态
import httpx

async def check_server():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"服务器状态: {response.status_code}")
        except Exception as e:
            print(f"服务器无法访问: {e}")

# 验证SDK配置
sdk = MarkioSDK(base_url="http://localhost:8000")
print(f"SDK将连接到: {sdk.base_url}")
```

#### 超时问题
**问题**: 大文件请求超时
```python
# 增加超时时间
sdk = MarkioSDK(timeout=600)  # 10分钟

# 或分小块处理
result = await sdk.parse_pdf(
    "large_file.pdf",
    start_page=0,
    end_page=50,
    save_parsed_content=True
)
```

#### 内存问题
**问题**: 处理期间内存使用过高
```python
# 顺序处理文件而不是并发
for file in files:
    result = await sdk.parse_pdf(file, save_parsed_content=True)
    # 立即处理结果，不要全部存储在内存中

# 使用更小的批次大小
batch_size = 2  # 从默认值减少
```

### 获取帮助

#### 调试信息
报告问题时请提供：
1. Python版本 (`python --version`)
2. Markio版本 (`pip show markio`)
3. 服务器状态和日志
4. 重现问题的示例代码
5. 错误消息和堆栈跟踪

#### 资源链接
- [项目Wiki与FAQ](https://github.com/Tendo33/markio/wiki)
- [GitHub Issues](https://github.com/Tendo33/markio/issues)
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- [主README](../README_zh.md) 获取完整文档
- [英文SDK指南](sdk_usage.md) 获取英文文档

**更多信息请访问 [Markio 项目文档](https://github.com/Tendo33/markio)**