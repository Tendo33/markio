import unittest
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.redis_task_store import RedisTaskStore


class FakeRedis:
    def __init__(self):
        self.hashes = defaultdict(dict)
        self.strings = {}
        self.zsets = defaultdict(dict)
        self.counters = defaultdict(int)
        self.scripts = {}

    async def hset(self, key, mapping=None, **kwargs):
        if mapping:
            for field, value in mapping.items():
                self.hashes[key][field] = value
        for field, value in kwargs.items():
            self.hashes[key][field] = value
        return True

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def set(self, key, value):
        self.strings[key] = value
        return True

    async def get(self, key):
        return self.strings.get(key)

    async def zadd(self, key, mapping):
        for member, score in mapping.items():
            self.zsets[key][member] = float(score)
        return True

    async def zrem(self, key, *members):
        removed = 0
        for member in members:
            if member in self.zsets.get(key, {}):
                removed += 1
                del self.zsets[key][member]
        return removed

    async def zcard(self, key):
        return len(self.zsets.get(key, {}))

    async def zrange(self, key, start, end, withscores=False):
        items = sorted(
            self.zsets.get(key, {}).items(),
            key=lambda item: (item[1], item[0]),
        )
        if end == -1:
            slice_items = items[start:]
        else:
            slice_items = items[start : end + 1]
        if withscores:
            return slice_items
        return [member for member, _ in slice_items]

    async def zrevrange(self, key, start, end, withscores=False):
        items = sorted(
            self.zsets.get(key, {}).items(),
            key=lambda item: (item[1], item[0]),
            reverse=True,
        )
        if end == -1:
            slice_items = items[start:]
        else:
            slice_items = items[start : end + 1]
        if withscores:
            return slice_items
        return [member for member, _ in slice_items]

    async def zpopmin(self, key, count=1):
        items = await self.zrange(key, 0, count - 1, withscores=True)
        for member, _ in items:
            self.zsets[key].pop(member, None)
        return items

    async def incr(self, key):
        self.counters[key] += 1
        return self.counters[key]

    async def delete(self, *keys):
        for key in keys:
            self.hashes.pop(key, None)
            self.strings.pop(key, None)
            self.zsets.pop(key, None)
            self.counters.pop(key, None)
        return True

    async def script_load(self, script):
        sha = f"sha-{len(self.scripts) + 1}"
        self.scripts[sha] = script
        return sha

    async def evalsha(self, sha, numkeys, *args):
        script = self.scripts.get(sha)
        if script is None:
            raise RuntimeError("missing script")
        return None


class RedisTaskStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.redis = FakeRedis()
        self.store = RedisTaskStore(self.redis, use_lua=False)

    async def test_submit_and_claim_task(self):
        request = SubmitTaskRequest(filename="demo.pdf", file_path="/tmp/demo.pdf")
        record = await self.store.submit_task(request)
        self.assertEqual(record.status, TaskStatus.pending)
        self.assertEqual(await self.redis.zcard("queue:pending"), 1)

        claimed = await self.store.claim_next_task()
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.task_id, record.task_id)
        self.assertEqual(claimed.status, TaskStatus.processing)
        pending_count = await self.redis.zcard("queue:pending")
        processing_count = await self.redis.zcard("queue:processing")
        self.assertEqual(pending_count, 0)
        self.assertEqual(processing_count, 1)

    async def test_mark_completed_writes_result(self):
        request = SubmitTaskRequest(filename="done.pdf", file_path="/tmp/done.pdf")
        record = await self.store.submit_task(request)
        claimed = await self.store.claim_next_task()
        self.assertIsNotNone(claimed)

        await self.store.mark_completed(record.task_id, "# result")
        task = await self.store.get_task(record.task_id)
        self.assertEqual(task.status, TaskStatus.completed)
        stored_result = await self.redis.get(f"result:{record.task_id}")
        self.assertEqual(stored_result, "# result")

    async def test_cancel_pending_task(self):
        request = SubmitTaskRequest(filename="cancel.pdf", file_path="/tmp/cancel.pdf")
        record = await self.store.submit_task(request)
        canceled = await self.store.cancel_task(record.task_id)
        self.assertTrue(canceled)
        task = await self.store.get_task(record.task_id)
        self.assertEqual(task.status, TaskStatus.canceled)
        pending_count = await self.redis.zcard("queue:pending")
        self.assertEqual(pending_count, 0)

    async def test_list_tasks_by_status(self):
        now = datetime.now(timezone.utc)
        for idx in range(3):
            request = SubmitTaskRequest(filename=f"file-{idx}.pdf", file_path="/tmp/demo.pdf")
            record = await self.store.submit_task(request, created_at=now)
            if idx == 0:
                await self.store.cancel_task(record.task_id)
        page = await self.store.list_tasks(status=TaskStatus.pending, page=1, page_size=10)
        self.assertEqual(page.total, 2)
        self.assertEqual(len(page.items), 2)

    async def test_list_tasks_returns_latest_first(self):
        base = datetime.now(timezone.utc)
        for idx in range(3):
            request = SubmitTaskRequest(
                filename=f"file-{idx}.pdf",
                file_path="/tmp/demo.pdf",
            )
            created_at = base + timedelta(microseconds=idx)
            await self.store.submit_task(request, created_at=created_at)

        page = await self.store.list_tasks(page=1, page_size=3)
        filenames = [item.filename for item in page.items]
        self.assertEqual(filenames, ["file-2.pdf", "file-1.pdf", "file-0.pdf"])

    async def test_owner_isolation_for_get_list_cancel_and_retry(self):
        request_a = SubmitTaskRequest(
            filename="a.pdf",
            file_path="/tmp/a.pdf",
            owner_id="owner-a",
        )
        request_b = SubmitTaskRequest(
            filename="b.pdf",
            file_path="/tmp/b.pdf",
            owner_id="owner-b",
        )
        task_a = await self.store.submit_task(request_a)
        await self.store.submit_task(request_b)

        listed_a = await self.store.list_tasks(owner_id="owner-a", page=1, page_size=10)
        self.assertEqual(listed_a.total, 1)
        self.assertEqual(listed_a.items[0].task_id, task_a.task_id)

        cross_get = await self.store.get_task(task_a.task_id, owner_id="owner-b")
        self.assertIsNone(cross_get)

        cross_cancel = await self.store.cancel_task(task_a.task_id, owner_id="owner-b")
        self.assertFalse(cross_cancel)

        own_cancel = await self.store.cancel_task(task_a.task_id, owner_id="owner-a")
        self.assertTrue(own_cancel)

        cross_retry = await self.store.mark_pending_for_retry(
            task_a.task_id,
            owner_id="owner-b",
        )
        self.assertFalse(cross_retry)

    async def test_owner_list_paginates_after_owner_filter(self):
        owner_task = await self.store.submit_task(
            SubmitTaskRequest(
                filename="owner-a.pdf",
                file_path="/tmp/owner-a.pdf",
                owner_id="owner-a",
            )
        )

        for idx in range(3):
            await self.store.submit_task(
                SubmitTaskRequest(
                    filename=f"owner-b-{idx}.pdf",
                    file_path=f"/tmp/owner-b-{idx}.pdf",
                    owner_id="owner-b",
                )
            )

        listed_a = await self.store.list_tasks(
            owner_id="owner-a",
            page=1,
            page_size=1,
        )
        self.assertEqual(listed_a.total, 1)
        self.assertEqual(len(listed_a.items), 1)
        self.assertEqual(listed_a.items[0].task_id, owner_task.task_id)

    async def test_owner_index_is_preserved_across_status_transitions(self):
        task = await self.store.submit_task(
            SubmitTaskRequest(
                filename="owner-a.pdf",
                file_path="/tmp/owner-a.pdf",
                owner_id="owner-a",
            )
        )
        owner_key = "task:owner:owner-a"
        self.assertIn(task.task_id, self.redis.zsets[owner_key])

        canceled = await self.store.cancel_task(task.task_id, owner_id="owner-a")
        self.assertTrue(canceled)
        self.assertIn(task.task_id, self.redis.zsets[owner_key])

        retried = await self.store.mark_pending_for_retry(task.task_id, owner_id="owner-a")
        self.assertTrue(retried)
        self.assertIn(task.task_id, self.redis.zsets[owner_key])

        claimed = await self.store.claim_next_task()
        self.assertIsNotNone(claimed)
        await self.store.mark_failed(task.task_id, "boom")
        self.assertIn(task.task_id, self.redis.zsets[owner_key])

    async def test_owner_index_rebuilds_for_legacy_records(self):
        task = await self.store.submit_task(
            SubmitTaskRequest(
                filename="legacy.pdf",
                file_path="/tmp/legacy.pdf",
                owner_id="owner-legacy",
            )
        )
        owner_key = "task:owner:owner-legacy"
        await self.redis.zrem(owner_key, task.task_id)
        self.assertEqual(await self.redis.zcard(owner_key), 0)

        listed = await self.store.list_tasks(owner_id="owner-legacy", page=1, page_size=10)
        self.assertEqual(listed.total, 1)
        self.assertEqual(listed.items[0].task_id, task.task_id)
        self.assertEqual(await self.redis.zcard(owner_key), 1)

    async def test_claim_and_cancel_race_keeps_consistent_status(self):
        request = SubmitTaskRequest(
            filename="race.pdf",
            file_path="/tmp/race.pdf",
            owner_id="owner-race",
        )
        record = await self.store.submit_task(request)

        claimed, canceled = await asyncio.gather(
            self.store.claim_next_task(),
            self.store.cancel_task(record.task_id, owner_id="owner-race"),
        )
        current = await self.store.get_task(record.task_id, include_result=False)
        self.assertIsNotNone(current)
        self.assertIn(current.status, {TaskStatus.processing, TaskStatus.canceled})

        if claimed is not None:
            self.assertEqual(current.status, TaskStatus.processing)
            self.assertFalse(canceled)
        else:
            self.assertTrue(canceled)
            self.assertEqual(current.status, TaskStatus.canceled)


if __name__ == "__main__":
    unittest.main()
