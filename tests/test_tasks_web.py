import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.testclient import TestClient

from app.core.state import TaskStateStore
from app.core.tasks import TaskAlreadyRunningError, TaskRegistry
from app.main import add_scheduled_jobs
from app.web.server import create_app


class DummyTask:
    runs = 0

    def __init__(self, **_) -> None:
        pass

    async def run(self) -> None:
        type(self).runs += 1


class TestTaskRegistry(unittest.IsolatedAsyncioTestCase):
    async def test_scheduled_job_uses_module_scoped_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry = TaskRegistry(TaskStateStore(Path(temp_dir)))
            scheduler = AsyncIOScheduler()
            alist_defs = registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV", "cron": "0 0 * * *"}])

            add_scheduled_jobs(scheduler, registry, alist_defs)

            self.assertIsNotNone(scheduler.get_job("Alist2Strm:AV"))

    async def test_run_updates_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            DummyTask.runs = 0
            store = TaskStateStore(Path(temp_dir))
            registry = TaskRegistry(store)
            definition = registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV"}])[0]

            success = await registry.run(definition)

            self.assertTrue(success)
            self.assertEqual(DummyTask.runs, 1)
            self.assertEqual(store.get("Alist2Strm:AV")["last_result"], "success")

    async def test_running_task_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry = TaskRegistry(TaskStateStore(Path(temp_dir)))
            definition = registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV"}])[0]
            lock = registry._locks[definition.key]

            await lock.acquire()
            try:
                with self.assertRaises(TaskAlreadyRunningError):
                    await registry.run(definition)
            finally:
                lock.release()


class TestWebApi(unittest.TestCase):
    def test_health_and_tasks_api(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry = TaskRegistry(TaskStateStore(Path(temp_dir)))
            registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV", "cron": "0 0 * * *"}])
            app = create_app(registry, None)
            client = TestClient(app)

            self.assertEqual(client.get("/health").status_code, 200)
            tasks = client.get("/api/tasks").json()

            self.assertEqual(tasks[0]["key"], "Alist2Strm:AV")

    def test_run_task_api(self) -> None:
        with TemporaryDirectory() as temp_dir:
            DummyTask.runs = 0
            registry = TaskRegistry(TaskStateStore(Path(temp_dir)))
            registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV"}])
            app = create_app(registry, None)
            client = TestClient(app)

            response = client.post("/api/tasks/Alist2Strm/AV/run")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(DummyTask.runs, 1)


if __name__ == "__main__":
    unittest.main()
