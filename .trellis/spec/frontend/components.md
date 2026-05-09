# Vue Components And State

## Pages

- `Dashboard.vue`: summary cards, recent tasks, refresh, and admin queue link.
- `TaskSubmit.vue`: upload form, parse method/language/priority/output/page range validation, and submit action.
- `TaskList.vue`: status/page filters, task table/cards, pagination, and active-task polling.
- `TaskDetail.vue`: task metadata, cancel/retry actions, result loading, and polling until terminal state.
- `QueueManagement.vue`: admin-only queue health, pause, resume, and refresh.

## State And API

- `taskStore.ts` owns dashboard, list, detail, submit, cancel, retry, and request states.
- `queueStore.ts` owns queue health and pause/resume.
- `authStore.ts` owns JWT token status and role.
- `api/client.ts` owns Axios config, token lookup, token classification, and error normalization.

Keep new API methods in `frontend/src/api` and expose state through Pinia stores rather than calling Axios directly from views.
