# Task Flow

1. Identify the affected surface: router, parser, service, task runtime, settings, SDK/CLI, Vue console, docs, or tests.
2. Read the relevant Trellis spec and source files.
3. Preserve auth, parser contracts, task owner isolation, and Redis fallback unless explicitly scoped.
4. Make a small typed change.
5. Add or update focused backend/frontend tests where behavior changes.
6. Run focused checks, then the shared verification gate.
7. Update `.trellis/spec/` when the change alters long-lived behavior or conventions.
