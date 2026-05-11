"""统一任务注册、运行和状态管理。"""

from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core import logger
from app.core.state import TaskStateStore
from app.utils.notify import send_notification


@dataclass(frozen=True)
class TaskDefinition:
    module_name: str
    task_id: str
    config: dict[str, Any]
    task_cls: type

    @property
    def key(self) -> str:
        return make_task_key(self.module_name, self.task_id)


def make_task_key(module_name: str, task_id: str) -> str:
    return f"{module_name}:{task_id}"


def get_task_id(config: dict[str, Any]) -> str:
    return str(config.get("id") or "<未命名>")


class TaskAlreadyRunningError(RuntimeError):
    """任务已在运行。"""


class TaskRegistry:
    """维护任务定义并提供统一执行入口。"""

    def __init__(self, state_store: TaskStateStore) -> None:
        self._state_store = state_store
        self._tasks: dict[str, TaskDefinition] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def replace_module(
        self,
        module_name: str,
        task_cls: type,
        configs: list[dict[str, Any]],
    ) -> list[TaskDefinition]:
        prefix = f"{module_name}:"
        for key in [key for key in self._tasks if key.startswith(prefix)]:
            del self._tasks[key]

        definitions = [
            TaskDefinition(module_name, get_task_id(config), dict(config), task_cls)
            for config in configs
        ]
        for definition in definitions:
            if definition.key in self._tasks:
                logger.warning(f"任务 ID 重复，后者覆盖前者：{definition.key}")
            self._tasks[definition.key] = definition
            self._locks.setdefault(definition.key, asyncio.Lock())
        return definitions

    def get(self, module_name: str, task_id: str) -> TaskDefinition | None:
        return self._tasks.get(make_task_key(module_name, task_id))

    def list_tasks(self, scheduler: Any | None = None) -> list[dict[str, Any]]:
        result = []
        for definition in sorted(self._tasks.values(), key=lambda item: item.key):
            state = dict(self._state_store.get(definition.key))
            job = scheduler.get_job(definition.key) if scheduler else None
            next_run_time = None
            if job and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()
            result.append(
                {
                    "key": definition.key,
                    "module": definition.module_name,
                    "id": definition.task_id,
                    "cron": definition.config.get("cron"),
                    "next_run_time": next_run_time,
                    "running": bool(state.get("running", False)),
                    "last_result": state.get("last_result"),
                    "last_error": state.get("last_error", ""),
                    "updated_at": state.get("updated_at"),
                }
            )
        return result

    def latest_run(self, module_name: str, task_id: str) -> dict[str, Any] | None:
        key = make_task_key(module_name, task_id)
        if key not in self._tasks:
            return None
        state = self._state_store.get(key)
        history = state.get("history")
        latest = history[0] if isinstance(history, list) and history else None
        return {"task": key, "latest": latest, "state": state}

    async def run(self, definition: TaskDefinition) -> bool:
        lock = self._locks.setdefault(definition.key, asyncio.Lock())
        if lock.locked():
            raise TaskAlreadyRunningError(f"任务正在运行：{definition.key}")

        async with lock:
            await send_notification(
                f"{definition.module_name} 任务开始",
                f"任务 [{definition.task_id}] 开始执行",
            )
            self._state_store.mark_started(definition.key)
            try:
                task = definition.task_cls(**definition.config)
                await task.run()
            except Exception as e:
                logger.error(
                    f"{definition.module_name} 任务 {definition.task_id} 执行失败：{e}"
                )
                logger.debug(traceback.format_exc())
                self._state_store.mark_finished(definition.key, False, str(e))
                await send_notification(
                    f"{definition.module_name} 任务失败",
                    f"任务 [{definition.task_id}] 执行失败：{e}",
                    "error",
                )
                return False

            self._state_store.mark_finished(definition.key, True)
            await send_notification(
                f"{definition.module_name} 任务完成",
                f"任务 [{definition.task_id}] 执行成功",
                "success",
            )
            return True

    async def run_by_id(self, module_name: str, task_id: str) -> bool:
        definition = self.get(module_name, task_id)
        if definition is None:
            raise KeyError(make_task_key(module_name, task_id))
        return await self.run(definition)

    async def run_at(self, module_name: str, task_id: str) -> dict[str, Any]:
        success = await self.run_by_id(module_name, task_id)
        return {
            "task": make_task_key(module_name, task_id),
            "success": success,
            "triggered_at": datetime.now().isoformat(),
        }
