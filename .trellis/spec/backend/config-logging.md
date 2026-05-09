# Configuration And Logging

## Settings

Settings are env-driven through `markio/settings`. Important runtime toggles include:

- JWT secret and auth configuration
- log directory and log level
- PDF/image parse engine selection
- Redis enablement and connection settings
- MCP enablement
- task queue/runtime options

`AUTH_JWT_SECRET` must be set before running the app in normal authenticated mode.

## Startup

`markio/main.py` lifespan starts the task manager, initializes Redis when enabled, initializes models safely, then shuts down Redis/task runtime on exit.

## Logging

Use `markio.utils.logger_config.get_logger` and existing structured messages. Do not replace the project logging setup with ad hoc `print` calls.
