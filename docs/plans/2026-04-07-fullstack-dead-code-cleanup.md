# Fullstack Dead Code Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove low-risk unused frontend/backend code without changing business logic, UI behavior, or API contracts, and explicitly flag higher-risk backend cleanup candidates for manual review.

**Architecture:** Start from concrete runtime entrypoints and import graphs, then only delete symbols whose usage can be disproved locally. For backend code that may be part of public APIs, startup scripts, or implicit runtime hooks, avoid deletion and instead record warnings for human review.

**Tech Stack:** FastAPI, Python 3.11, Vue 3, Pinia, TypeScript, Vite, Tailwind CSS, pytest

---

### Task 1: Build the candidate inventory

**Files:**
- Modify: `frontend/src/utils/format.ts`
- Modify: `frontend/src/style.css`
- Review: `markio/main.py`
- Review: `markio/services/__init__.py`
- Review: `markio/utils/__init__.py`
- Review: `markio/web/gradio_frontend.py`

**Step 1: Trace frontend runtime entrypoints**

Run: `rg -n "createRouter|defineStore|from '@/utils/format'|from '@/utils/toast'|LoadingSpinner|StatusBadge|FileUploader|StatCard|ConfirmDialog" frontend/src`
Expected: Only actively routed views/components appear.

**Step 2: Trace backend runtime entrypoints**

Run: `rg -n "include_router|handle_middleware|mount_web_console|MarkioMCP|from markio\\.services import|from markio\\.utils import|gradio_frontend" markio tests start_services.sh README.md README.zh.md`
Expected: Distinguish runtime/public entrypoints from truly dead modules.

**Step 3: Identify low-risk unused frontend code**

Run: `rg -n "formatDate\\(|formatBackendName\\(" frontend/src tests`
Expected: Definitions only, no call sites.

**Step 4: Identify unused custom CSS utility classes**

Run: `rg -n "bg-accent|text-accent|border-success|border-info|border-strong|border-accent|scrollbar-hide|badge" frontend/src`
Expected: No source usage outside `frontend/src/style.css`.

### Task 2: Apply low-risk cleanup

**Files:**
- Modify: `frontend/src/utils/format.ts`
- Modify: `frontend/src/style.css`

**Step 1: Remove unused frontend formatter helpers**

Delete only helpers that have no local references and do not affect API payloads.

**Step 2: Remove unused custom CSS classes**

Delete only source-defined classes with no matches in the Vue source tree. Do not touch Tailwind utility classes or dynamic class expressions.

**Step 3: Keep backend cleanup conservative**

If a backend candidate is tied to startup scripts, package exports, CLI entrypoints, tests, or docs, do not delete it in this pass.

### Task 3: Verify behavior

**Files:**
- Test: `frontend/package.json`
- Test: `tests/test_console_frontend.py`
- Test: `tests/test_main_routes.py`

**Step 1: Rebuild frontend**

Run: `cd frontend && pnpm run build`
Expected: TypeScript compile and Vite build succeed.

**Step 2: Run backend regression tests for touched surface**

Run: `uv run pytest tests/test_console_frontend.py tests/test_main_routes.py`
Expected: All selected tests pass.

**Step 3: Summarize high-risk candidates**

List backend/public-surface candidates that look redundant but were not deleted because they may affect API consumers, startup scripts, or implicit integration paths.
