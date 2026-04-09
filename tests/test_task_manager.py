import asyncio
import unittest
from pathlib import Path

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus
from markio.services.task_manager import AsyncTaskManager


class TaskManagerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp_dir = Path("/tmp/markio-task-tests")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        for item in self.tmp_dir.iterdir():
            if item.is_file():
                item.unlink()

    async def _wait_status(
        self,
        manager: AsyncTaskManager,
        task_id: str,
        expected: TaskStatus,
        timeout: float = 2.0,
    ) -> None:
        deadline = asyncio.get_event_loop().time() + timeout
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
            self.assertTrue(path.endswith("example.pdf"))
            self.assertEqual(request.parse_method, "auto")
            return "# parsed"

        manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="example.pdf",
                file_path=str(file_path),
                parse_method="auto",
                lang="ch",
            )
        )

        self.assertEqual(task.status, TaskStatus.pending)
        await self._wait_status(manager, task.task_id, TaskStatus.completed)

        completed = await manager.get_task(task.task_id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, TaskStatus.completed)
        self.assertEqual(completed.result, "# parsed")
        self.assertIsNone(completed.error_message)

        stats = await manager.get_stats()
        self.assertEqual(stats.completed, 1)
        self.assertEqual(stats.failed, 0)

        await manager.stop()

    async def test_completed_task_tracks_processing_duration(self):
        file_path = self.tmp_dir / "duration.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            await asyncio.sleep(0.01)
            return "# parsed"

        manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="duration.pdf",
                file_path=str(file_path),
            )
        )

        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        completed = await manager.get_task(task.task_id)
        self.assertIsNotNone(completed)
        self.assertIsNotNone(completed.processing_duration_ms)
        self.assertGreaterEqual(completed.processing_duration_ms, 0)
        await manager.stop()

    async def test_marks_failure(self):
        file_path = self.tmp_dir / "bad.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def failing_parser(path: str, request: SubmitTaskRequest) -> str:
            raise RuntimeError("parse error")

        manager = AsyncTaskManager(worker_count=1, parser_func=failing_parser)
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="bad.pdf",
                file_path=str(file_path),
            )
        )

        await self._wait_status(manager, task.task_id, TaskStatus.failed)

        failed = await manager.get_task(task.task_id)
        self.assertIsNotNone(failed)
        self.assertEqual(failed.status, TaskStatus.failed)
        self.assertIn("parse error", failed.error_message or "")

        stats = await manager.get_stats()
        self.assertEqual(stats.failed, 1)

        await manager.stop()

    async def test_cache_hit_skips_parsing(self):
        file_path = self.tmp_dir / "cached.pdf"
        file_path.write_text("demo", encoding="utf-8")

        parser_called = False

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal parser_called
            parser_called = True
            return "should-not-run"

        async def fake_cache_get(key: str):
            return "# cached-result"

        cache_sets = []

        async def fake_cache_set(key: str, value: str):
            cache_sets.append((key, value))
            return True

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            cache_getter=fake_cache_get,
            cache_setter=fake_cache_set,
        )
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="cached.pdf",
                file_path=str(file_path),
            )
        )

        self.assertEqual(task.status, TaskStatus.completed)
        self.assertTrue(task.cache_hit)
        self.assertEqual(task.result, "# cached-result")
        self.assertFalse(parser_called)
        self.assertEqual(cache_sets, [])
        self.assertFalse(file_path.exists())

        await manager.stop()

    async def test_cache_set_after_task_completed(self):
        file_path = self.tmp_dir / "cache-set.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        async def fake_cache_get(key: str):
            return None

        cache_sets = []

        async def fake_cache_set(key: str, value: str):
            cache_sets.append((key, value))
            return True

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            cache_getter=fake_cache_get,
            cache_setter=fake_cache_set,
        )
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="cache-set.pdf",
                file_path=str(file_path),
            )
        )

        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        self.assertEqual(len(cache_sets), 1)
        self.assertEqual(cache_sets[0][1], "# parsed")
        self.assertFalse(file_path.exists())

        await manager.stop()

    async def test_pause_resume_queue(self):
        file_path = self.tmp_dir / "pause.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
        await manager.start()
        await manager.pause_queue()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="pause.pdf",
                file_path=str(file_path),
            )
        )

        await asyncio.sleep(0.1)
        pending_task = await manager.get_task(task.task_id)
        self.assertIsNotNone(pending_task)
        self.assertEqual(pending_task.status, TaskStatus.pending)

        await manager.resume_queue()
        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        await manager.stop()

    async def test_cancel_pending_task(self):
        file_path = self.tmp_dir / "cancel.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        manager = AsyncTaskManager(worker_count=1, parser_func=fake_parser)
        await manager.start()
        await manager.pause_queue()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="cancel.pdf",
                file_path=str(file_path),
            )
        )

        canceled = await manager.cancel_task(task.task_id)
        self.assertTrue(canceled)
        canceled_task = await manager.get_task(task.task_id)
        self.assertIsNotNone(canceled_task)
        self.assertEqual(canceled_task.status, TaskStatus.canceled)

        await manager.resume_queue()
        await asyncio.sleep(0.1)
        canceled_task = await manager.get_task(task.task_id)
        self.assertEqual(canceled_task.status, TaskStatus.canceled)

        await manager.stop()

    async def test_retry_failed_task(self):
        file_path = self.tmp_dir / "retry.pdf"
        file_path.write_text("demo", encoding="utf-8")

        attempts = 0

        async def flaky_parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("first failure")
            return "# success"

        manager = AsyncTaskManager(worker_count=1, parser_func=flaky_parser)
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(
                filename="retry.pdf",
                file_path=str(file_path),
            )
        )

        await self._wait_status(manager, task.task_id, TaskStatus.failed)
        retried = await manager.retry_task(task.task_id)
        self.assertTrue(retried)
        await self._wait_status(manager, task.task_id, TaskStatus.completed)

        completed = await manager.get_task(task.task_id)
        self.assertEqual(completed.result, "# success")
        self.assertEqual(completed.retry_count, 1)
        await manager.stop()

    async def test_persistence_loads_previous_tasks(self):
        file_path = self.tmp_dir / "persist.pdf"
        file_path.write_text("demo", encoding="utf-8")
        state_file = self.tmp_dir / "task_state.json"

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# persisted"

        manager1 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=4096,
        )
        await manager1.start()

        task = await manager1.submit(
            SubmitTaskRequest(
                filename="persist.pdf",
                file_path=str(file_path),
            )
        )
        await self._wait_status(manager1, task.task_id, TaskStatus.completed)
        await manager1.stop()

        manager2 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=4096,
        )
        await manager2.start()
        loaded = await manager2.get_task(task.task_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, TaskStatus.completed)
        self.assertEqual(loaded.result, "# persisted")
        await manager2.stop()

    async def test_persistence_truncates_result_by_config(self):
        file_path = self.tmp_dir / "persist-truncate.pdf"
        file_path.write_text("demo", encoding="utf-8")
        state_file = self.tmp_dir / "task_state_truncate.json"

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "1234567890"

        manager1 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=4,
        )
        await manager1.start()

        task = await manager1.submit(
            SubmitTaskRequest(
                filename="persist-truncate.pdf",
                file_path=str(file_path),
            )
        )
        await self._wait_status(manager1, task.task_id, TaskStatus.completed)
        await manager1.stop()

        manager2 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=4,
        )
        await manager2.start()
        loaded = await manager2.get_task(task.task_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.result, "1234")
        await manager2.stop()

    async def test_persistence_can_disable_result_storage(self):
        file_path = self.tmp_dir / "persist-no-result.pdf"
        file_path.write_text("demo", encoding="utf-8")
        state_file = self.tmp_dir / "task_state_no_result.json"

        async def fake_parser(path: str, request: SubmitTaskRequest) -> str:
            return "# do-not-persist"

        manager1 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=0,
        )
        await manager1.start()

        task = await manager1.submit(
            SubmitTaskRequest(
                filename="persist-no-result.pdf",
                file_path=str(file_path),
            )
        )
        await self._wait_status(manager1, task.task_id, TaskStatus.completed)
        await manager1.stop()

        manager2 = AsyncTaskManager(
            worker_count=1,
            parser_func=fake_parser,
            state_file_path=str(state_file),
            state_result_max_chars=0,
        )
        await manager2.start()
        loaded = await manager2.get_task(task.task_id)
        self.assertIsNotNone(loaded)
        self.assertIsNone(loaded.result)
        await manager2.stop()

    async def test_list_tasks_supports_pagination_and_status(self):
        state_file = self.tmp_dir / "list_state.json"

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            if request.filename.startswith("bad"):
                raise RuntimeError("fail")
            return "# ok"

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=parser,
            state_file_path=str(state_file),
        )
        await manager.start()

        for name in ["ok1.pdf", "bad1.pdf", "ok2.pdf"]:
            file_path = self.tmp_dir / name
            file_path.write_text("demo", encoding="utf-8")
            await manager.submit(SubmitTaskRequest(filename=name, file_path=str(file_path)))

        await asyncio.sleep(0.3)
        completed_page = await manager.list_tasks(
            page=1,
            page_size=1,
            status=TaskStatus.completed,
        )
        self.assertEqual(len(completed_page.items), 1)
        self.assertEqual(completed_page.total, 2)

        failed_page = await manager.list_tasks(
            page=1,
            page_size=10,
            status=TaskStatus.failed,
        )
        self.assertEqual(failed_page.total, 1)
        self.assertEqual(failed_page.items[0].status, TaskStatus.failed)
        await manager.stop()

    async def test_priority_queue_processes_higher_priority_first(self):
        order = []

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            order.append(request.filename)
            await asyncio.sleep(0.02)
            return "# ok"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser)
        await manager.start()
        await manager.pause_queue()

        low_file = self.tmp_dir / "low.pdf"
        low_file.write_text("demo", encoding="utf-8")
        high_file = self.tmp_dir / "high.pdf"
        high_file.write_text("demo", encoding="utf-8")

        low_task = await manager.submit(
            SubmitTaskRequest(
                filename="low.pdf",
                file_path=str(low_file),
                priority=1,
            )
        )
        high_task = await manager.submit(
            SubmitTaskRequest(
                filename="high.pdf",
                file_path=str(high_file),
                priority=10,
            )
        )

        await manager.resume_queue()
        await self._wait_status(manager, low_task.task_id, TaskStatus.completed)
        await self._wait_status(manager, high_task.task_id, TaskStatus.completed)
        self.assertEqual(order[0], "high.pdf")
        self.assertEqual(order[1], "low.pdf")
        await manager.stop()

    async def test_prune_keeps_pending_tasks(self):
        async def parser(path: str, request: SubmitTaskRequest) -> str:
            return "# ok"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser, max_history=1)
        await manager.start()
        await manager.pause_queue()

        first_task_id = None
        for index in range(21):
            file_path = self.tmp_dir / f"pending-{index}.pdf"
            file_path.write_text("demo", encoding="utf-8")
            task = await manager.submit(
                SubmitTaskRequest(filename=file_path.name, file_path=str(file_path))
            )
            if index == 0:
                first_task_id = task.task_id

        self.assertIsNotNone(first_task_id)
        self.assertIsNotNone(await manager.get_task(first_task_id))

        await manager.resume_queue()
        await self._wait_status(manager, first_task_id, TaskStatus.completed)
        await manager.stop()

    async def test_auto_retry_succeeds(self):
        attempts = 0

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("first fail")
            return "# success"

        file_path = self.tmp_dir / "auto-retry.pdf"
        file_path.write_text("demo", encoding="utf-8")

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=parser,
            max_auto_retries=1,
            retry_delay_seconds=0.01,
        )
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(filename="auto-retry.pdf", file_path=str(file_path))
        )
        await self._wait_status(manager, task.task_id, TaskStatus.completed)
        done = await manager.get_task(task.task_id)
        self.assertEqual(done.retry_count, 1)
        self.assertEqual(done.result, "# success")
        await manager.stop()

    async def test_retry_canceled_task_keeps_file(self):
        file_path = self.tmp_dir / "cancel-retry.pdf"
        file_path.write_text("demo", encoding="utf-8")

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            return "# parsed"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser)
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

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            nonlocal parser_called
            parser_called = True
            return "# parsed"

        async def cache_get(key: str):
            return "# cached"

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=parser,
            cache_getter=cache_get,
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
        await manager.stop()

    async def test_auto_retry_exhausted(self):
        async def parser(path: str, request: SubmitTaskRequest) -> str:
            raise RuntimeError("always fail")

        file_path = self.tmp_dir / "auto-retry-fail.pdf"
        file_path.write_text("demo", encoding="utf-8")

        manager = AsyncTaskManager(
            worker_count=1,
            parser_func=parser,
            max_auto_retries=1,
            retry_delay_seconds=0.01,
        )
        await manager.start()

        task = await manager.submit(
            SubmitTaskRequest(filename="auto-retry-fail.pdf", file_path=str(file_path))
        )
        await self._wait_status(manager, task.task_id, TaskStatus.failed, timeout=3.0)
        failed = await manager.get_task(task.task_id)
        self.assertEqual(failed.retry_count, 1)
        self.assertIn("always fail", failed.error_message or "")
        await manager.stop()

    async def test_dashboard_snapshot(self):
        file_ok = self.tmp_dir / "dash-ok.pdf"
        file_ok.write_text("demo", encoding="utf-8")
        file_fail = self.tmp_dir / "dash-fail.pdf"
        file_fail.write_text("demo", encoding="utf-8")

        async def parser(path: str, request: SubmitTaskRequest) -> str:
            if request.filename.endswith("fail.pdf"):
                raise RuntimeError("dash fail")
            return "# ok"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser)
        await manager.start()
        ok_task = await manager.submit(
            SubmitTaskRequest(filename="dash-ok.pdf", file_path=str(file_ok))
        )
        fail_task = await manager.submit(
            SubmitTaskRequest(filename="dash-fail.pdf", file_path=str(file_fail))
        )
        await self._wait_status(manager, ok_task.task_id, TaskStatus.completed)
        await self._wait_status(manager, fail_task.task_id, TaskStatus.failed)

        dashboard = await manager.get_dashboard(recent_limit=5)
        self.assertEqual(dashboard["stats"]["completed"], 1)
        self.assertEqual(dashboard["stats"]["failed"], 1)
        self.assertIn("success_rate", dashboard)
        self.assertGreaterEqual(len(dashboard["recent_tasks"]), 2)
        await manager.stop()

    async def test_cache_key_ignores_filename_but_not_owner(self):
        file_path = self.tmp_dir / "same-content.pdf"
        file_path.write_text("demo", encoding="utf-8")

        manager = AsyncTaskManager(worker_count=1)

        request_a = SubmitTaskRequest(
            filename="first-name.pdf",
            file_path=str(file_path),
            owner_id="user-a",
            parse_method="auto",
            lang="ch",
        )
        request_b = SubmitTaskRequest(
            filename="second-name.pdf",
            file_path=str(file_path),
            owner_id="user-b",
            parse_method="auto",
            lang="ch",
        )

        self.assertNotEqual(
            manager._build_cache_key(request_a),
            manager._build_cache_key(request_b),
        )

    async def test_stop_while_paused_does_not_hang(self):
        async def parser(path: str, request: SubmitTaskRequest) -> str:
            return "# ok"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser)
        await manager.start()
        await manager.pause_queue()

        file_path = self.tmp_dir / "stop-paused.pdf"
        file_path.write_text("demo", encoding="utf-8")
        task = await manager.submit(
            SubmitTaskRequest(filename="stop-paused.pdf", file_path=str(file_path))
        )
        canceled = await manager.cancel_task(task.task_id)
        self.assertTrue(canceled)

        await asyncio.wait_for(manager.stop(), timeout=1.0)

    async def test_queue_health_updates_after_cancel(self):
        async def parser(path: str, request: SubmitTaskRequest) -> str:
            return "# ok"

        manager = AsyncTaskManager(worker_count=1, parser_func=parser)
        await manager.start()
        await manager.pause_queue()

        file_path = self.tmp_dir / "queued-cancel.pdf"
        file_path.write_text("demo", encoding="utf-8")
        task = await manager.submit(
            SubmitTaskRequest(filename="queued-cancel.pdf", file_path=str(file_path))
        )

        health_before = await manager.get_queue_health()
        self.assertEqual(health_before.queued, 1)

        canceled = await manager.cancel_task(task.task_id)
        self.assertTrue(canceled)
        health_after = await manager.get_queue_health()
        self.assertEqual(health_after.queued, 0)

        await manager.resume_queue()
        await manager.stop()


if __name__ == "__main__":
    unittest.main()
