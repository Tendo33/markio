# Parser/Task Architecture P0-P2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate parser routing, reduce duplicated task-manager logic, standardize sync parse responses, and improve request/task observability without breaking existing parse behavior.

**Architecture:** Introduce shared service layers (parser registry + sync parse execution + task-manager base) and migrate routers/managers to these shared primitives. Keep endpoint paths stable, preserve `parsed_content` compatibility, and add additive metadata (`parser`, `source_type`, `request_id`, `duration_ms`, `processing_duration_ms`).

**Tech Stack:** FastAPI, Pydantic/dataclasses, asyncio task workers, pytest/httpx.

---

### Task 1: P0 - Single Parser Registry for Dispatch

**Files:**
- Create: `markio/services/parser_registry.py`
- Modify: `markio/routers/file_router.py`
- Modify: `markio/services/document_service.py`
- Test: `tests/test_parser_registry_dispatch.py`

**Step 1: Write the failing test**

Add tests that expect:
1. `/v1/parse_file` accepts `.htm` and dispatches via a shared registry.
2. `parse_local_file()` in async task flow uses the same shared registry mapping.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parser_registry_dispatch.py -q`
Expected: FAIL (missing `parser_registry` module/usage).

**Step 3: Write minimal implementation**

Implement registry functions:
- canonical extension->parser mapping
- extension->MIME mapping
- helpers for supported extensions, parser lookup, and MIME checks

Migrate `file_router` and `document_service` to use these helpers.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_parser_registry_dispatch.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_parser_registry_dispatch.py markio/services/parser_registry.py markio/routers/file_router.py markio/services/document_service.py
git commit -m "refactor: unify parser dispatch registry"
```

### Task 2: P0 - Shared TaskManager Base

**Files:**
- Create: `markio/services/task_manager_base.py`
- Modify: `markio/services/task_manager.py`
- Modify: `markio/services/redis_task_manager.py`
- Test: `tests/test_task_manager_base.py`

**Step 1: Write the failing test**

Add tests that expect:
1. `AsyncTaskManager` and `RedisTaskManager` inherit from `BaseTaskManager`.
2. shared cache-key behavior is exposed through the shared base implementation.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_task_manager_base.py -q`
Expected: FAIL (no `BaseTaskManager`).

**Step 3: Write minimal implementation**

Move shared logic to base class:
- parser/cache initialization
- `_build_cache_key`
- `_safe_cache_get` / `_safe_cache_set`
- `_normalize_status_filter`
- `_cleanup_temp_file`

Update both managers to extend base class.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_task_manager_base.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_task_manager_base.py markio/services/task_manager_base.py markio/services/task_manager.py markio/services/redis_task_manager.py
git commit -m "refactor: share task manager base behavior"
```

### Task 3: P1 - Shared Sync Parse Execution Service

**Files:**
- Create: `markio/services/sync_parse_service.py`
- Modify: `markio/routers/file_router.py`
- Modify: `markio/routers/doc_router.py`
- Modify: `markio/routers/docx_router.py`
- Modify: `markio/routers/pdf_router.py`
- Modify: `markio/routers/ppt_router.py`
- Modify: `markio/routers/pptx_router.py`
- Modify: `markio/routers/xlsx_router.py`
- Modify: `markio/routers/html_router.py`
- Modify: `markio/routers/epub_router.py`
- Modify: `markio/routers/image_router.py`
- Modify: `markio/routers/fasta_router.py`
- Modify: `markio/routers/genbank_router.py`
- Test: `tests/test_sync_parse_service.py`

**Step 1: Write the failing test**

Add tests for helper behavior:
1. Uploaded file is written once to unique temp path and always cleaned in `finally`.
2. Wrapped parser receives expected path/args.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_parse_service.py -q`
Expected: FAIL (helper missing).

**Step 3: Write minimal implementation**

Create shared helper to:
- persist uploaded file to temp
- invoke parser callback
- cleanup temp file in `finally`

Refactor file-based routers to reuse helper.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sync_parse_service.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_parse_service.py markio/services/sync_parse_service.py markio/routers/*.py
git commit -m "refactor: extract shared sync parse execution flow"
```

### Task 4: P1 - Standardize Sync Parse Response Contract

**Files:**
- Create: `markio/schemas/api_schemas.py`
- Modify: `markio/services/sync_parse_service.py`
- Modify: `markio/routers/file_router.py`
- Modify: `markio/routers/url_router.py`
- Modify: `markio/routers/doc_router.py`
- Modify: `markio/routers/docx_router.py`
- Modify: `markio/routers/pdf_router.py`
- Modify: `markio/routers/ppt_router.py`
- Modify: `markio/routers/pptx_router.py`
- Modify: `markio/routers/xlsx_router.py`
- Modify: `markio/routers/html_router.py`
- Modify: `markio/routers/epub_router.py`
- Modify: `markio/routers/image_router.py`
- Modify: `markio/routers/fasta_router.py`
- Modify: `markio/routers/genbank_router.py`
- Test: `tests/test_sync_response_contract.py`

**Step 1: Write the failing test**

Add API tests requiring sync parse responses to include:
- `parsed_content`
- `parser`
- `source_type`
- `request_id`
- `duration_ms`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_response_contract.py -q`
Expected: FAIL (keys absent).

**Step 3: Write minimal implementation**

Add `ParseResponse` schema and helper builder. Update sync endpoints to return standardized payload while preserving `parsed_content` backward compatibility.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sync_response_contract.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_sync_response_contract.py markio/schemas/api_schemas.py markio/services/sync_parse_service.py markio/routers/*.py
git commit -m "feat: standardize sync parse response contract"
```

### Task 5: P2 - Add Observability Fields and Duration Tracking

**Files:**
- Modify: `markio/schemas/task_schemas.py`
- Modify: `markio/services/task_manager.py`
- Modify: `markio/services/redis_task_manager.py`
- Modify: `markio/services/sync_parse_service.py`
- Test: `tests/test_task_manager.py`
- Test: `tests/test_sync_response_contract.py`

**Step 1: Write the failing test**

Add tests that expect:
1. completed async tasks include `processing_duration_ms` (non-negative integer).
2. sync parse response includes measurable `duration_ms` and non-empty `request_id`.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_task_manager.py::TaskManagerTests::test_processes_task tests/test_sync_response_contract.py -q`
Expected: FAIL (missing observability fields).

**Step 3: Write minimal implementation**

- Add optional `processing_duration_ms` to task record and persistence/serialization paths.
- Calculate duration from `started_at` to completion/failure/cancel.
- Keep logging of parser latency and include request id in sync response helper.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_task_manager.py::TaskManagerTests::test_processes_task tests/test_sync_response_contract.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_task_manager.py tests/test_sync_response_contract.py markio/schemas/task_schemas.py markio/services/task_manager.py markio/services/redis_task_manager.py markio/services/sync_parse_service.py
git commit -m "feat: add parse and task observability metadata"
```

### Task 6: Verification + Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `README_zh.md`

**Step 1: Run verification suite**

Run:
- `uv run pytest tests/test_parser_registry_dispatch.py tests/test_task_manager_base.py tests/test_sync_parse_service.py tests/test_sync_response_contract.py -q`
- `uv run pytest tests/test_task_manager.py tests/test_redis_task_manager.py tests/test_task_router.py tests/test_pdf_engine_router_support.py -q`

Expected: all PASS.

**Step 2: Update docs**

Add concise notes for:
- parser dispatch strategy (single registry)
- sync response metadata fields
- task observability field

**Step 3: Final sanity check**

Run: `git diff --stat` and confirm only intended files changed.

**Step 4: Commit**

```bash
git add README.md README_zh.md
git commit -m "docs: document parser routing and response metadata"
```
