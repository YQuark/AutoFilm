import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.modules.alist2strm.alist2strm import Alist2Strm
from app.modules.alist2strm.manifest import ScanManifest
from app.modules.alist2strm.strm_protection import StrmProtectionManager


class TestAlist2StrmPaths(unittest.TestCase):
    def make_instance(self, source_dir: str) -> Alist2Strm:
        instance = object.__new__(Alist2Strm)
        instance.source_dir = Alist2Strm._normalize_remote_dir(source_dir)
        return instance

    def test_normalizes_remote_source_dir(self) -> None:
        self.assertEqual(Alist2Strm._normalize_remote_dir("/media/"), "/media")
        self.assertEqual(Alist2Strm._normalize_remote_dir("media"), "/media")
        self.assertEqual(Alist2Strm._normalize_remote_dir("/"), "/")

    def test_relative_remote_path_respects_directory_boundary(self) -> None:
        instance = self.make_instance("/media")

        self.assertEqual(instance._relative_remote_path("/media/movie/a.mkv"), "movie/a.mkv")
        self.assertEqual(instance._relative_remote_path("/media-other/a.mkv"), "media-other/a.mkv")

    def test_relative_remote_path_for_root_source(self) -> None:
        instance = self.make_instance("/")

        self.assertEqual(instance._relative_remote_path("/movie/a.mkv"), "movie/a.mkv")

    def test_normalizes_custom_extension(self) -> None:
        self.assertEqual(Alist2Strm._normalize_ext(" md "), ".md")
        self.assertEqual(Alist2Strm._normalize_ext(".ZIP"), ".zip")


class TestStrmProtectionManager(unittest.TestCase):
    def test_state_file_parent_is_created_on_save(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "nested" / "target"
            manager = StrmProtectionManager(target_dir, "task:id", threshold=1, grace_scans=2)
            manager.protected["movie/a.strm"] = 1

            manager.save()

            self.assertTrue((target_dir / ".autofilm_strm_task_id.json").exists())

    def test_grace_scans_delay_large_delete(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            file_path = target_dir / "a.strm"
            file_path.write_text("url", encoding="utf-8")
            manager = StrmProtectionManager(target_dir, "task", threshold=1, grace_scans=2)

            first = manager.process({file_path}, set())
            second = manager.process({file_path}, set())

            self.assertEqual(first, set())
            self.assertEqual(second, {file_path})


class TestScanManifest(unittest.TestCase):
    def test_directory_entries_are_change_checked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            manifest = ScanManifest(Path(temp_dir), "task")

            manifest.mark_directory("/media/anime", 100.0, 0)

            self.assertFalse(
                manifest.is_changed(manifest.dir_key("/media/anime"), 100.0, 0)
            )
            self.assertTrue(
                manifest.is_changed(manifest.dir_key("/media/anime"), 101.0, 0)
            )

    def test_prune_stale_preserves_skipped_directory_subtree(self) -> None:
        with TemporaryDirectory() as temp_dir:
            manifest = ScanManifest(Path(temp_dir), "task")
            manifest.mark_directory("/media/anime", 100.0, 0)
            manifest.mark_processed("/media/anime/a.mp4", 100.0, 10)
            manifest.mark_processed("bdmv:/media/anime/movie", 100.0, 20)
            manifest.mark_processed("/media/movie/b.mp4", 100.0, 30)

            manifest.prune_stale(
                {manifest.dir_key("/media/anime")}, preserved_prefixes={"/media/anime"}
            )

            self.assertFalse(manifest.is_changed("/media/anime/a.mp4", 100.0, 10))
            self.assertFalse(
                manifest.is_changed("bdmv:/media/anime/movie", 100.0, 20)
            )
            self.assertTrue(manifest.is_changed("/media/movie/b.mp4", 100.0, 30))


if __name__ == "__main__":
    unittest.main()
