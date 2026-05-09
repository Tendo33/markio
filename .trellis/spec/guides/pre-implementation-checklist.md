# Pre-Implementation Checklist

- [ ] Which route, parser, service, task runtime, SDK/CLI path, Vue view/store, or doc is affected?
- [ ] Does the change affect JWT auth or owner/admin boundaries?
- [ ] Does it affect Redis fallback or in-memory runtime behavior?
- [ ] Does it affect `/console` build/mount assumptions?
- [ ] Which pytest or frontend build checks cover the change?
- [ ] Do public docs and `.trellis/spec/` need matching updates?
