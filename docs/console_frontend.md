# Markio Console Frontend

[Back to README](../README.md) | [中文版本](console_frontend_zh.md)

## What It Is

The console is the primary web control plane for Markio. It is a Vue 3 + TypeScript + Vite SPA built from `frontend/` and mounted by FastAPI at `/console`.

Current product intent:

- the console is the main browser workflow
- Gradio is optional and auxiliary
- same-origin deployment is the default and recommended path

## Runtime Contract

### Build output

The frontend must build into `markio/webapp`.

```bash
cd frontend
npm install
npm run build
```

### Backend serving

`markio/main.py` mounts the console as follows:

- when `markio/webapp/index.html` exists, `/console` serves the SPA
- when assets are missing, `/console` returns a fallback helper page

The fallback page is not a parallel product surface. It only exists to explain that the console has not been built yet.

## Route Map

- `/` dashboard
- `/tasks` task list
- `/tasks/submit` task submission
- `/tasks/:id` task detail
- `/queue` queue controls

Those routes are client-side routes inside the `/console` SPA mount.

## Backend API Mapping

Frontend modules:

- `frontend/src/api/taskApi.ts`
- `frontend/src/api/queueApi.ts`

Backend endpoints used by the console:

- `POST /v1/tasks/submit`
- `GET /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `GET /v1/tasks/dashboard`
- `GET /v1/tasks/queue`
- `POST /v1/tasks/queue/pause`
- `POST /v1/tasks/queue/resume`
- `POST /v1/tasks/{task_id}/cancel`
- `POST /v1/tasks/{task_id}/retry`

## Auth and Permissions

- every console-triggered API call still depends on JWT auth
- the current frontend keeps the token client-side and persists it in `localStorage`
- expired or malformed browser tokens are treated as unavailable until the user replaces them
- queue controls are effectively admin-only because the backend requires `role=admin`
- dashboard and task list responses are owner-scoped; the backend remains the source of truth for access control

## Network Model

Default behavior:

- `VITE_API_BASE_URL=""`
- requests go to same-origin `/v1/*`
- local Vite development proxies `/v1` to `http://localhost:8000`

Cross-origin development is possible, but requires backend CORS allowlisting.

## Security Headers and Browser Policy

The backend now serves the console with a tighter CSP posture:

- `script-src` is restricted to `'self'`
- `object-src 'none'`
- `frame-ancestors 'none'`
- `connect-src` reduced to same-origin defaults

When extending the console, prefer same-origin API access and avoid introducing browser features that require loosening that policy without a strong reason.

## Tests and Delivery Expectations

The repository now treats the built SPA as part of the delivery contract:

- console route tests validate real built assets
- the test fixture builds the frontend when needed
- import-time side effects are intentionally avoided

Relevant tests:

- `tests/test_console_frontend.py`

## Development Notes

```bash
cd frontend
npm install
npm run dev
```

Useful paths:

- `frontend/src/views/`
- `frontend/src/components/`
- `frontend/src/stores/`
- `frontend/src/router/`

## Known Boundaries

- no dedicated frontend E2E suite yet
- auth remains token-based on the frontend for now
- `/console` is only considered healthy when real build assets exist
