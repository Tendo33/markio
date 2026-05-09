# Dependencies

## Backend

- Python `>=3.11`
- FastAPI, Uvicorn, Pydantic-style schemas, JWT auth helpers
- Docling, MinerU, Pandoc/LibreOffice helpers, Biopython parsers, URL parsing utilities
- Optional Redis via `redis[hiredis]`
- Pytest and pytest-asyncio for tests

## Frontend

- Vue 3.5, TypeScript 5.9, Vite 7
- Tailwind CSS 4 through `@tailwindcss/vite`
- Pinia, Vue Router, Axios, Day.js, and `lucide-vue-next`
- npm with `frontend/package-lock.json`

## Commands

```bash
uv sync
uv run pytest
npm --prefix frontend ci
npm --prefix frontend run build
```

Do not add pnpm/yarn lockfiles to this project without an explicit package-manager migration.
