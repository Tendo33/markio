# Backend Testing

Use pytest for backend verification.

Important suites:

- `tests/test_main_routes.py`: app/route behavior
- `tests/test_parser_registry_dispatch.py`: parser dispatch
- `tests/test_sync_parse_service.py`: sync parse response contract
- `tests/test_task_*`: task manager, runtime, auth, queue, transitions
- `tests/test_url_parser.py`: URL safety
- `tests/test_console_frontend.py`: console static serving/fallback
- `tests/test_sdk_auth.py`: SDK auth behavior
- `tests/test_biological_parsers.py`: FASTA/GenBank behavior

Default test runs exclude `live` tests through `pytest.ini`. Only run `-m live` when the task intentionally depends on an external running service.
