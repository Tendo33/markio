# Code Quality

- Keep parser contracts explicit and testable.
- Prefer existing router/service/parser boundaries over adding broad abstractions.
- Use type hints on public Python interfaces.
- Preserve existing test markers: default tests exclude `live`; external service checks use `@pytest.mark.live`.
- Keep frontend API calls centralized in `frontend/src/api`.
- Keep browser token storage centralized in `frontend/src/api/client.ts`.
- Do not make Redis, LibreOffice, Gradio, MCP, or model downloads mandatory for the default local path unless explicitly scoped.
