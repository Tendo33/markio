# Type Safety

- Keep public parser, service, and SDK interfaces typed.
- Prefer explicit schema/config classes from `markio/schemas`.
- Avoid passing raw request data through services without validation.
- Keep async task records serializable across in-memory and Redis implementations.
- Preserve mypy's current pragmatic configuration; broad strictness upgrades are separate refactors.
