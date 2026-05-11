"""轻量 API 和内置 Web UI。"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from app.core import settings
from app.core.tasks import TaskAlreadyRunningError, TaskRegistry


def _authorize(authorization: str | None = Header(default=None)) -> None:
    token = settings.WebToken
    if not token:
        return
    if authorization != f"Bearer {token}":
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

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> str:
        return _render_index(request)

    return app


def _render_index(request: Request) -> str:
    token_hint = "Token enabled" if settings.WebToken else "Token disabled"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoFilm</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: #f5f7fb; color: #1d2733; }}
    header {{ padding: 20px 28px; background: #ffffff; border-bottom: 1px solid #dde3ea; display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
    main {{ padding: 24px 28px; }}
    h1 {{ font-size: 22px; margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #dde3ea; }}
    th, td {{ padding: 12px 10px; text-align: left; border-bottom: 1px solid #eef2f6; font-size: 14px; }}
    th {{ background: #f9fbfd; color: #536170; }}
    button {{ border: 1px solid #1f6feb; background: #1f6feb; color: #fff; border-radius: 6px; padding: 7px 10px; cursor: pointer; }}
    button:disabled {{ opacity: .55; cursor: not-allowed; }}
    .muted {{ color: #667789; font-size: 13px; }}
    .error {{ color: #b42318; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>AutoFilm {settings.APP_VERSION}</h1>
      <div class="muted">{token_hint}</div>
    </div>
    <button onclick="loadTasks()">Refresh</button>
  </header>
  <main>
    <table>
      <thead>
        <tr><th>Task</th><th>Cron</th><th>Next Run</th><th>Status</th><th>Last Result</th><th>Action</th></tr>
      </thead>
      <tbody id="tasks"><tr><td colspan="6">Loading...</td></tr></tbody>
    </table>
  </main>
  <script>
    const token = localStorage.getItem("autofilm_token") || "";
    async function loadTasks() {{
      const res = await fetch("/api/tasks");
      const rows = await res.json();
      const tbody = document.getElementById("tasks");
      if (!rows.length) {{
        tbody.innerHTML = '<tr><td colspan="6">No tasks configured</td></tr>';
        return;
      }}
      tbody.innerHTML = rows.map(row => `
        <tr>
          <td>${{row.module}}:${{row.id}}</td>
          <td>${{row.cron || ""}}</td>
          <td>${{row.next_run_time || ""}}</td>
          <td>${{row.running ? "Running" : "Idle"}}</td>
          <td class="${{row.last_result === "error" ? "error" : ""}}">${{row.last_result || ""}} ${{row.last_error || ""}}</td>
          <td><button onclick="runTask('${{row.module}}', '${{row.id}}')" ${{row.running ? "disabled" : ""}}>Run</button></td>
        </tr>`).join("");
    }}
    async function runTask(moduleName, taskId) {{
      const headers = token ? {{ Authorization: `Bearer ${{token}}` }} : {{}};
      const res = await fetch(`/api/tasks/${{encodeURIComponent(moduleName)}}/${{encodeURIComponent(taskId)}}/run`, {{ method: "POST", headers }});
      if (!res.ok) alert(await res.text());
      await loadTasks();
    }}
    loadTasks();
  </script>
</body>
</html>"""
