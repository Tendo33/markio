`# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Markio is a high-performance document conversion API platform that parses various file formats (PDF, Office documents, HTML, EPUB, images) and converts them to Markdown. The project provides multiple interfaces: REST API, CLI, Python SDK, and web UI (Gradio).

## Development Environment

### System Dependencies
- **Python**: 3.11+ (required)
- **System packages**: `libreoffice`, `pandoc` (for document conversion)
- **Package manager**: `uv` (recommended) or pip

### Setup Commands
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/Tendo33/markio.git
cd markio
uv venv && uv pip install -e .
```

### Common Development Commands

#### Running the Application
```bash
# Start both API and web interface
./start_services.sh

# Start API only
python markio/main.py

# Start web interface only
python markio/web/gradio_frontend.py

# Docker deployment
docker compose up -d
```

#### CLI Usage
```bash
# Parse documents via CLI
markio pdf test.pdf -o result.md
markio docx test.docx --save --output result.md
markio image test.png --save
```

#### Testing
```bash
# Run all tests (requires running server)
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py --type api
python tests/run_tests.py --type concurrent

# Run tests with pytest directly
pytest tests/ -v -s
```

#### Code Quality
```bash
# Format code
black markio/

# Lint code
ruff check markio/

# Type checking
mypy markio/
```

## Architecture Overview

### Core Components

1. **FastAPI Application** (`markio/main.py`): Main API server with automatic model initialization
2. **Document Parsers** (`markio/parsers/`): Format-specific parsing modules using different engines:
   - PDF: MinerU, VLM, OCR
   - Office documents: docling (DOCX, PPTX, XLSX)
   - Legacy Office: LibreOffice + docling (DOC, PPT)
   - Web: jina (URL), docling (HTML)
   - Other: pandoc (EPUB), MinerU (images)

3. **API Routers** (`markio/routers/`): REST API endpoints for each document type
4. **SDK** (`markio/sdk/`): Python SDK and CLI interface
5. **Configuration** (`markio/settings/`): Environment-based configuration system

### Key Design Patterns

- **Router-based API structure**: Each document type has its own router with consistent endpoint patterns
- **Async/await throughout**: All parsing operations are asynchronous
- **Model management**: Centralized model initialization with safe error handling
- **Configuration via environment**: All settings through environment variables with Pydantic validation
- **Middleware stack**: CORS, GZIP, tracing middleware for production readiness

### Configuration System

Environment variables control all aspects of the application:
- `LOG_LEVEL`: Logging verbosity (DEBUG/INFO/WARNING/ERROR)
- `OUTPUT_DIR`: Directory for parsed content outputs
- `PDF_PARSE_ENGINE`: PDF parsing engine selection (`pipeline`/`vlm-sglang-engine`)
- `MINERU_DEVICE_MODE`: Device selection for MinerU models (`cuda`/`cpu`)
- `VLM_SERVER_URL`: VLM server endpoint for remote processing

## Important Implementation Details

### Model Initialization
- Models are initialized safely at startup with error handling
- Initialization happens in `main.py:initialize_models_safely()`
- Model manager handles switching between different parsing engines

### File Processing Pipeline
1. File upload via FastAPI endpoints
2. Format-specific router handles routing
3. Parser module processes based on configuration
4. Results returned as Markdown with metadata
5. Optional saving to output directory

### Error Handling
- Comprehensive error handling in all parsing operations
- Graceful degradation when models fail to initialize
- Detailed logging for debugging purposes

### Testing Strategy
- Integration tests require running server
- Test files in `tests/test_docs/` for all supported formats
- Concurrent performance testing for high-load scenarios
- Health checks before test execution

## Development Notes

### Adding New Document Formats
1. Create parser module in `markio/parsers/`
2. Add router in `markio/routers/`
3. Register router in `main.py:register_routers()`
4. Add CLI command in `markio_sdk.py` and `markio_cli.py`
5. Update tests and documentation

### Performance Considerations
- Models are loaded once and cached
- Async processing for concurrent requests
- Configurable batch sizes for model inference
- Memory management for GPU operations

### Dependencies
Key libraries and their purposes:
- **FastAPI**: Web framework with automatic OpenAPI documentation
- **MinerU**: PDF parsing with layout analysis and OCR
- **docling**: Office document and HTML parsing
- **Typer**: CLI framework with rich help text
- **Gradio**: Web interface for document preview
- **Pydantic**: Data validation and configuration management