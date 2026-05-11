import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.config import SettingManager


class TempSettingManager(SettingManager):
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        super().__init__()

    @property
    def BASE_DIR(self) -> Path:
        return self._base_dir


class TestSettingManager(unittest.TestCase):
    def test_missing_config_uses_safe_defaults(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings = TempSettingManager(Path(temp_dir))

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.AlistServerList, [])
            self.assertEqual(settings.Ani2AlistList, [])
            self.assertEqual(settings.LibraryPosterList, [])
            self.assertTrue(settings.CONFIG_DIR.exists())
            self.assertTrue(settings.LOG_DIR.exists())

    def test_empty_config_uses_safe_defaults(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            config_dir = base_dir / "config"
            config_dir.mkdir()
            (config_dir / "config.yaml").write_text("", encoding="utf-8")

            settings = TempSettingManager(base_dir)

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.AlistServerList, [])

    def test_non_mapping_config_fails_clearly(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            config_dir = base_dir / "config"
            config_dir.mkdir()
            (config_dir / "config.yaml").write_text("- item\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "顶层必须是 YAML 映射"):
                TempSettingManager(base_dir)


if __name__ == "__main__":
    unittest.main()
