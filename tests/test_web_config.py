import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.state import TaskStateStore
from app.core.tasks import TaskRegistry
from app.web import config_api
from app.web.server import create_app


class DummyTask:
    def __init__(self, **_) -> None:
        pass

    async def run(self) -> None:
        return


class TestWebConfigApi(unittest.TestCase):
    def make_settings(self, temp_dir: str, token: str = "") -> SimpleNamespace:
        base = Path(temp_dir)
        config_dir = base / "config"
        config_dir.mkdir(exist_ok=True)
        return SimpleNamespace(
            CONFIG=config_dir / "config.yaml",
            CONFIG_DIR=config_dir,
            WebToken=token,
            APP_NAME="AutoFilm",
            APP_VERSION="test",
        )

    def test_summary_redacts_secret_fields(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fake_settings = self.make_settings(temp_dir)
            fake_settings.CONFIG.write_text(
                "Settings:\n  web_token: secret\nAlist2StrmList:\n"
                "  - id: AV\n    password: pass\n    token: alist-token\n",
                encoding="utf-8",
            )

            with patch.object(config_api, "settings", fake_settings):
                summary = config_api.config_summary()
                raw = config_api.read_config_text(reveal=False)

            self.assertEqual(summary["settings"]["web_token"], "***")
            self.assertIn("token: '***'", raw)
            self.assertIn("password: '***'", raw)

    def test_save_config_creates_backup_and_replaces_content(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fake_settings = self.make_settings(temp_dir, token="secret")
            fake_settings.CONFIG.write_text("Settings:\n  old: true\n", encoding="utf-8")

            with patch.object(config_api, "settings", fake_settings):
                result = config_api.save_config("Settings:\n  web_enabled: true\n")
                backups = config_api.list_backups()

            self.assertTrue(result["ok"])
            self.assertEqual(len(backups), 1)
            self.assertIn("web_enabled: true", fake_settings.CONFIG.read_text(encoding="utf-8"))


class TestWebConfigRoutes(unittest.TestCase):
    def make_client(self, temp_dir: str, token: str = "") -> tuple[TestClient, SimpleNamespace]:
        fake_settings = self.make_settings(temp_dir, token)
        fake_settings.CONFIG.write_text("Settings:\n  web_enabled: true\n", encoding="utf-8")
        registry = TaskRegistry(TaskStateStore(Path(temp_dir) / "state"))
        registry.replace_module("Alist2Strm", DummyTask, [{"id": "AV"}])
        app = create_app(registry, None)
        patcher = patch.object(config_api, "settings", fake_settings)
        patcher.start()
        self.addCleanup(patcher.stop)
        return TestClient(app), fake_settings

    def make_settings(self, temp_dir: str, token: str = "") -> SimpleNamespace:
        base = Path(temp_dir)
        config_dir = base / "config"
        config_dir.mkdir(exist_ok=True)
        return SimpleNamespace(
            CONFIG=config_dir / "config.yaml",
            CONFIG_DIR=config_dir,
            WebToken=token,
            APP_NAME="AutoFilm",
            APP_VERSION="test",
        )

    def test_config_write_requires_token(self) -> None:
        with TemporaryDirectory() as temp_dir:
            client, _ = self.make_client(temp_dir, token="")

            response = client.put(
                "/api/config/raw",
                json={"content": "Settings:\n  web_enabled: false\n"},
            )

            self.assertEqual(response.status_code, 403)

    def test_config_write_accepts_valid_token(self) -> None:
        with TemporaryDirectory() as temp_dir:
            client, fake_settings = self.make_client(temp_dir, token="secret")

            response = client.put(
                "/api/config/raw",
                headers={"Authorization": "Bearer secret"},
                json={"content": "Settings:\n  web_enabled: false\n"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn("web_enabled: false", fake_settings.CONFIG.read_text(encoding="utf-8"))

    def test_settings_form_update_accepts_valid_token(self) -> None:
        with TemporaryDirectory() as temp_dir:
            client, fake_settings = self.make_client(temp_dir, token="secret")

            response = client.put(
                "/api/config/settings",
                headers={"Authorization": "Bearer secret"},
                json={
                    "web_enabled": True,
                    "web_host": "0.0.0.0",
                    "web_port": 8001,
                    "hot_reload": True,
                    "hot_reload_interval": 15,
                },
            )

            content = fake_settings.CONFIG.read_text(encoding="utf-8")
            self.assertEqual(response.status_code, 200)
            self.assertIn("web_port: 8001", content)
            self.assertIn("hot_reload_interval: 15", content)

    def test_task_runs_endpoint_returns_history(self) -> None:
        with TemporaryDirectory() as temp_dir:
            client, _ = self.make_client(temp_dir)

            response = client.get("/api/tasks/Alist2Strm/AV/runs")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["history"], [])

    def test_index_returns_console_shell(self) -> None:
        with TemporaryDirectory() as temp_dir:
            client, _ = self.make_client(temp_dir)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("AutoFilm 控制台", response.text)
            self.assertIn("概览", response.text)
            self.assertIn("任务", response.text)
            self.assertIn("配置", response.text)
            self.assertIn("日志", response.text)
            self.assertIn("搜索任务", response.text)
            self.assertNotIn(">Dashboard<", response.text)
            self.assertNotIn(">Tasks<", response.text)
            self.assertNotIn(">Refresh<", response.text)


if __name__ == "__main__":
    unittest.main()
