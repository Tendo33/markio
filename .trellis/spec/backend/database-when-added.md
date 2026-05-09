# Task Runtime And Persistence

Markio currently uses an in-memory task manager by default and Redis optionally for task/cache persistence.

## Rules

- Do not make Redis mandatory for local development.
- Keep in-memory behavior covered by tests.
- Redis code must preserve owner isolation, task status transitions, serialization, and error recovery.
- Queue pause/resume and queue health are admin-only operations.
- Task states must remain compatible with the Vue console: `pending`, `processing`, `completed`, `failed`, and `canceled`.

If a durable database is added later, write a migration spec first; do not silently reinterpret this Redis/in-memory boundary as a relational database contract.
