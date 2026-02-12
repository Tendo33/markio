# Redis Task Queue Design (ZSET + Lua)

Date: 2026-02-12

## Summary
Replace the in-memory task queue and local JSON state file with Redis-backed storage using ZSETs for priority ordering and Lua scripts for atomic task claiming. Keep API and frontend contracts unchanged. Redis is the single source of truth for task metadata, status, and results. No TTLs are applied to tasks or results (per requirement).

## Goals
- Preserve current async task workflow (submit, list, cancel, retry, dashboard, queue health).
- Support priority scheduling with deterministic ordering.
- Ensure atomic task claiming across multiple workers/instances.
- Provide consistent listing and status filters without local JSON state.

## Non-Goals
- Persist raw file data in Redis.
- Introduce authentication/authorization or a relational database.
- Change public API or frontend behavior.

## Data Model (Redis Keys)
- task:{task_id} (HASH):
  - status, priority, filename, parse_method, lang
  - created_at, started_at, completed_at
  - retry_count, error_message, cache_hit
  - result_key = result:{task_id}
- result:{task_id} (STRING/JSON): parsed output
- queue:pending (ZSET): task_id, score = priority_rank * 1e12 + enqueue_seq
- queue:processing (ZSET): task_id, score = started_at (epoch seconds)
- task:created (ZSET): task_id, score = created_at
- task:status:{status} (ZSET): task_id, score = created_at

## Core Flows
- Submit:
  - Write task hash (status=pending), add to task:created and task:status:pending.
  - Add to queue:pending with priority-based score.
- Claim (Lua):
  - ZPOPMIN queue:pending -> task_id
  - HSET task:{id} status=processing started_at=now
  - ZADD queue:processing score=now
  - Update task:status indices
- Complete:
  - SET result:{id}, HSET task:{id} status=completed completed_at=now
  - ZREM queue:processing, update task:status indices
- Fail / Retry:
  - HSET status=failed + error_message, ZREM queue:processing
  - If retry_count < max_auto_retries, requeue to pending and increment retry_count
- Cancel:
  - Only from pending; mark canceled and remove from queue:pending

## Error Handling
- Lua ensures atomic claim and prevents double-claiming.
- State transitions are guarded by status checks to prevent invalid moves.
- Processing timeouts are re-queued by scanning queue:processing.
- If result write fails, mark task failed with error_message.

## Testing
- Unit tests for RedisTaskStore: submit/claim/complete/fail/cancel/retry/list/stats.
- Concurrency test: multiple workers claim tasks without duplicates.
- Timeout recovery test: processing tasks re-queued after threshold.
- Index consistency checks for task:status:* and task:created.

