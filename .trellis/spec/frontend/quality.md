# Frontend Quality

Default frontend gate:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

`frontend/package.json` currently defines `build`, `dev`, `preview`, and `test:e2e`; it does not define lint or unit-test scripts. Do not document nonexistent commands as required gates.

When changing console behavior, also run backend tests that cover static serving or task API contracts where relevant.
