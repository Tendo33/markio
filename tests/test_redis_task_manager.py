import asyncio
import unittest
from collections import defaultdict
from pathlib import Path

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.redis_task_store import RedisTaskStore
from markio.services.redis_task_manager import RedisTaskManager


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

    async def zrangebyscore(self, key, min_score, max_score):
        items = [
            (member, score)
            for member, score in self.zsets.get(key, {}).items()
            if float(min_score) <= score <= float(max_score)
        ]
        items.sort(key=lambda item: (item[1], item[0]))
        return [member for member, _ in items]

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

    async def evalsha(self, sha, _numkeys, *args):
        script = self.scripts.get(sha)
        if script is None:
            raise RuntimeError("missing script")
        return None


class RedisTaskManagerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp_dir = Path("/tmp/markio-redis-task-tests")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        for item in self.tmp_dir.iterdir():
            if item.is_file():
                item.unlink()

    async def _wait_status(self, manager: RedisTaskManager, task_id: str, expected: TaskStatus):
        deadline = asyncio.get_event_loop().time() + 2.0
        while asyncio.get_event_loop().time() < deadline:
            task = await manager.get_task(task_id)
            if task is not None and task.status == expected:
                return
            await asyncio.sleep(0.01)
        self.fail(f"task {task_id} did not reach {expected}")

    async def test_processes_task(self):
        file_path = self.tmp_dir / "example.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)
        manager = RedisTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            store=store,
        )
        await manager.start()
        task = await manager.submit(
            SubmitTaskRequest(filename="example.pdf", file_path=str(file_path))
        )
        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        completed = await manager.get_task(task.task_id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.result, "# parsed")
        await manager.stop()

    async def test_cancel_pending_task(self):
        file_path = self.tmp_dir / "cancel.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)
        manager = RedisTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            store=store,
        )
        await manager.start()
        await manager.pause_queue()

        task = await manager.submit(
            SubmitTaskRequest(filename="cancel.pdf", file_path=str(file_path))
        )
        canceled = await manager.cancel_task(task.task_id)
        self.assertTrue(canceled)
        canceled_task = await manager.get_task(task.task_id)
        self.assertIsNotNone(canceled_task)
        self.assertEqual(canceled_task.status, TaskStatus.canceled)
        await manager.stop()

    async def test_retry_canceled_task_keeps_file(self):
        file_path = self.tmp_dir / "cancel-retry.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)
        manager = RedisTaskManager(
            worker_count=1,
            parser_func=parser,
            store=store,
        )
        await manager.start()
        await manager.pause_queue()

        task = await manager.submit(
            SubmitTaskRequest(filename="cancel-retry.pdf", file_path=str(file_path))
        )
        canceled = await manager.cancel_task(task.task_id)
        self.assertTrue(canceled)

        retried = await manager.retry_task(task.task_id)
        self.assertTrue(retried)

        await manager.resume_queue()
        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        await manager.stop()

    async def test_cache_bypass_when_saving_content(self):
        file_path = self.tmp_dir / "cache-save.pdf"
        file_path.write_text("demo", encoding="utf-8")

        parser_called = False
        cache_called = False

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal parser_called
            parser_called = True
            return "# parsed"

        async def cache_get(key: str):
            nonlocal cache_called
            cache_called = True
            return "# cached"

        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)
        manager = RedisTaskManager(
            worker_count=1,
            parser_func=parser,
            cache_getter=cache_get,
            store=store,
        )
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="cache-save.pdf",
                file_path=str(file_path),
                save_parsed_content=True,
            )
        )

        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        completed = await manager.get_task(task.task_id)
        self.assertEqual(completed.result, "# parsed")
        self.assertTrue(parser_called)
        self.assertFalse(cache_called)
        await manager.stop()

    async def test_pause_state_persists_across_manager_restart(self):
        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        manager = RedisTaskManager(worker_count=1, parser_func=fake_parser, store=store)
        await manager.start()
        await manager.pause_queue()
        self.assertTrue((await manager.get_queue_health()).paused)
        await manager.stop()

        restarted = RedisTaskManager(worker_count=1, parser_func=fake_parser, store=store)
        await restarted.start()
        self.assertTrue((await restarted.get_queue_health()).paused)

        await restarted.resume_queue()
        self.assertFalse((await restarted.get_queue_health()).paused)
        await restarted.stop()

    async def test_cache_key_is_owner_scoped_for_cached_results(self):
        file_path = self.tmp_dir / "owner-cache.pdf"
        file_path.write_text("demo", encoding="utf-8")
        cache_values: dict[str, str] = {}
        parser_calls = 0

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal parser_calls
            parser_calls += 1
            return f"# parsed for {request.owner_id}"

        async def cache_get(key: str):
            return cache_values.get(key)

        async def cache_set(key: str, value: str):
            cache_values[key] = value
            return True

        redis = FakeRedis()
        store = RedisTaskStore(redis, use_lua=False)
        manager = RedisTaskManager(
            worker_count=1,
            parser_func=parser,
            cache_getter=cache_get,
            cache_setter=cache_set,
            store=store,
        )
        await manager.start()

        owner_a = await manager.submit(
            SubmitTaskRequest(
                filename="owner-cache.pdf",
                file_path=str(file_path),
                owner_id="owner-a",
            )
        )
        await self._wait_status(manager, owner_a.task_id, TaskStatus.completed)
        owner_a_completed = await manager.get_task(owner_a.task_id)
        self.assertEqual(owner_a_completed.result, "# parsed for owner-a")
        self.assertEqual(parser_calls, 1)

        file_path.write_text("demo", encoding="utf-8")
        owner_b = await manager.submit(
            SubmitTaskRequest(
                filename="owner-cache.pdf",
                file_path=str(file_path),
                owner_id="owner-b",
            )
        )
        await self._wait_status(manager, owner_b.task_id, TaskStatus.completed)
        owner_b_completed = await manager.get_task(owner_b.task_id)
        self.assertEqual(owner_b_completed.result, "# parsed for owner-b")
        self.assertEqual(parser_calls, 2)

        file_path.write_text("demo", encoding="utf-8")
        owner_a_cached = await manager.submit(
            SubmitTaskRequest(
                filename="owner-cache.pdf",
                file_path=str(file_path),
                owner_id="owner-a",
            )
        )
        owner_a_cached_completed = await manager.get_task(owner_a_cached.task_id)
        self.assertIsNotNone(owner_a_cached_completed)
        self.assertTrue(owner_a_cached_completed.cache_hit)
        self.assertEqual(owner_a_cached_completed.result, "# parsed for owner-a")
        self.assertEqual(parser_calls, 2)
        await manager.stop()


if __name__ == "__main__":
    unittest.main()
