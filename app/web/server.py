"""轻量 API 和内置 Web UI。"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse

from app.core import settings
from app.core.tasks import TaskAlreadyRunningError, TaskRegistry
from app.web.config_api import (
    ConfigPayload,
    SettingsPayload,
    config_summary,
    has_write_token,
    is_authorized,
    list_backups,
    read_config_text,
    restore_backup,
    save_config,
    update_settings,
    load_yaml,
)
from app.web.ui import render_index


def _authorize(authorization: str | None = Header(default=None)) -> None:
    token = settings.WebToken
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def _require_write_token(authorization: str | None = Header(default=None)) -> None:
    if not has_write_token():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Web token is required before config writes are enabled",
        )
    if not is_authorized(authorization):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def create_app(registry: TaskRegistry, scheduler) -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/api/tasks")
    async def list_tasks() -> list[dict]:
        return registry.list_tasks(scheduler)

    @app.post(
        "/api/tasks/{module_name}/{task_id}/run",
        dependencies=[Depends(_authorize)],
    )
    async def run_task(module_name: str, task_id: str) -> dict:
        definition = registry.get(module_name, task_id)
        if definition is None:
            raise HTTPException(status_code=404, detail="Task not found")
        try:
            return await registry.run_at(module_name, task_id)
        except TaskAlreadyRunningError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @app.get("/api/tasks/{module_name}/{task_id}/runs/latest")
    async def latest_run(module_name: str, task_id: str) -> dict:
        data = registry.latest_run(module_name, task_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return data

    @app.get("/api/tasks/{module_name}/{task_id}/runs")
    async def runs(module_name: str, task_id: str) -> dict:
        data = registry.runs(module_name, task_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return data

    @app.get("/api/config/summary")
    async def get_config_summary() -> dict:
        return config_summary()

    @app.get("/api/config/raw")
    async def get_config_raw(
        reveal: bool = False,
        authorization: str | None = Header(default=None),
    ) -> dict:
        if reveal and not is_authorized(authorization):
            raise HTTPException(status_code=401, detail="Unauthorized")
        return {
            "content": read_config_text(reveal=reveal),
            "redacted": not reveal,
            "write_enabled": has_write_token(),
        }

    @app.post("/api/config/validate")
    async def validate_config(payload: ConfigPayload) -> dict:
        try:
            data = load_yaml(payload.content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"ok": True, "sections": list(data.keys())}

    @app.put("/api/config/raw", dependencies=[Depends(_require_write_token)])
    async def put_config_raw(payload: ConfigPayload) -> dict:
        try:
            return save_config(payload.content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.put("/api/config/settings", dependencies=[Depends(_require_write_token)])
    async def put_config_settings(payload: SettingsPayload) -> dict:
        try:
            return update_settings(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get("/api/config/backups")
    async def get_config_backups() -> list[dict]:
        return list_backups()

    @app.post(
        "/api/config/backup/{name}/restore",
        dependencies=[Depends(_require_write_token)],
    )
    async def post_restore_backup(name: str) -> dict:
        try:
            return restore_backup(name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return render_index()

    return app
