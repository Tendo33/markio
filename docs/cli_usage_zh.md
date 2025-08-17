# Markio CLI 使用指南

一行命令，解析各种文档。

[返回主README](../README_zh.md) | [English CLI Guide](cli_usage.md)

---

## 为什么用Markio CLI？
- **一行命令，解析多格式：** PDF、Office、HTML、EPUB、图片
- **批量与自动化：** 处理文件夹或集成到脚本
- **灵活输出：** Markdown 格式，控制输出位置
- **智能引擎：** OCR、VLM、文本提取，自动识别
- **生产就绪：** 错误处理、日志、配置管理

---

## 快速上手

```bash
# 解析PDF为Markdown
markio pdf document.pdf -o result.md

# 解析DOCX文件
markio docx document.docx --save --output result.md

# 批量处理文件夹下所有PDF
for file in *.pdf; do markio pdf "$file" -s -o "${file%.pdf}.md"; done
```

---

## 典型场景

| 场景         | 命令示例                                         |
|--------------|--------------------------------------------------|
| PDF OCR      | markio pdf document.pdf -m ocr                   |
| VLM引擎      | markio pdf-vlm document.pdf                      |
| 指定页码     | markio pdf document.pdf -st 0 -e 5               |
| HTML/URL     | markio html page.html / markio url https://...   |
| 图片OCR      | markio image screenshot.png                      |
| 输出到目录   | markio pdf document.pdf -s -o output_dir/file.md |
| 旧版Office   | markio doc old.doc -s / markio ppt old.ppt -s    |
| 批量处理     | markio pdf *.pdf -s -o ./results/               |

---

## 进阶用法

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

## 环境变量

| 变量名              | 默认值   | 说明                 |
|---------------------|----------|----------------------|
| OUTPUT_DIR          | outputs  | 默认输出目录         |
| LOG_LEVEL           | INFO     | 日志级别             |
| PDF_PARSE_ENGINE    | pipeline | PDF解析引擎          |
| MINERU_DEVICE_MODE  | cuda     | MinerU设备选择       |
| VLM_SERVER_URL      | -        | VLM服务端点          |

---

## FAQ与常见问题

### 常见CLI问题

#### 命令未找到
**问题**: `markio: command not found`
```bash
# 检查markio是否安装
pip list | grep markio

# 重新安装开发模式
uv pip install -e .

# 添加到PATH（如果需要）
export PATH=$PATH:/path/to/markio/package
```

#### 权限错误
**问题**: 访问文件时出现权限错误
```bash
# 检查文件权限
ls -la document.pdf

# 使用适当权限
chmod 644 document.pdf

# 或使用适当用户运行
sudo -u username markio pdf document.pdf
```

#### 内存问题
**问题**: 处理失败并出现内存错误
```bash
# 减少内存使用
export MINERU_MIN_BATCH_INFERENCE_SIZE=128
export MINERU_VIRTUAL_VRAM_SIZE=4096

# 使用CPU模式
export MINERU_DEVICE_MODE=cpu

# 先处理小文件
markio pdf small_file.pdf -s
```

#### VLM引擎问题
**问题**: VLM处理失败
```bash
# 检查VLM服务器状态
curl http://localhost:30000/health

# 验证服务器配置
export VLM_SERVER_URL=http://localhost:30000
export PDF_PARSE_ENGINE=vlm-sglang-engine

# 先用简单文件测试
markio pdf-vlm simple.pdf --save
```

#### 大文件处理
**问题**: 大文件处理时间过长或失败
```bash
# 使用页码范围处理
markio pdf large_file.pdf -st 0 -e 50 -s
markio pdf large_file.pdf -st 51 -e 100 -s

# 保存中间文件用于调试
markio pdf large_file.pdf -sm -s -o ./debug/

# 批量处理多个大文件
for file in large*.pdf; do
    markio pdf "$file" -s -o "./results/${file%.pdf}.md"
done
```

#### 输出目录问题
**问题**: 无法保存到指定目录
```bash
# 先创建输出目录
mkdir -p ./results

# 检查目录权限
ls -la ./results/

# 使用绝对路径
markio pdf document.pdf -s -o /home/user/results/output.md
```

### 性能技巧

#### 批量处理
```bash
# 高效处理多个文件
find ./input -name "*.pdf" -print0 | xargs -0 -I {} -P 4 markio pdf {} -s -o ./results/

# 为避免内存问题限制并行进程数
parallel -j 2 markio pdf {} -s -o "{.}.md" ::: *.pdf
```

#### 文件组织
```bash
# 按文件类型组织输出
markio pdf document.pdf -s -o ./pdfs/document.md
markio docx report.docx -s -o ./docs/report.md
markio html page.html -s -o ./web/page.md
```

### 获取帮助

#### 调试信息
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
export LOG_DIR=./debug_logs

# 显示特定命令的帮助
markio pdf --help
markio pdf-vlm --help

# 检查环境变量
env | grep MARKIO
env | grep MINERU
```

#### 系统信息
报告问题时请提供：
- 操作系统和版本
- Python版本 (`python --version`)
- Markio版本 (`pip show markio`)
- 错误消息和堆栈跟踪
- 重现问题的示例命令

### 资源链接
- [项目Wiki与FAQ](https://github.com/Tendo33/markio/wiki)
- [GitHub Issues](https://github.com/Tendo33/markio/issues)
- [GitHub Discussions](https://github.com/Tendo33/markio/discussions)
- [主README](../README_zh.md) 获取完整文档
- [英文CLI指南](cli_usage.md) 获取英文文档
- [SDK使用指南](sdk_usage_zh.md) 获取Python SDK文档
- [英文SDK指南](sdk_usage.md) 获取英文SDK文档

**更多信息请参考 [Markio 项目文档](https://github.com/Tendo33/markio)**