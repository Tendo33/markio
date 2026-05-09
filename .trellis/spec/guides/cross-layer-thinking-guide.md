# Cross-Layer Thinking Guide

For Markio, cross-layer changes often touch API routes, parser services, task records, SDK/CLI docs, and the Vue console.

Trace changes like this:

```text
router or SDK/CLI command
  -> schema/config validation
  -> parser or task service
  -> task serialization / Redis or memory runtime
  -> Vue API client/store/composable
  -> docs and tests
```

Ask:

- Does this route still require JWT auth?
- Does task list/detail/cancel/retry preserve owner isolation?
- Are admin-only queue operations still admin-only?
- Does Redis behavior match in-memory behavior?
- Does the Vue console API type still match backend response shape?
- Do README/docs/SDK/CLI examples need updates?
