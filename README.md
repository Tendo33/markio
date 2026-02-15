<img src="assets/image.png" alt="Markio Logo" height="300" style="display:block;margin:auto;">

> **Markio**: enterprise-lite document parsing platform powered by **docling + MinerU**.

<div align="center">

### 🌍 Language / 语言

**English** | [中文](README_zh.md)

</div>

---

## What Markio Is

Markio provides a unified FastAPI service for converting multiple document formats to Markdown and structured text.

This refactor focuses on:

- latest MinerU-compatible parsing flow
- async task queue with retry/cancel/pause/resume
- Redis cache for task result reuse
- OpenAI-style web console at `/console`

## Current Scope (after refactor)

- Keep: docling + MinerU document processing
- Keep: synchronous parse endpoints (`/v1/parse_*`)
- Add: async task endpoints (`/v1/tasks/*`)
- Add: queue management and dashboard APIs
- Add: Vue console frontend served by FastAPI static files
- Exclude: GPU load balancing, heavy auth/user center, extra Tianshu-only modality stack

---

## Quick Start

### 1) Local

```bash
git clone https://github.com/Tendo33/markio.git
cd markio

uv sync
uv pip install -e .

python markio/main.py
```

Open:

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Console: [http://localhost:8000/console](http://localhost:8000/console)

### 2) Docker

```bash
docker compose up -d
```

Then open the same URLs as above.

---

## Async Task API

Base path: `/v1/tasks`

| Endpoint | Method | Purpose |
|---|---|---|
| `/submit` | POST | Submit file as async task |
| `/` | GET | List tasks with pagination/filter |
| `/{task_id}` | GET | Get task detail |
| `/dashboard` | GET | Dashboard summary + recent tasks |
| `/queue` | GET | Queue health |
| `/queue/pause` | POST | Pause queue |
| `/queue/resume` | POST | Resume queue |
| `/{task_id}/cancel` | POST | Cancel pending task |
| `/{task_id}/retry` | POST | Retry failed/canceled task |

Example:

```bash
curl -X POST "http://localhost:8000/v1/tasks/submit" \
  -F "file=@./sample.pdf" \
  -F "parse_method=auto" \
  -F "lang=ch" \
  -F "priority=5"
```

---

## Frontend Console (OpenAI-style)

The new console frontend source is under `frontend/` and outputs static assets to `markio/webapp/`.

Build manually:

```bash
cd frontend
npm install
npm run build
```

More details:

- [docs/console_frontend.md](docs/console_frontend.md)
- [docs/console_frontend_zh.md](docs/console_frontend_zh.md)

---

## Key Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PDF_PARSE_ENGINE` | `pipeline` | PDF engine mode |
| `MINERU_DEVICE_MODE` | `cuda` | MinerU device (`cuda/cpu/mps`) |
| `REDIS_ENABLED` | `false` | Enable Redis cache |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `TASK_WORKER_COUNT` | `2` | Async workers |
| `TASK_QUEUE_BACKEND` | `memory` | Task queue backend (`memory/redis`) |
| `TASK_HISTORY_LIMIT` | `500` | In-memory task history size |
| `TASK_STATE_FILE` | `data/task_state.json` | Persisted task state path |
| `TASK_UPLOAD_DIR` | `data/task_uploads` | Uploaded file temp dir |
| `TASK_MAX_AUTO_RETRIES` | `0` | Max auto retries |
| `TASK_RETRY_DELAY_SECONDS` | `0` | Retry delay |
| `TASK_PROCESSING_TIMEOUT_SECONDS` | `0` | Processing timeout before requeue |

See `.env.example` for full config template.

---

## Documentation

- CLI usage: [docs/cli_usage.md](docs/cli_usage.md)
- SDK usage: [docs/sdk_usage.md](docs/sdk_usage.md)
- Redis integration: [docs/REDIS_INTEGRATION.md](docs/REDIS_INTEGRATION.md)
- Frontend console: [docs/console_frontend.md](docs/console_frontend.md)

---

## License

Markio is MIT licensed. See [LICENSE](LICENSE).

The frontend includes adapted third-party code from `mineru-tianshu` (Apache-2.0).
See: `frontend/THIRD_PARTY_NOTICES.md`.
