# HTTP API

## Route Prefix

All parser and task routes are registered with prefix `/v1` and `Depends(require_auth_user)`.

## Sync Parser Routes

Supported routes include:

- `/v1/parse_file`
- `/v1/parse_pdf_file`
- `/v1/parse_doc_file`
- `/v1/parse_docx_file`
- `/v1/parse_ppt_file`
- `/v1/parse_pptx_file`
- `/v1/parse_xlsx_file`
- `/v1/parse_html_file`
- `/v1/parse_epub_file`
- `/v1/parse_image_file`
- `/v1/parse_url`
- `/v1/parse_fasta_file`
- `/v1/parse_genbank_file`

Keep URL safety behavior aligned across local parser mode, SDK local mode, and remote `/v1/parse_url`.

## Async Task Routes

Task APIs live under `/v1/tasks`:

- submit, list, stats, dashboard, detail
- cancel/retry
- queue health/pause/resume for admin users

Task listing/detail must enforce owner visibility. Queue controls require admin role.

## Static Console

`/console` serves `markio/webapp` when built. If missing, the backend intentionally returns a helper fallback HTML page.
