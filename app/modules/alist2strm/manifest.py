"""扫描清单：支持增量扫描，跳过未变更的文件"""

import json
from datetime import datetime
from pathlib import Path
from re import sub as re_sub

from app.core import logger


class ScanManifest:
    """持久化的文件清单，用于增量扫描。

    Key 格式：
      - 普通文件：Alist full_path（用户根相对路径）
      - BDMV 目录： "bdmv:" + BDMV 根目录 full_path
    Value：{"mtime": float, "size": int, "processed_at": ISO字符串}
    """

    def __init__(self, target_dir: Path, task_id: str) -> None:
        safe_id = re_sub(r"[^\w\-]", "_", str(task_id))
        self._state_file = target_dir / f".autofilm_manifest_{safe_id}.json"
        self._entries: dict[str, dict] = {}

    def load(self) -> None:
        """从磁盘加载清单。缺失或损坏的文件视为空状态。"""
        if not self._state_file.exists():
            logger.info("未找到扫描清单，将执行全量扫描")
            return

        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data.get("entries", {})
            logger.info(
                f"加载扫描清单: {len(self._entries)} 个条目 ({self._state_file.name})"
            )
        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"加载扫描清单失败: {e}，将执行全量扫描")
            self._entries = {}

    def save(self) -> None:
        """原子持久化清单到磁盘（写入 .tmp 再 replace）"""
        temp_file = self._state_file.with_suffix(".tmp")
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "updated": datetime.now().isoformat(),
                        "entries": self._entries,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            temp_file.replace(self._state_file)
            logger.debug(f"扫描清单已保存: {len(self._entries)} 个条目")
        except OSError as e:
            logger.error(f"扫描清单保存失败: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    def is_changed(
        self, key: str, remote_mtime: float, remote_size: int
    ) -> bool:
        """返回 True 表示文件是新增或已变更。"""
        entry = self._entries.get(key)
        if entry is None:
            return True
        return (
            entry.get("mtime") != remote_mtime
            or entry.get("size") != remote_size
        )

    def mark_processed(
        self, key: str, remote_mtime: float, remote_size: int
    ) -> None:
        """记录文件已在本次扫描中成功处理。"""
        self._entries[key] = {
            "mtime": remote_mtime,
            "size": remote_size,
            "processed_at": datetime.now().isoformat(),
        }

    def prune_stale(self, known_keys: set[str]) -> None:
        """移除远程已不存在的文件条目。"""
        stale = set(self._entries) - known_keys
        for key in stale:
            del self._entries[key]
        if stale:
            logger.info(f"扫描清单清理 {len(stale)} 个过期条目")

    @property
    def entry_count(self) -> int:
        return len(self._entries)
