# Markio Console Frontend

This directory contains the Vue 3 console that FastAPI serves at `/console`.

## Stack

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router

## Start Local Development

```bash
npm install
npm run dev
```

Default dev URL:

- `http://localhost:3000`

The default Vite setup proxies `/v1` to the local backend, so same-origin-style API usage still works during development.

## Build

```bash
npm run build
```

Build output is written to:

- `../markio/webapp`

That output is part of the backend delivery contract. When it exists, FastAPI serves the SPA at `/console`. When it does not exist, the backend intentionally serves a fallback helper page instead.

## Environment Model

Primary variable:

- `VITE_API_BASE_URL`

Recommended modes:

- same-origin backend hosting: leave it empty
- local Vite development: leave it empty and rely on the proxy
- explicit cross-origin development: set it to `http://127.0.0.1:8000` and allow that origin in backend CORS

Optional variable:

- `VITE_TASK_MAX_UPLOAD_SIZE_BYTES`

Use it if you want the frontend to pre-validate task upload size with the same limit the backend enforces.

## Current Feature Set

- dashboard with task summaries and recent activity
- paginated task list with refresh, cancel, and retry actions
- task submission flow
- task detail view with polling
- queue management view for admin flows
- toast notifications and confirm dialogs

## Auth Behavior

- the frontend currently uses a browser-managed token model
- API calls are skipped or constrained when no token is present
- admin-only backend routes still depend on JWT claims; the frontend does not replace backend authorization

## Testing and Delivery Notes

- console route tests build the real SPA assets when required
- import-time build side effects are intentionally avoided
- browser E2E coverage lives in `e2e/` and runs with Playwright against mocked `/v1/*` traffic

### Run browser E2E

```bash
npx playwright install chromium
npm run test:e2e
```

Useful companion docs:

- `../docs/console_frontend.md`
- `THIRD_PARTY_NOTICES.md`
