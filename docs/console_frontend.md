# Markio Console Frontend (OpenAI-style UI/UX)

## Scope

The console frontend is adapted from `mineru-tianshu`, then trimmed to fit Markio's lightweight enterprise scope:

- Keep only task-related views (Dashboard, Task List, Submit, Detail, Queue)
- Align strictly with Markio `/v1/tasks/*` APIs
- Serve static assets via FastAPI at `/console`

## Route Map

- `/` dashboard
- `/tasks` paginated task list
- `/tasks/submit` submit new task
- `/tasks/:id` task detail
- `/queue` queue control and logs

## API Mapping

Frontend adapters:

- `frontend/src/api/taskApi.ts`
- `frontend/src/api/queueApi.ts`

Mapped backend endpoints:

- `POST /v1/tasks/submit`
- `GET /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `GET /v1/tasks/dashboard`
- `GET /v1/tasks/queue`
- `POST /v1/tasks/queue/pause`
- `POST /v1/tasks/queue/resume`
- `POST /v1/tasks/{task_id}/cancel`
- `POST /v1/tasks/{task_id}/retry`

## Design Direction

`frontend/src/style.css` defines a minimalist OpenAI-inspired language:

- neutral surfaces and subtle borders
- restrained motion
- readability-first spacing and typography
- reduced semantic color palette

## Build and Deploy

```bash
cd frontend
npm install
npm run build
```

Build output target: `markio/webapp`

After backend startup, open:

- `http://localhost:8000/console`

## Third-party Notice

See `frontend/THIRD_PARTY_NOTICES.md` for source attribution and changes.
