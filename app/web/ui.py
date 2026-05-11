"""内置无构建控制台 UI。"""

from __future__ import annotations

from app.core import settings


def render_index() -> str:
    return HTML.replace("__VERSION__", settings.APP_VERSION)


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoFilm 控制台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fb;
      --surface: #ffffff;
      --surface-2: #edf2f7;
      --line: #dbe3ec;
      --text: #17202a;
      --muted: #607080;
      --primary: #1769aa;
      --primary-strong: #0f4c81;
      --ok: #147d4f;
      --warn: #9a5b00;
      --bad: #b42318;
      --focus: #6aa9ff;
      --radius: 8px;
      --pad: 16px;
    }
    [data-theme="dark"] {
      color-scheme: dark;
      --bg: #101820;
      --surface: #18232e;
      --surface-2: #223140;
      --line: #324657;
      --text: #edf4fb;
      --muted: #a8b6c4;
      --primary: #6aa9ff;
      --primary-strong: #9fc7ff;
      --ok: #62c78f;
      --warn: #f0b85a;
      --bad: #ff8b7e;
      --focus: #9fc7ff;
    }
    [data-density="compact"] { --pad: 10px; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100dvh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 16px;
      line-height: 1.5;
    }
    a, button, input, select, textarea { font: inherit; }
    button, select, input, textarea {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface);
      color: var(--text);
    }
    button {
      min-height: 44px;
      padding: 0 14px;
      cursor: pointer;
    }
    button.primary {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }
    button.ghost { background: transparent; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    :focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
    .shell {
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      min-height: 100dvh;
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--surface);
      padding: 18px;
    }
    main { min-width: 0; }
    header {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: color-mix(in srgb, var(--surface) 94%, transparent);
      backdrop-filter: blur(10px);
    }
    h1, h2, h3 { margin: 0; line-height: 1.2; }
    h1 { font-size: 22px; }
    h2 { font-size: 18px; margin-bottom: 12px; }
    h3 { font-size: 15px; }
    .brand { display: grid; gap: 4px; margin-bottom: 22px; }
    .version, .muted { color: var(--muted); font-size: 13px; }
    nav { display: grid; gap: 8px; }
    nav button {
      justify-content: flex-start;
      text-align: left;
      border-color: transparent;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    nav button.active { background: var(--surface-2); border-color: var(--line); }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .content { padding: 22px; display: grid; gap: 18px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: var(--pad);
    }
    .metric { display: grid; gap: 6px; min-height: 94px; }
    .metric strong { font-size: 28px; font-variant-numeric: tabular-nums; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 13px;
      background: var(--surface-2);
    }
    .dot { width: 8px; height: 8px; border-radius: 999px; background: var(--muted); }
    .ok .dot { background: var(--ok); }
    .bad .dot { background: var(--bad); }
    .warn .dot { background: var(--warn); }
    table { width: 100%; border-collapse: collapse; }
    th, td {
      padding: 11px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }
    th { color: var(--muted); font-weight: 600; background: var(--surface-2); }
    .task-cards { display: none; gap: 12px; }
    [data-view="cards"] .table-wrap { display: none; }
    [data-view="cards"] .task-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .task-card { display: grid; gap: 10px; }
    .row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .split { display: grid; grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr); gap: 14px; align-items: start; }
    .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 13px; }
    input, select { min-height: 42px; padding: 8px 10px; }
    textarea {
      width: 100%;
      min-height: 460px;
      padding: 12px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      line-height: 1.45;
      tab-size: 2;
    }
    .hidden { display: none !important; }
    .notice { border-left: 4px solid var(--primary); padding: 10px 12px; background: var(--surface-2); }
    .error-text { color: var(--bad); }
    .success-text { color: var(--ok); }
    @media (max-width: 920px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      header { position: static; align-items: flex-start; flex-direction: column; }
      .grid, .split, .form-grid { grid-template-columns: 1fr; }
      .table-wrap { display: none; }
      .task-cards, [data-view="cards"] .task-cards { display: grid; grid-template-columns: 1fr; }
    }
    @media (prefers-color-scheme: dark) {
      [data-theme="system"] {
        color-scheme: dark;
        --bg: #101820;
        --surface: #18232e;
        --surface-2: #223140;
        --line: #324657;
        --text: #edf4fb;
        --muted: #a8b6c4;
        --primary: #6aa9ff;
        --primary-strong: #9fc7ff;
        --ok: #62c78f;
        --warn: #f0b85a;
        --bad: #ff8b7e;
        --focus: #9fc7ff;
      }
    }
  </style>
</head>
<body data-theme="system" data-density="comfortable" data-view="table">
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>AutoFilm</h1>
        <span class="version">__VERSION__</span>
      </div>
      <nav aria-label="主导航">
        <button class="active" data-page="dashboard" type="button">Dashboard</button>
        <button data-page="tasks" type="button">Tasks</button>
        <button data-page="config" type="button">Config</button>
        <button data-page="settings" type="button">Preferences</button>
      </nav>
    </aside>
    <main>
      <header>
        <div>
          <h1 id="page-title">Dashboard</h1>
          <div class="muted" id="health-line">Checking service...</div>
        </div>
        <div class="toolbar">
          <input id="token-input" type="password" autocomplete="current-password" placeholder="Web token">
          <button id="save-token" type="button">Save token</button>
          <button id="refresh" class="primary" type="button">Refresh</button>
        </div>
      </header>
      <section class="content" id="page-dashboard">
        <div class="grid" id="metrics"></div>
        <div class="panel">
          <h2>Recent Activity</h2>
          <div id="recent-activity" class="muted">No activity</div>
        </div>
      </section>
      <section class="content hidden" id="page-tasks">
        <div class="panel">
          <div class="toolbar">
            <h2 style="margin-right:auto">Tasks</h2>
            <select id="module-filter" aria-label="Module filter">
              <option value="">All modules</option>
              <option value="Alist2Strm">Alist2Strm</option>
              <option value="Ani2Alist">Ani2Alist</option>
            </select>
            <select id="view-mode" aria-label="View mode">
              <option value="table">Table</option>
              <option value="cards">Cards</option>
            </select>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Task</th><th>Cron</th><th>Next run</th><th>Status</th><th>Last result</th><th>Action</th></tr>
              </thead>
              <tbody id="task-rows"></tbody>
            </table>
          </div>
          <div class="task-cards" id="task-cards"></div>
        </div>
        <div class="panel">
          <h2>Run History</h2>
          <div id="run-history" class="muted">Select a task.</div>
        </div>
      </section>
      <section class="content hidden" id="page-config">
        <div class="split">
          <div class="panel">
            <h2>Config Summary</h2>
            <div id="config-summary" class="muted">Loading...</div>
            <h2 style="margin-top:18px">Settings Form</h2>
            <div class="form-grid">
              <label>Web enabled
                <select id="cfg-web-enabled">
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              </label>
              <label>Web host
                <input id="cfg-web-host" type="text" placeholder="0.0.0.0">
              </label>
              <label>Web port
                <input id="cfg-web-port" type="number" min="1" max="65535" placeholder="8000">
              </label>
              <label>Web token
                <input id="cfg-web-token" type="password" placeholder="Leave blank to keep unchanged">
              </label>
              <label>Hot reload
                <select id="cfg-hot-reload">
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              </label>
              <label>Reload interval
                <input id="cfg-hot-reload-interval" type="number" min="5" placeholder="30">
              </label>
            </div>
            <div class="toolbar" style="margin-top:12px">
              <button id="save-settings" class="primary" type="button">Save settings form</button>
            </div>
            <h2 style="margin-top:18px">Backups</h2>
            <div id="backups" class="muted">No backups</div>
          </div>
          <div class="panel">
            <div class="toolbar">
              <h2 style="margin-right:auto">YAML Editor</h2>
              <button id="validate-config" type="button">Validate</button>
              <button id="save-config" class="primary" type="button">Save</button>
            </div>
            <div id="config-notice" class="notice">Writing config requires a Web token.</div>
            <textarea id="config-editor" spellcheck="false" aria-label="config.yaml editor"></textarea>
          </div>
        </div>
      </section>
      <section class="content hidden" id="page-settings">
        <div class="panel">
          <h2>Display</h2>
          <div class="form-grid">
            <label>Theme
              <select id="theme-select">
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </label>
            <label>Density
              <select id="density-select">
                <option value="comfortable">Comfortable</option>
                <option value="compact">Compact</option>
              </select>
            </label>
            <label>Auto refresh
              <select id="refresh-select">
                <option value="0">Off</option>
                <option value="15">15s</option>
                <option value="30">30s</option>
                <option value="60">60s</option>
              </select>
            </label>
          </div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const state = { tasks: [], summary: null, backups: [], refreshTimer: null };
    const $ = (id) => document.getElementById(id);
    const token = () => localStorage.getItem("autofilm_token") || "";
    const authHeaders = () => token() ? { Authorization: `Bearer ${token()}` } : {};
    function setText(id, text) { $(id).textContent = text; }
    function fmt(value) { return value || ""; }
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));
    }
    function showPage(name) {
      document.querySelectorAll("nav button").forEach((btn) => btn.classList.toggle("active", btn.dataset.page === name));
      document.querySelectorAll("main > section").forEach((section) => section.classList.add("hidden"));
      $(`page-${name}`).classList.remove("hidden");
      setText("page-title", name.charAt(0).toUpperCase() + name.slice(1));
      if (name === "config") loadConfig();
    }
    function applyPrefs() {
      document.body.dataset.theme = localStorage.getItem("autofilm_theme") || "system";
      document.body.dataset.density = localStorage.getItem("autofilm_density") || "comfortable";
      document.body.dataset.view = localStorage.getItem("autofilm_view") || "table";
      $("theme-select").value = document.body.dataset.theme;
      $("density-select").value = document.body.dataset.density;
      $("view-mode").value = document.body.dataset.view;
      $("refresh-select").value = localStorage.getItem("autofilm_refresh") || "0";
      scheduleRefresh();
    }
    function scheduleRefresh() {
      if (state.refreshTimer) clearInterval(state.refreshTimer);
      const seconds = Number(localStorage.getItem("autofilm_refresh") || "0");
      if (seconds > 0) state.refreshTimer = setInterval(loadAll, seconds * 1000);
    }
    async function api(path, options = {}) {
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }
    async function loadAll() {
      try {
        const health = await api("/health");
        setText("health-line", `Service ok · ${health.version}`);
      } catch (error) {
        setText("health-line", "Service unavailable");
      }
      await loadTasks();
      await loadSummary();
    }
    async function loadTasks() {
      state.tasks = await api("/api/tasks");
      renderMetrics();
      renderTasks();
      renderRecent();
    }
    async function loadSummary() {
      state.summary = await api("/api/config/summary");
      renderConfigSummary();
    }
    function filteredTasks() {
      const moduleName = $("module-filter").value;
      return state.tasks.filter((task) => !moduleName || task.module === moduleName);
    }
    function renderMetrics() {
      const total = state.tasks.length;
      const running = state.tasks.filter((task) => task.running).length;
      const failed = state.tasks.filter((task) => task.last_result === "error").length;
      const ok = state.tasks.filter((task) => task.last_result === "success").length;
      $("metrics").innerHTML = [
        ["Tasks", total, "Configured jobs"],
        ["Running", running, "Active now"],
        ["Success", ok, "Latest result"],
        ["Errors", failed, "Need attention"],
      ].map(([label, value, hint]) => `<div class="panel metric"><span class="muted">${label}</span><strong>${value}</strong><span class="muted">${hint}</span></div>`).join("");
    }
    function statusPill(task) {
      const cls = task.running ? "warn" : task.last_result === "error" ? "bad" : task.last_result === "success" ? "ok" : "";
      const label = task.running ? "Running" : task.last_result || "Idle";
      return `<span class="status ${cls}"><span class="dot"></span>${escapeHtml(label)}</span>`;
    }
    function renderTasks() {
      const rows = filteredTasks();
      $("task-rows").innerHTML = rows.map((task) => `
        <tr>
          <td><strong>${escapeHtml(task.module)}:${escapeHtml(task.id)}</strong><div class="muted">${escapeHtml(task.key)}</div></td>
          <td>${escapeHtml(fmt(task.cron))}</td>
          <td>${escapeHtml(fmt(task.next_run_time))}</td>
          <td>${statusPill(task)}</td>
          <td>${escapeHtml(task.last_error || task.last_result || "")}</td>
          <td class="row-actions">${taskButtons(task)}</td>
        </tr>`).join("") || '<tr><td colspan="6" class="muted">No tasks</td></tr>';
      $("task-cards").innerHTML = rows.map((task) => `
        <div class="panel task-card">
          <h3>${escapeHtml(task.module)}:${escapeHtml(task.id)}</h3>
          ${statusPill(task)}
          <div class="muted">Cron: ${escapeHtml(fmt(task.cron))}</div>
          <div class="muted">Next: ${escapeHtml(fmt(task.next_run_time))}</div>
          <div class="row-actions">${taskButtons(task)}</div>
        </div>`).join("");
    }
    function taskButtons(task) {
      return `<button class="primary" type="button" aria-label="Run ${escapeHtml(task.key)}" onclick="runTask('${escapeHtml(task.module)}','${escapeHtml(task.id)}')" ${task.running ? "disabled" : ""}>Run</button>
        <button type="button" aria-label="Show history ${escapeHtml(task.key)}" onclick="loadHistory('${escapeHtml(task.module)}','${escapeHtml(task.id)}')">History</button>`;
    }
    async function runTask(moduleName, taskId) {
      try {
        await api(`/api/tasks/${encodeURIComponent(moduleName)}/${encodeURIComponent(taskId)}/run`, { method: "POST", headers: authHeaders() });
        await loadTasks();
      } catch (error) {
        alert(error.message);
      }
    }
    async function loadHistory(moduleName, taskId) {
      const data = await api(`/api/tasks/${encodeURIComponent(moduleName)}/${encodeURIComponent(taskId)}/runs`);
      $("run-history").innerHTML = data.history.length ? data.history.map((run) => `
        <div class="panel" style="margin-top:10px">
          <strong>${run.success ? "Success" : "Error"}</strong>
          <div class="muted">${escapeHtml(run.started_at || "")} → ${escapeHtml(run.finished_at || "")}</div>
          <div class="error-text">${escapeHtml(run.error || "")}</div>
        </div>`).join("") : "No history";
      showPage("tasks");
    }
    function renderRecent() {
      const items = state.tasks.filter((task) => task.updated_at).slice(0, 6);
      $("recent-activity").innerHTML = items.length ? items.map((task) => `<div>${statusPill(task)} ${escapeHtml(task.key)} <span class="muted">${escapeHtml(task.updated_at)}</span></div>`).join("") : "No activity";
    }
    async function loadConfig() {
      const reveal = token() ? "?reveal=true" : "";
      let raw;
      try {
        raw = await api(`/api/config/raw${reveal}`, { headers: authHeaders() });
      } catch (error) {
        raw = await api("/api/config/raw");
      }
      $("config-editor").value = raw.content || "";
      $("config-notice").textContent = raw.write_enabled ? "Token active. Saving creates a backup and applies config.yaml atomically." : "Read-only mode. Set Web token to enable saving.";
      await loadSummary();
      state.backups = await api("/api/config/backups");
      renderBackups();
    }
    function renderConfigSummary() {
      if (!state.summary) return;
      const counts = state.summary.counts || {};
      const settings = state.summary.settings || {};
      $("config-summary").innerHTML = `
        <div class="muted">Path: ${escapeHtml(state.summary.path)}</div>
        <div style="margin-top:10px">Alist2Strm: <strong>${counts.alist2strm || 0}</strong></div>
        <div>Ani2Alist: <strong>${counts.ani2alist || 0}</strong></div>
        <div>Notifiers: <strong>${counts.notifiers || 0}</strong></div>
        <div>Write: <strong>${state.summary.write_enabled ? "enabled" : "read-only"}</strong></div>
        <h3 style="margin-top:14px">Alist2Strm</h3>
        ${(state.summary.alist2strm || []).map((task) => `<div class="notice" style="margin-top:8px"><strong>${escapeHtml(task.id)}</strong><div class="muted">${escapeHtml(task.mode || "")} · ${escapeHtml(task.source_dir || "")} → ${escapeHtml(task.target_dir || "")}</div></div>`).join("") || '<div class="muted">No tasks</div>'}`;
      $("cfg-web-enabled").value = String(Boolean(settings.web_enabled));
      $("cfg-web-host").value = settings.web_host || "0.0.0.0";
      $("cfg-web-port").value = settings.web_port || 8000;
      $("cfg-hot-reload").value = String(settings.hot_reload !== false);
      $("cfg-hot-reload-interval").value = settings.hot_reload_interval || 30;
    }
    function renderBackups() {
      $("backups").innerHTML = state.backups.length ? state.backups.map((backup) => `
        <div class="notice" style="margin-top:8px">
          <strong>${escapeHtml(backup.name)}</strong>
          <div class="muted">${escapeHtml(backup.modified)} · ${backup.size} bytes</div>
          <button type="button" onclick="restoreBackup('${escapeHtml(backup.name)}')">Restore</button>
        </div>`).join("") : "No backups";
    }
    async function validateConfig() {
      const result = await api("/api/config/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: $("config-editor").value }),
      });
      $("config-notice").textContent = result.ok ? "YAML is valid." : "Invalid config.";
    }
    async function saveConfig() {
      try {
        const result = await api("/api/config/raw", {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({ content: $("config-editor").value }),
        });
        $("config-notice").textContent = `Saved. Backup: ${result.backup || "none"}`;
        await loadConfig();
      } catch (error) {
        $("config-notice").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    }
    async function saveSettingsForm() {
      try {
        const payload = {
          web_enabled: $("cfg-web-enabled").value === "true",
          web_host: $("cfg-web-host").value || "0.0.0.0",
          web_port: Number($("cfg-web-port").value || 8000),
          hot_reload: $("cfg-hot-reload").value === "true",
          hot_reload_interval: Number($("cfg-hot-reload-interval").value || 30),
        };
        if ($("cfg-web-token").value) payload.web_token = $("cfg-web-token").value;
        const result = await api("/api/config/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify(payload),
        });
        $("config-notice").textContent = `Settings saved. Backup: ${result.backup || "none"}`;
        $("cfg-web-token").value = "";
        await loadConfig();
      } catch (error) {
        $("config-notice").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    }
    async function restoreBackup(name) {
      if (!confirm(`Restore ${name}?`)) return;
      await api(`/api/config/backup/${encodeURIComponent(name)}/restore`, { method: "POST", headers: authHeaders() });
      await loadConfig();
    }
    document.querySelectorAll("nav button").forEach((btn) => btn.addEventListener("click", () => showPage(btn.dataset.page)));
    $("refresh").addEventListener("click", loadAll);
    $("save-token").addEventListener("click", () => { localStorage.setItem("autofilm_token", $("token-input").value); loadConfig(); });
    $("module-filter").addEventListener("change", renderTasks);
    $("view-mode").addEventListener("change", (event) => { localStorage.setItem("autofilm_view", event.target.value); document.body.dataset.view = event.target.value; });
    $("theme-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_theme", event.target.value); applyPrefs(); });
    $("density-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_density", event.target.value); applyPrefs(); });
    $("refresh-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_refresh", event.target.value); applyPrefs(); });
    $("validate-config").addEventListener("click", validateConfig);
    $("save-config").addEventListener("click", saveConfig);
    $("save-settings").addEventListener("click", saveSettingsForm);
    $("token-input").value = token();
    applyPrefs();
    loadAll();
  </script>
</body>
</html>
"""
