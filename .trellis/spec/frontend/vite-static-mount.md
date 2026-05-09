# Vite Static Mount

`frontend/vite.config.ts` is part of the backend runtime contract:

- `base` is `/console/`
- build output is `../markio/webapp`
- dev server runs on port `3000`
- dev proxy forwards `/v1` to `http://localhost:8000`
- Vite plugins are Vue and Tailwind CSS 4

FastAPI serves `markio/webapp` at `/console` when `index.html` exists. When the assets are missing, `markio/main.py` returns a helper fallback page rather than a broken SPA shell.

Do not change `base`, `outDir`, or backend mount behavior without updating tests and docs.
