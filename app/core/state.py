"""任务运行状态持久化。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core import logger


class TaskStateStore:
    """保存任务最近运行状态和有限历史记录。"""

    def __init__(self, state_dir: Path, history_limit: int = 20) -> None:
        self._state_dir = state_dir
        self._state_file = state_dir / "tasks.json"
        self._history_limit = max(1, history_limit)
        self._state: dict[str, Any] = {"tasks": {}}
        self.load()

    def load(self) -> None:
        if not self._state_file.exists():
            return
        try:
            with self._state_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"任务状态加载失败，将使用空状态：{e}")
            self._state = {"tasks": {}}
            return

        self._state = data if isinstance(data, dict) else {"tasks": {}}
        if not isinstance(self._state.get("tasks"), dict):
            self._state["tasks"] = {}

    def save(self) -> None:
        temp_file = self._state_file.with_suffix(".tmp")
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            with temp_file.open("w", encoding="utf-8") as file:
                json.dump(self._state, file, ensure_ascii=False, indent=2)
            temp_file.replace(self._state_file)
        except OSError as e:
            logger.error(f"任务状态保存失败：{e}")
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except OSError:
                pass

    def snapshot(self) -> dict[str, Any]:
        return self._state

    def get(self, key: str) -> dict[str, Any]:
        task_state = self._state.setdefault("tasks", {}).setdefault(key, {})
        return task_state if isinstance(task_state, dict) else {}

    def mark_started(self, key: str) -> None:
        now = datetime.now().isoformat()
        state = self.get(key)
        state.update(
            {
                "running": True,
                "started_at": now,
                "updated_at": now,
                "last_error": "",
            }
        )
        self._state["tasks"][key] = state
        self.save()

    def mark_finished(self, key: str, success: bool, error: str = "") -> None:
        now = datetime.now().isoformat()
        state = self.get(key)
        started_at = state.get("started_at")
        run = {
            "started_at": started_at,
            "finished_at": now,
            "success": success,
            "error": error,
        }
        history = state.get("history")
        if not isinstance(history, list):
            history = []
        history.insert(0, run)
        del history[self._history_limit :]

        state.update(
            {
                "running": False,
                "updated_at": now,
                "last_result": "success" if success else "error",
                "last_error": error,
                "history": history,
            }
        )
        self._state["tasks"][key] = state
        self.save()
