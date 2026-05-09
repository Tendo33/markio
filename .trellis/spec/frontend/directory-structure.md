# Frontend Directory Structure

- `frontend/src/main.ts`: Vue app bootstrap.
- `frontend/src/App.vue`: console shell.
- `frontend/src/router/index.ts`: route table and document title sync.
- `frontend/src/layouts/AppLayout.vue`: common console layout.
- `frontend/src/views/`: dashboard, task list, task submit, task detail, and queue pages.
- `frontend/src/api/`: Axios client, task API, queue API, and shared response types.
- `frontend/src/stores/`: Pinia auth, task, and queue stores.
- `frontend/src/composables/`: polling and page-state lifecycle helpers.
- `frontend/src/components/`: shared UI pieces.
- `frontend/src/style.css`: Tailwind CSS 4 import and console styling.

Use `@` alias for imports from `frontend/src`.
