# Markio CLI Guide

[Back to README](../README.md) | [中文版本](cli_usage_zh.md)

## Scope

The `markio` CLI is the quickest way to exercise the sync parsing surface from a terminal.

It currently supports:

- PDF and PDF VLM
- DOC / DOCX
- PPT / PPTX
- XLSX
- HTML
- URL
- EPUB
- Image OCR

It does **not** currently expose dedicated FASTA or GenBank subcommands.

## Install

```bash
uv sync
uv pip install -e .
```

Then inspect the available commands:

```bash
markio --help
```

## Command Catalog

| Command | Purpose |
|---|---|
| `markio pdf` | Parse PDF with `auto`, `ocr`, or `txt` |
| `markio pdf-vlm` | Parse PDF through the VLM backend |
| `markio docx` | Parse DOCX |
| `markio doc` | Convert DOC through LibreOffice, then parse |
| `markio pptx` | Parse PPTX |
| `markio ppt` | Convert PPT through LibreOffice, then parse |
| `markio xlsx` | Parse XLSX |
| `markio html` | Parse local HTML |
| `markio url` | Parse a remote URL |
| `markio epub` | Parse EPUB |
| `markio image` | OCR an image |

## Local Mode

Local mode runs parser modules in-process and writes outputs under the SDK output directory when `--save` is enabled.

```bash
markio pdf ./sample.pdf --method auto
markio docx ./report.docx --save
markio url https://example.com
markio image ./scan.png --save
```

### Output behavior

- `--save` asks the parser to persist its normal output/artifacts
- `--output` writes the CLI command result to a specific file path
- You can use both when you want normal parser persistence plus a custom final file

Example:

```bash
markio pdf ./sample.pdf --save --output ./artifacts/sample.md
```

## Remote API Mode

If `--api-base-url` is set, the CLI stops calling local parser modules and sends requests to the FastAPI server instead.

```bash
markio --api-base-url http://localhost:8000 --token <YOUR_JWT> pdf ./sample.pdf --save
markio --api-base-url http://localhost:8000 --token <YOUR_JWT> url https://example.com
```

Environment-based configuration works too:

```bash
export MARKIO_API_BASE_URL=http://localhost:8000
export MARKIO_API_TOKEN=<YOUR_JWT>

markio pdf ./sample.pdf
```

Important:

- every `/v1/*` route requires JWT auth
- remote `markio url` calls `/v1/parse_url`
- local `markio url` calls the local URL parser
- both paths now follow the same URL safety constraints

## Common Examples

### PDF

```bash
markio pdf ./sample.pdf --method auto
markio pdf ./sample.pdf --method ocr --save
markio pdf ./sample.pdf --start 0 --end 9
markio pdf-vlm ./complex.pdf --save --server http://localhost:30000
```

### Office documents

```bash
markio docx ./report.docx --save
markio doc ./legacy.doc --save
markio pptx ./slides.pptx --save
markio ppt ./legacy-slides.ppt --save
markio xlsx ./sheet.xlsx --save
```

### Web and images

```bash
markio html ./page.html --save
markio url https://example.com --save
markio image ./scan.png --save
markio epub ./book.epub --save
```

## URL Safety Notes

`markio url` intentionally does not behave like a raw downloader. By default it enforces:

- `http` and `https` only
- redirect validation
- private and loopback network blocking
- response-size limits
- request timeouts
- optional domain allowlists

Relevant environment variables:

- `URL_FETCH_MODE`
- `URL_PROXY_BASE`
- `URL_REQUEST_TIMEOUT_SECONDS`
- `URL_MAX_RESPONSE_BYTES`
- `URL_BLOCK_PRIVATE_NETWORKS`
- `URL_ALLOWED_DOMAINS`
- `URL_MAX_REDIRECTS`

## Environment Variables

| Variable | Purpose |
|---|---|
| `MARKIO_API_BASE_URL` | Enable remote API mode |
| `MARKIO_API_TOKEN` | JWT sent as `Authorization: Bearer ...` |
| `OUTPUT_DIR` | Default local output directory |
| `LOG_LEVEL` | Logging level |
| `PDF_PARSE_ENGINE` | Default PDF engine |
| `MINERU_DEVICE_MODE` | `cuda`, `cpu`, or `mps` |
| `VLM_SERVER_URL` | Remote VLM server |

## Troubleshooting

### `markio: command not found`

```bash
uv pip install -e .
```

### Remote CLI returns `401`

- confirm `MARKIO_API_TOKEN` or `--token`
- confirm the server has a valid `AUTH_JWT_SECRET`
- confirm the token uses the expected `HS256` secret

### `markio url` is rejected

Likely causes:

- non-HTTP URL
- redirect to a blocked host
- private or loopback address
- response too large
- host not allowed by `URL_ALLOWED_DOMAINS`

### Legacy Office parsing fails

Install LibreOffice and ensure `soffice` is available on `PATH`.

## What the CLI Does Not Cover

- async task submission and queue management
- console workflows
- FASTA and GenBank subcommands

For those, use the REST API, the console, or lower-level parser modules directly.
