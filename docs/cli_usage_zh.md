# Markio CLI 使用指南

[返回 README](../README.zh.md) | [English Version](cli_usage.md)

## 适用范围

`markio` CLI 是从终端直接调用同步解析能力的最快方式。

当前支持：

- PDF 与 PDF VLM
- DOC / DOCX
- PPT / PPTX
- XLSX
- HTML
- URL
- EPUB
- 图片 OCR

当前**不提供** FASTA 与 GenBank 的专用 CLI 子命令。

## 安装

```bash
uv sync
uv pip install -e .
```

查看命令：

```bash
markio --help
```

## 命令一览

| 命令 | 作用 |
|---|---|
| `markio pdf` | 用 `auto`、`ocr` 或 `txt` 解析 PDF |
| `markio pdf-vlm` | 使用 VLM 后端解析 PDF |
| `markio docx` | 解析 DOCX |
| `markio doc` | 通过 LibreOffice 转换 DOC 后再解析 |
| `markio pptx` | 解析 PPTX |
| `markio ppt` | 通过 LibreOffice 转换 PPT 后再解析 |
| `markio xlsx` | 解析 XLSX |
| `markio html` | 解析本地 HTML |
| `markio url` | 解析远程 URL |
| `markio epub` | 解析 EPUB |
| `markio image` | 对图片做 OCR |

## 本地模式

本地模式会直接在当前进程内调用 parser 模块；当使用 `--save` 时，解析器会把常规输出写入本地输出目录。

```bash
markio pdf ./sample.pdf --method auto
markio docx ./report.docx --save
markio url https://example.com
markio image ./scan.png --save
```

### 输出行为

- `--save`：要求解析器按其常规方式持久化输出或附属资源
- `--output`：把当前命令的结果额外写到指定文件
- 两者可以同时使用

示例：

```bash
markio pdf ./sample.pdf --save --output ./artifacts/sample.md
```

## 远程 API 模式

只要设置了 `--api-base-url`，CLI 就不再直接调本地 parser，而是向 FastAPI 服务发送请求。

```bash
markio --api-base-url http://localhost:8000 --token <YOUR_JWT> pdf ./sample.pdf --save
markio --api-base-url http://localhost:8000 --token <YOUR_JWT> url https://example.com
```

也可以通过环境变量配置：

```bash
export MARKIO_API_BASE_URL=http://localhost:8000
export MARKIO_API_TOKEN=<YOUR_JWT>

markio pdf ./sample.pdf
```

注意：

- 所有 `/v1/*` 路由都要求 JWT
- 远程 `markio url` 实际调用 `/v1/parse_url`
- 本地 `markio url` 调用本地 URL parser
- 两条路径现在共享同一套 URL 安全边界

## 常见示例

### PDF

```bash
markio pdf ./sample.pdf --method auto
markio pdf ./sample.pdf --method ocr --save
markio pdf ./sample.pdf --start 0 --end 9
markio pdf-vlm ./complex.pdf --save --server http://localhost:30000
```

### Office 文档

```bash
markio docx ./report.docx --save
markio doc ./legacy.doc --save
markio pptx ./slides.pptx --save
markio ppt ./legacy-slides.ppt --save
markio xlsx ./sheet.xlsx --save
```

### Web 与图片

```bash
markio html ./page.html --save
markio url https://example.com --save
markio image ./scan.png --save
markio epub ./book.epub --save
```

## URL 安全说明

`markio url` 不是一个裸下载器。默认会强制：

- 仅允许 `http` 与 `https`
- redirect 目标再次校验
- 默认阻断私网、回环、链路本地等地址
- 限制响应大小
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

## 环境变量

| 变量 | 作用 |
|---|---|
| `MARKIO_API_BASE_URL` | 启用远程 API 模式 |
| `MARKIO_API_TOKEN` | 作为 `Authorization: Bearer ...` 发送的 JWT |
| `OUTPUT_DIR` | 默认本地输出目录 |
| `LOG_LEVEL` | 日志级别 |
| `PDF_PARSE_ENGINE` | 默认 PDF 引擎 |
| `MINERU_DEVICE_MODE` | `cuda`、`cpu` 或 `mps` |
| `VLM_SERVER_URL` | 远程 VLM 服务地址 |

## 故障排查

### `markio: command not found`

```bash
uv pip install -e .
```

### 远程 CLI 返回 `401`

- 检查 `MARKIO_API_TOKEN` 或 `--token`
- 检查服务端是否设置了有效的 `AUTH_JWT_SECRET`
- 检查 token 是否使用相同的 `HS256` 密钥签发

### `markio url` 被拒绝

常见原因：

- 不是 HTTP URL
- redirect 指向被阻断目标
- 指向私网或回环地址
- 响应过大
- 不在 `URL_ALLOWED_DOMAINS` 白名单中

### 旧版 Office 解析失败

请安装 LibreOffice，并确认 `soffice` 在 `PATH` 中可用。

## CLI 当前不覆盖的能力

- 异步任务提交与队列管理
- 控制台工作流
- FASTA 与 GenBank 子命令

这些场景请使用 REST API、console 或更底层的 parser 模块。
