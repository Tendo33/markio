# Markio SDK Guide

[Back to README](../README.md) | [中文版本](sdk_usage_zh.md)

## Scope

`markio.sdk.markio_sdk.MarkioSDK` is the high-level Python entrypoint for the current sync parsing surface.

It wraps:

- local parser modules when `api_base_url` is not set
- remote `/v1/parse_*` endpoints when `api_base_url` is set

## Installation

```bash
uv sync
uv pip install -e .
```

## Initialize the SDK

```python
from markio.sdk.markio_sdk import MarkioSDK

sdk = MarkioSDK(output_dir="outputs")
```

Remote mode:

```python
sdk = MarkioSDK(
    output_dir="outputs",
    api_base_url="http://localhost:8000",
    token="<YOUR_JWT>",
    timeout_seconds=180,
)
```

Important:

- all remote `/v1/*` calls require JWT auth
- the SDK automatically sends `Authorization: Bearer <token>` when `token` is set
- local and remote URL parsing now follow the same safety policy

## Return Shape

Each high-level parse method returns a dictionary with:

- `content`
- `file_name`
- `output_path`

`content` is the Markdown or parsed text payload that callers usually care about most.

## Supported Methods

| Method | Notes |
|---|---|
| `parse_pdf()` | Supports `parse_method`, page range, middle-content persistence |
| `parse_pdf_vlm()` | Local VLM parser; remote mode still calls `/v1/parse_pdf_file` |
| `parse_docx()` | DOCX parsing |
| `parse_doc()` | DOC via LibreOffice conversion |
| `parse_pptx()` | PPTX parsing |
| `parse_ppt()` | PPT via LibreOffice conversion |
| `parse_xlsx()` | XLSX parsing |
| `parse_html()` | Local HTML file parsing |
| `parse_url()` | Remote or local URL parsing |
| `parse_epub()` | EPUB parsing |
| `parse_image()` | OCR image parsing |

There are currently **no** `MarkioSDK` façade methods for FASTA or GenBank.

## Examples

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

### Office and image formats

```python
docx_result = await sdk.parse_docx("report.docx", save_parsed_content=True)
pptx_result = await sdk.parse_pptx("slides.pptx", save_parsed_content=True)
xlsx_result = await sdk.parse_xlsx("sheet.xlsx", save_parsed_content=True)
image_result = await sdk.parse_image("scan.png", save_parsed_content=True)
```

### URL parsing

```python
url_result = await sdk.parse_url(
    "https://example.com",
    save_parsed_content=True,
)
```

## Local Mode vs Remote Mode

### Local mode

Pros:

- no running server required
- direct access to local parser capabilities
- easiest for embedded scripts or notebooks

Tradeoffs:

- local machine must have the required parser dependencies
- no task queue, dashboard, or server-managed observability layer

### Remote mode

Pros:

- consistent with deployed API behavior
- central auth, rate limiting, and route-level guards
- useful when the heavy parsing stack is hosted elsewhere

Tradeoffs:

- requires a running server
- requires JWT for all `/v1/*` routes

## URL Parsing Semantics

`parse_url()` is intentionally constrained. Both local and remote modes enforce:

- `http` and `https` only
- redirect validation
- private-network blocking by default
- response-size limits
- timeout limits
- optional domain allowlist

Related environment variables:

- `URL_FETCH_MODE`
- `URL_PROXY_BASE`
- `URL_REQUEST_TIMEOUT_SECONDS`
- `URL_MAX_RESPONSE_BYTES`
- `URL_BLOCK_PRIVATE_NETWORKS`
- `URL_ALLOWED_DOMAINS`
- `URL_MAX_REDIRECTS`

## Working with Results

```python
result = await sdk.parse_docx("report.docx", save_parsed_content=True)

content = result["content"]
file_name = result["file_name"]
output_path = result["output_path"]
```

`output_path` is the SDK-side expected location. In remote mode it is a convenience path under the SDK output directory, not a server-side absolute path.

## Limitations

- No async task API wrapper is exposed from `MarkioSDK`
- No façade methods for FASTA or GenBank
- Remote `parse_pdf_vlm()` currently reuses `/v1/parse_pdf_file` rather than a dedicated VLM endpoint

For async task workflows, use the REST API or the `/console` frontend directly.

## Troubleshooting

### Remote SDK returns `401`

- verify `token`
- verify the server `AUTH_JWT_SECRET`
- verify the token is signed with `HS256`

### Local DOC or PPT parsing fails

Install LibreOffice and ensure `soffice` is available.

### `parse_url()` fails unexpectedly

Check:

- host allowlist settings
- private-network blocking
- redirect target
- response size
- timeout

## Related Docs

- CLI guide: [cli_usage.md](cli_usage.md)
- Console guide: [console_frontend.md](console_frontend.md)
- Biological parsing guide: [biological_data_parsing.md](biological_data_parsing.md)
