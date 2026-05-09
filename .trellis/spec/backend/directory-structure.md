# Backend Directory Structure

- `markio/main.py`: FastAPI app wiring, middleware registration, router registration, lifespan, console mount, MCP mount, health endpoints.
- `markio/auth/`: JWT user extraction and admin authorization.
- `markio/routers/`: API route modules for files, type-specific parsers, URL parsing, async tasks, and request guards.
- `markio/parsers/`: parser implementations for PDF, DOC/DOCX, PPT/PPTX, XLSX, HTML, EPUB, image, URL, FASTA, and GenBank.
- `markio/services/`: task manager interfaces/implementations, runtime selection, parser registry, sync parse execution, Redis store, serialization, and transitions.
- `markio/schemas/`: parser config, response, and task schemas.
- `markio/settings/`: env config model and accessors.
- `markio/middlewares/`: CORS, gzip, rate limit, security headers, trace middleware, and error handlers.
- `markio/utils/`: logging, file utilities, LibreOffice conversion, model manager, Redis utilities.
- `markio/sdk/`: Python SDK and Typer CLI.
- `markio/web/`: optional Gradio frontend.
- `markio/mcps/`: optional MCP server.
- `markio/webapp/`: generated Vue console assets; do not edit by hand.
