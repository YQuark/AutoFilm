"""轻量 API 和内置 Web UI。"""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import settings
from app.core.tasks import TaskAlreadyRunningError, TaskRegistry
from app.web.config_api import (
    ConfigPayload,
    SettingsPayload,
    config_summary,
    list_backups,
    read_config_text,
    restore_backup,
    save_config,
    update_settings,
    load_yaml,
    delete_backup,
)
from app.web.ui import render_index


_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_WRITE_PATH_PREFIXES = ("/api/config/",)
_RUN_PATH_PREFIX = "/api/tasks/"


class _RateLimiter(BaseHTTPMiddleware):
    """简单滑动窗口限流中间件。

    读请求: 120次/分钟
    写请求: 30次/分钟
    任务触发: 10次/分钟
    """

    _WINDOW_S = 60
    _READ_LIMIT = 120
    _WRITE_LIMIT = 30
    _RUN_LIMIT = 10

    def __init__(self, app) -> None:
        super().__init__(app)
        self._buckets: defaultdict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取最右侧 IP（离服务最近的代理），防止伪造
            parts = [ip.strip() for ip in forwarded.split(",")]
            if parts:
                return parts[-1]
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        host = request.client.host if request.client else "unknown"
        return host

    def _prune(self, key: str, now: float) -> None:
        cutoff = now - self._WINDOW_S
        self._buckets[key] = [
            stamp for stamp in self._buckets[key] if stamp > cutoff
        ]

    async def dispatch(self, request: Request, call_next):
        ip = self._client_ip(request)
        now = time.monotonic()
        path = request.url.path
        method = request.method.upper()

        # GET/HEAD/OPTIONS 一律走读限流，不因路径前缀误判
        if method in ("GET", "HEAD", "OPTIONS"):
            limits = (self._READ_LIMIT, "120次/分钟")
        elif path.startswith(_RUN_PATH_PREFIX) and method in _WRITE_METHODS:
            limits = (self._RUN_LIMIT, "10次/分钟")
        elif method in _WRITE_METHODS:
            limits = (self._WRITE_LIMIT, "30次/分钟")
        else:
            limits = (self._READ_LIMIT, "120次/分钟")

        key = f"{ip}:{limits[0]}"
        self._prune(key, now)

        if len(self._buckets[key]) >= limits[0]:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁（{limits[1]}），请稍后再试",
                headers={"Retry-After": str(self._WINDOW_S)},
            )

        self._buckets[key].append(now)
        return await call_next(request)


def create_app(registry: TaskRegistry, scheduler) -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
    app.add_middleware(_RateLimiter)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/api/tasks")
    async def list_tasks() -> list[dict]:
        return registry.list_tasks(scheduler)

    @app.post("/api/tasks/{module_name}/{task_id}/run")
    async def run_task(module_name: str, task_id: str) -> dict:
        definition = registry.get(module_name, task_id)
        if definition is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        try:
            return await registry.run_at(module_name, task_id)
        except TaskAlreadyRunningError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @app.get("/api/tasks/{module_name}/{task_id}/runs/latest")
    async def latest_run(module_name: str, task_id: str) -> dict:
        data = registry.latest_run(module_name, task_id)
        if data is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return data

    @app.get("/api/tasks/{module_name}/{task_id}/runs")
    async def runs(module_name: str, task_id: str) -> dict:
        data = registry.runs(module_name, task_id)
        if data is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return data

    @app.get("/api/config/summary")
    async def get_config_summary() -> dict:
        return config_summary()

    @app.get("/api/config/raw")
    async def get_config_raw() -> dict:
        return {
            "content": read_config_text(reveal=True),
            "redacted": False,
        }

    @app.post("/api/config/validate")
    async def validate_config(payload: ConfigPayload) -> dict:
        try:
            data = load_yaml(payload.content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"ok": True, "sections": list(data.keys())}

    @app.put("/api/config/raw")
    async def put_config_raw(payload: ConfigPayload) -> dict:
        try:
            return save_config(payload.content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.put("/api/config/settings")
    async def put_config_settings(payload: SettingsPayload) -> dict:
        try:
            return update_settings(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get("/api/config/backups")
    async def get_config_backups() -> list[dict]:
        return list_backups()

    @app.post("/api/config/backup/{name}/restore")
    async def post_restore_backup(name: str) -> dict:
        try:
            return restore_backup(name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @app.delete("/api/config/backup/{name}")
    async def delete_config_backup(name: str) -> dict:
        try:
            delete_backup(name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"ok": True}

    @app.get("/api/logs")
    async def get_logs(lines: int = Query(default=200, ge=1, le=2000), level: str = Query(default="")) -> dict:
        today = time.strftime("%Y-%m-%d")
        log_path = settings.LOG_DIR / f"{today}.log"
        if not log_path.exists():
            return {"date": today, "lines": 0, "entries": []}

        try:
            raw = log_path.read_text(encoding="utf-8")
        except OSError:
            return {"date": today, "lines": 0, "entries": []}

        all_lines = raw.strip().split("\n")
        selected = all_lines[-lines:]
        if level:
            level_upper = level.upper()
            selected = [l for l in selected if f"【{level_upper}】" in l]

        return {"date": today, "lines": len(selected), "entries": selected}

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return render_index()

    return app
