# Python Package, SDK, And CLI

## Package

- Package name: `markio`
- Python baseline: `>=3.11`
- Version source: `markio/__init__.py`
- CLI entrypoint: `markio = "markio.sdk.markio_cli:app"`

## SDK/CLI Boundaries

- Keep remote API behavior aligned with FastAPI routes.
- Keep local parser mode aligned with router/parser logic.
- Do not add SDK convenience behavior that bypasses URL safety, parser validation, or auth assumptions documented for the API.
- FASTA and GenBank have dedicated routes/parsers; only add first-class SDK/CLI facades when tests and docs are updated together.

## Parser Boundaries

- Parser implementations belong in `markio/parsers`.
- Router modules should validate request shape and call shared execution helpers.
- Cross-format dispatch belongs in parser registry/service code, not copy-pasted into each route.
