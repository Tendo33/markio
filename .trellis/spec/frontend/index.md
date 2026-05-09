# Frontend Spec Index

## Current Frontend

Markio's browser console is a Vue 3 + Vite + TypeScript SPA. It is built into `markio/webapp` and served by FastAPI at `/console`.

Primary routes:

- `/`: dashboard
- `/tasks`: task list
- `/tasks/submit`: task submission
- `/tasks/:id`: task detail and polling
- `/queue`: admin queue management

## Pre-Development Checklist

- Read [directory-structure.md](directory-structure.md) before moving Vue files.
- Read [vite-static-mount.md](vite-static-mount.md) before changing build output, base path, or backend serving.
- Read [components.md](components.md) before changing UI.
- Read [design-md.md](design-md.md) before major UI work.
- Read [quality.md](quality.md) before verification.

## Quality Check

- Console keeps Vue 3, Pinia, Vue Router, Axios, and Tailwind CSS 4.
- API calls stay centralized in `frontend/src/api`.
- Token storage stays centralized in `frontend/src/api/client.ts`.
- Polling is stopped on route/visibility transitions where current composables do so.
- `npm --prefix frontend run build` produces assets in `markio/webapp`.
