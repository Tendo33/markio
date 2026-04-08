# Markio SDK 使用指南

[返回 README](../README.zh.md) | [English Version](sdk_usage.md)

## 适用范围

`markio.sdk.markio_sdk.MarkioSDK` 是当前同步解析能力的高层 Python 入口。

它会在两种模式间切换：

- 未设置 `api_base_url` 时，直接调用本地 parser 模块
- 设置了 `api_base_url` 时，改为调用远程 `/v1/parse_*` 接口

## 安装

```bash
uv sync
uv pip install -e .
```

## 初始化 SDK

```python
from markio.sdk.markio_sdk import MarkioSDK

sdk = MarkioSDK(output_dir="outputs")
```

远程模式：

```python
sdk = MarkioSDK(
    output_dir="outputs",
    api_base_url="http://localhost:8000",
    token="<YOUR_JWT>",
    timeout_seconds=180,
)
```

注意：

- 所有远程 `/v1/*` 调用都需要 JWT
- 只要设置了 `token`，SDK 会自动附带 `Authorization: Bearer <token>`
- 本地与远程 `parse_url()` 现在遵循同一套 URL 安全约束

## 返回结构

每个高层解析方法都会返回一个字典，包含：

- `content`
- `file_name`
- `output_path`

其中 `content` 一般是调用方最关心的 Markdown 或解析结果。

## 当前支持的方法

| 方法 | 说明 |
|---|---|
| `parse_pdf()` | 支持 `parse_method`、页码范围与中间产物保存 |
| `parse_pdf_vlm()` | 本地 VLM 解析；远程模式仍调用 `/v1/parse_pdf_file` |
| `parse_docx()` | 解析 DOCX |
| `parse_doc()` | 通过 LibreOffice 转换 DOC 后解析 |
| `parse_pptx()` | 解析 PPTX |
| `parse_ppt()` | 通过 LibreOffice 转换 PPT 后解析 |
| `parse_xlsx()` | 解析 XLSX |
| `parse_html()` | 解析本地 HTML 文件 |
| `parse_url()` | 解析远程 URL |
| `parse_epub()` | 解析 EPUB |
| `parse_image()` | OCR 图片 |

当前 **没有** FASTA 或 GenBank 的 `MarkioSDK` façade 方法。

## 示例

### PDF

```python
import asyncio
from markio.sdk.markio_sdk import MarkioSDK

async def main():
    sdk = MarkioSDK(output_dir="outputs")
    result = await sdk.parse_pdf(
        file_path="sample.pdf",
        parse_method="auto",
        save_parsed_content=True,
        save_middle_content=False,
        start_page=0,
        end_page=9,
    )
    print(result["content"][:500])

asyncio.run(main())
```

### PDF VLM

```python
result = await sdk.parse_pdf_vlm(
    file_path="complex.pdf",
    save_parsed_content=True,
    start_page=0,
    end_page=4,
    server_url="http://localhost:30000",
)
```

### Office 与图片

```python
docx_result = await sdk.parse_docx("report.docx", save_parsed_content=True)
pptx_result = await sdk.parse_pptx("slides.pptx", save_parsed_content=True)
xlsx_result = await sdk.parse_xlsx("sheet.xlsx", save_parsed_content=True)
image_result = await sdk.parse_image("scan.png", save_parsed_content=True)
```

### URL 解析

```python
url_result = await sdk.parse_url(
    "https://example.com",
    save_parsed_content=True,
)
```

## 本地模式与远程模式

### 本地模式

优点：

- 不依赖运行中的服务
- 直接获得本地 parser 能力
- 适合脚本与 notebook 集成

代价：

- 本机必须具备对应解析依赖
- 不提供任务队列、dashboard 或服务端可观测能力

### 远程模式

优点：

- 与部署后的 API 行为一致
- 统一走服务端鉴权、限流和路由守卫
- 适合将重解析能力放在独立服务节点上

代价：

- 需要运行中的服务
- 所有 `/v1/*` 路由都要 JWT

## URL 解析语义

`parse_url()` 不是无约束抓取器。本地与远程模式都会强制：

- 仅允许 `http` 与 `https`
- redirect 目标再次校验
- 默认阻断私网地址
- 限制响应体大小
- 限制请求超时
- 支持可选域名白名单

相关环境变量：

- `URL_FETCH_MODE`
- `URL_PROXY_BASE`
- `URL_REQUEST_TIMEOUT_SECONDS`
- `URL_MAX_RESPONSE_BYTES`
- `URL_BLOCK_PRIVATE_NETWORKS`
- `URL_ALLOWED_DOMAINS`
- `URL_MAX_REDIRECTS`

## 如何处理结果

```python
result = await sdk.parse_docx("report.docx", save_parsed_content=True)

content = result["content"]
file_name = result["file_name"]
output_path = result["output_path"]
```

`output_path` 是 SDK 侧的预期路径。在远程模式下，它只是 SDK 输出目录下的便捷路径，不代表服务端真实绝对路径。

## 当前边界

- `MarkioSDK` 没有暴露异步任务 API wrapper
- 没有 FASTA 与 GenBank façade 方法
- 远程 `parse_pdf_vlm()` 当前仍复用 `/v1/parse_pdf_file`

如果你需要异步任务工作流，请直接使用 REST API 或 `/console`。

## 故障排查

### 远程 SDK 返回 `401`

- 检查 `token`
- 检查服务端 `AUTH_JWT_SECRET`
- 检查 token 是否用 `HS256` 签发

### 本地 DOC / PPT 解析失败

请安装 LibreOffice，并确认 `soffice` 可用。

### `parse_url()` 异常失败

重点检查：

- 域名白名单
- 私网阻断配置
- redirect 目标
- 响应大小
- 超时

## 相关文档

- CLI 指南：[cli_usage_zh.md](cli_usage_zh.md)
- Console 指南：[console_frontend_zh.md](console_frontend_zh.md)
- 生物数据解析指南：[biological_data_parsing_zh.md](biological_data_parsing_zh.md)
