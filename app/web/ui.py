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
    nav button svg { flex-shrink: 0; opacity: 0.65; }
    nav button.active { background: var(--surface-2); border-color: var(--line); }
    nav button.active svg { opacity: 1; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .content { padding: 22px; display: grid; gap: 18px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: var(--pad);
    }
    .metric { display: grid; gap: 6px; min-height: 94px; position: relative; overflow: hidden; }
    .metric-bar { position: absolute; top: 0; left: 0; width: 100%; height: 3px; }
    .metric-bar.c-primary { background: var(--primary); }
    .metric-bar.c-ok { background: var(--ok); }
    .metric-bar.c-warn { background: var(--warn); }
    .metric-bar.c-bad { background: var(--bad); }
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
    .dot.spin { animation: spin 1s linear infinite; border: 2px solid var(--muted); border-top-color: var(--warn); background: transparent; }
    @keyframes spin { to { transform: rotate(360deg); } }
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
    th { color: var(--muted); font-weight: 600; background: var(--surface-2); white-space: nowrap; cursor: pointer; user-select: none; }
    th:hover { color: var(--text); }
    th .sort-arrow { font-size: 11px; margin-left: 4px; }
    tbody tr:hover { background: var(--surface-2); }
    tbody tr:nth-child(even) { background: rgba(0,0,0,.015); }
    [data-theme="dark"] tbody tr:nth-child(even) { background: rgba(255,255,255,.015); }
    [data-theme="dark"] tbody tr:hover { background: var(--surface-2); }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .task-cards { display: none; gap: 12px; }
    [data-view="cards"] .table-wrap { display: none; }
    [data-view="cards"] .task-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .task-card { display: grid; gap: 10px; }
    .row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .split { display: grid; grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr); gap: 14px; align-items: start; }
    .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 13px; }
    input, select { min-height: 42px; padding: 8px 10px; }
    input[type="search"] { min-height: 42px; padding: 8px 10px; max-width: 180px; }
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
    .highlight-wrap { position: relative; }
    .highlight-wrap textarea, .highlight-wrap .hl-backdrop {
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      line-height: 1.45;
      tab-size: 2;
      white-space: pre-wrap;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }
    .highlight-wrap .hl-backdrop {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      padding: 13px;
      pointer-events: none;
      color: transparent;
    }
    .hl-key { color: #0550ae; }
    .hl-str { color: #0a8a3d; }
    .hl-comment { color: #6e7781; font-style: italic; }
    .hl-bool { color: #cf6600; }
    [data-theme="dark"] .hl-key { color: #79c0ff; }
    [data-theme="dark"] .hl-str { color: #7ee787; }
    [data-theme="dark"] .hl-comment { color: #8b949e; }
    [data-theme="dark"] .hl-bool { color: #ffa657; }
    .toast-container {
      position: fixed; bottom: 18px; right: 18px; z-index: 999;
      display: grid; gap: 8px; max-width: 380px;
    }
    .toast {
      padding: 12px 16px; border-radius: var(--radius);
      background: var(--surface); border: 1px solid var(--line);
      box-shadow: 0 4px 16px rgba(0,0,0,.12);
      display: grid; gap: 4px; animation: toastIn .25s ease-out;
    }
    @keyframes toastIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .toast-info { border-left: 4px solid var(--primary); }
    .toast-success { border-left: 4px solid var(--ok); }
    .toast-error { border-left: 4px solid var(--bad); }
    .toast-warn { border-left: 4px solid var(--warn); }
    .toast strong { font-size: 14px; }
    .toast div { font-size: 13px; color: var(--muted); }
    .diff-overlay {
      display: none; position: fixed; inset: 0; z-index: 99;
      background: rgba(0,0,0,.35); align-items: center; justify-content: center;
    }
    .diff-overlay.show { display: flex; }
    .diff-box {
      background: var(--surface); border-radius: var(--radius);
      padding: 22px; max-width: 520px; width: 90vw; max-height: 80vh; overflow-y: auto;
    }
    .diff-added { color: var(--ok); }
    .diff-removed { color: var(--bad); }
    .log-viewer {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      max-height: 520px; overflow-y: auto;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 12px; line-height: 1.5; padding: 12px;
      white-space: pre-wrap; word-break: break-all;
    }
    .log-line-error { color: var(--bad); }
    .log-line-warn { color: var(--warn); }
    .log-line-info { color: var(--text); }
    .log-line-debug { color: var(--muted); font-style: italic; }
    .empty-state {
      text-align: center; padding: 40px 20px; color: var(--muted);
      border: 2px dashed var(--line); border-radius: var(--radius); font-size: 14px;
    }
    .recent-item {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 0; border-bottom: 1px solid var(--line); cursor: pointer;
    }
    .recent-item:last-child { border-bottom: 0; }
    .recent-item:hover { background: var(--surface-2); margin: 0 calc(-1 * var(--pad)); padding-left: var(--pad); padding-right: var(--pad); border-radius: 4px; }
    .recent-module { font-size: 12px; color: var(--muted); }
    .recent-time { font-size: 12px; color: var(--muted); margin-left: auto; }
    .shortcut-hint {
      font-size: 10px; padding: 1px 5px; border-radius: 3px;
      background: var(--surface-2); color: var(--muted);
      border: 1px solid var(--line); margin-left: 4px;
    }
    .hidden { display: none !important; }
    .notice { border-left: 4px solid var(--primary); padding: 10px 12px; background: var(--surface-2); }
    .notice.warn { border-left-color: var(--warn); }
    .error-text { color: var(--bad); }
    .success-text { color: var(--ok); }
    @media (max-width: 920px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      header { position: static; align-items: flex-start; flex-direction: column; }
      .grid, .split, .form-grid { grid-template-columns: 1fr; }
      .table-wrap { display: none; }
      .task-cards, [data-view="cards"] .task-cards { display: grid; grid-template-columns: 1fr; }
      input[type="search"] { max-width: 100%; width: 100%; }
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
  <div class="diff-overlay" id="diff-overlay">
    <div class="diff-box" id="diff-box-content"></div>
  </div>
  <div class="toast-container" id="toasts"></div>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>AutoFilm</h1>
        <span class="version">__VERSION__</span>
      </div>
      <nav aria-label="主导航">
        <button class="active" data-page="dashboard" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>概览</button>
        <button data-page="tasks" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 14l2 2 4-4"/></svg>任务</button>
        <button data-page="config" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>配置</button>
        <button data-page="logs" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>日志</button>
        <button data-page="settings" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>偏好</button>
      </nav>
    </aside>
    <main>
      <header>
        <div>
          <h1 id="page-title">概览</h1>
          <div class="muted" id="health-line">正在检查服务...</div>
        </div>
        <div class="toolbar">
          <button id="refresh" class="primary" type="button">刷新 <kbd class="shortcut-hint">Ctrl+R</kbd></button>
        </div>
      </header>
      <section class="content" id="page-dashboard">
        <div class="grid" id="metrics"></div>
        <div class="panel">
          <h2>最近活动</h2>
          <div id="recent-activity"></div>
        </div>
      </section>
      <section class="content hidden" id="page-tasks">
        <div class="panel">
          <div class="toolbar">
            <h2 style="margin-right:auto">任务</h2>
            <input id="task-search" type="search" placeholder="搜索任务..." aria-label="搜索任务">
            <select id="module-filter" aria-label="模块筛选">
              <option value="">全部模块</option>
            </select>
            <select id="view-mode" aria-label="视图模式">
              <option value="table">表格</option>
              <option value="cards">卡片</option>
            </select>
            <button id="run-all" type="button" title="触发全部未运行任务">运行全部</button>
            <button id="run-failed" class="ghost hidden" type="button" style="color:var(--bad)">重试失败</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th data-sort="key">任务 <span class="sort-arrow"></span></th><th data-sort="cron">Cron <span class="sort-arrow"></span></th><th data-sort="next_run_time">下次运行 <span class="sort-arrow"></span></th><th data-sort="last_result">状态 <span class="sort-arrow"></span></th><th>最近结果</th><th>操作</th></tr>
              </thead>
              <tbody id="task-rows"></tbody>
            </table>
          </div>
          <div class="task-cards" id="task-cards"></div>
        </div>
        <div class="panel" id="history-panel">
          <div class="toolbar" style="margin-bottom:10px">
            <h2 style="margin-right:auto" id="history-title">运行历史</h2>
            <button id="back-to-tasks" class="ghost hidden" type="button">← 返回任务列表</button>
            <button id="clear-history" class="ghost" type="button">清空</button>
          </div>
          <div id="run-history" class="empty-state">请选择一个任务。</div>
        </div>
      </section>
      <section class="content hidden" id="page-config">
        <div class="split">
          <div class="panel">
            <h2>配置摘要</h2>
            <div id="config-summary"></div>
            <h2 style="margin-top:18px">常用设置</h2>
            <div class="form-grid">
              <label>启用 Web
                <select id="cfg-web-enabled">
                  <option value="true">是</option>
                  <option value="false">否</option>
                </select>
              </label>
              <label>Web 监听地址
                <input id="cfg-web-host" type="text" placeholder="0.0.0.0">
              </label>
              <label>Web 端口
                <input id="cfg-web-port" type="number" min="1" max="65535" placeholder="8000">
              </label>
              <label>热重载
                <select id="cfg-hot-reload">
                  <option value="true">是</option>
                  <option value="false">否</option>
                </select>
              </label>
              <label>重载间隔
                <input id="cfg-hot-reload-interval" type="number" min="5" placeholder="30">
              </label>
            </div>
            <div class="toolbar" style="margin-top:12px">
              <button id="save-settings" class="primary" type="button">保存常用设置</button>
              <button id="reset-settings-form" class="ghost" type="button">重置为服务器值</button>
            </div>
            <h2 style="margin-top:18px">配置备份</h2>
            <div id="backups"></div>
          </div>
          <div class="panel">
            <div class="toolbar">
              <h2 style="margin-right:auto">YAML 编辑器</h2>
              <button id="discard-changes" class="ghost hidden" type="button" style="color:var(--warn)">放弃更改</button>
              <button id="validate-config" type="button">校验</button>
              <button id="save-config" class="primary" type="button">保存 <kbd class="shortcut-hint">Ctrl+S</kbd></button>
            </div>
            <div id="config-notice" class="notice">保存时会自动备份并原子替换 config.yaml。</div>
            <div class="highlight-wrap">
              <textarea id="config-editor" spellcheck="false" aria-label="config.yaml 编辑器"></textarea>
              <pre class="hl-backdrop" id="hl-backdrop" aria-hidden="true"></pre>
            </div>
          </div>
        </div>
      </section>
      <section class="content hidden" id="page-logs">
        <div class="panel">
          <div class="toolbar">
            <h2 style="margin-right:auto">运行日志</h2>
            <input id="log-search" type="search" placeholder="在日志中搜索..." aria-label="搜索日志">
            <select id="log-level" aria-label="日志级别">
              <option value="">全部级别</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
            <select id="log-lines" aria-label="行数">
              <option value="100">100 行</option>
              <option value="200" selected>200 行</option>
              <option value="500">500 行</option>
              <option value="1000">1000 行</option>
            </select>
            <button id="refresh-logs" class="primary" type="button">刷新</button>
          </div>
          <div class="log-viewer" id="log-content">正在加载...</div>
        </div>
      </section>
      <section class="content hidden" id="page-settings">
        <div class="panel">
          <h2>显示设置</h2>
          <div class="form-grid">
            <label>主题
              <select id="theme-select">
                <option value="system">跟随系统</option>
                <option value="light">浅色</option>
                <option value="dark">深色</option>
              </select>
            </label>
            <label>密度
              <select id="density-select">
                <option value="comfortable">舒适</option>
                <option value="compact">紧凑</option>
              </select>
            </label>
            <label>自动刷新
              <select id="refresh-select">
                <option value="0">关闭</option>
                <option value="15">15s</option>
                <option value="30">30s</option>
                <option value="60">60s</option>
              </select>
            </label>
          </div>
          <div class="muted" style="margin-top:18px; font-size:13px">
            快捷键：<kbd>Ctrl+R</kbd> 刷新 · <kbd>Ctrl+S</kbd> 保存配置 · <kbd>1-5</kbd> 切换页面
          </div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const state = { tasks: [], summary: null, backups: [], editorDirty: false, currentPage: "dashboard", sortField: null, sortDir: "asc", historyKey: null };
    const $ = (id) => document.getElementById(id);
    function setText(id, text) { if ($(id)) $(id).textContent = text; }
    function fmt(value) { return value || ""; }
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));
    }
    function toast(msg, type = "info", duration = 3500) {
      const el = document.createElement("div");
      el.className = `toast toast-${type}`;
      const labels = { error: "错误", success: "成功", warn: "警告", info: "信息" };
      el.innerHTML = `<strong>${labels[type] || type}</strong><div>${escapeHtml(msg)}</div>`;
      $("toasts").appendChild(el);
      setTimeout(() => el.remove(), duration);
    }
    function relTime(iso) {
      if (!iso) return "";
      const diff = (Date.now() - new Date(iso).getTime()) / 1000;
      if (diff < 60) return "刚刚";
      if (diff < 3600) return Math.floor(diff / 60) + " 分钟前";
      if (diff < 86400) return Math.floor(diff / 3600) + " 小时前";
      return Math.floor(diff / 86400) + " 天前";
    }
    function duration(a, b) {
      if (!a || !b) return "";
      const s = (new Date(b).getTime() - new Date(a).getTime()) / 1000;
      if (s < 1) return "<1s";
      if (s < 60) return Math.floor(s) + "s";
      const m = Math.floor(s / 60);
      if (m < 60) return m + "m " + Math.floor(s % 60) + "s";
      return Math.floor(m / 60) + "h " + (m % 60) + "m";
    }
    function showPage(name) {
      const pageNames = { dashboard: "概览", tasks: "任务", config: "配置", logs: "日志", settings: "偏好" };
      state.currentPage = name;
      document.querySelectorAll("nav button").forEach((btn) => btn.classList.toggle("active", btn.dataset.page === name));
      document.querySelectorAll("main > section").forEach((section) => section.classList.add("hidden"));
      const el = $(`page-${name}`);
      if (el) el.classList.remove("hidden");
      setText("page-title", pageNames[name] || name);
      if (name === "config") loadConfig();
      if (name === "logs") loadLogs();
      if (name === "tasks") { buildModuleFilter(); renderTasks(); }
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
        setText("health-line", `服务正常 · ${health.version}`);
      } catch (error) {
        setText("health-line", "服务不可用");
      }
      await loadTasks();
      await loadSummary();
      if (state.currentPage === "config" && state.editorDirty) return;
    }
    async function loadTasks() {
      state.tasks = await api("/api/tasks");
      buildModuleFilter();
      renderMetrics();
      renderTasks();
      renderRecent();
    }
    async function loadSummary() {
      state.summary = await api("/api/config/summary");
      renderConfigSummary();
    }
    function buildModuleFilter() {
      const modules = [...new Set(state.tasks.map((t) => t.module).filter(Boolean))];
      const select = $("module-filter");
      const cur = select.value;
      select.innerHTML = '<option value="">全部模块</option>' + modules.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
      if (cur && modules.includes(cur)) select.value = cur;
    }
    function filteredTasks() {
      const moduleName = $("module-filter").value;
      const search = ($("task-search").value || "").toLowerCase();
      let list = state.tasks;
      if (moduleName) list = list.filter((t) => t.module === moduleName);
      if (search) list = list.filter((t) => (t.key || "").toLowerCase().includes(search) || (t.id || "").toLowerCase().includes(search));
      return list;
    }
    function sortedTasks() {
      const list = filteredTasks();
      if (!state.sortField) return list;
      return [...list].sort((a, b) => {
        let va = a[state.sortField], vb = b[state.sortField];
        if (va == null) va = "";
        if (vb == null) vb = "";
        if (state.sortField === "running") { va = a.running ? 1 : 0; vb = b.running ? 1 : 0; }
        if (state.sortField === "last_result") { const order = { "error": 0, "": 1, "success": 2 }; va = order[a.last_result] ?? 1; vb = order[b.last_result] ?? 1; }
        const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
        return state.sortDir === "asc" ? cmp : -cmp;
      });
    }
    function setSort(field) {
      if (state.sortField === field) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortField = field;
        state.sortDir = "asc";
      }
      renderTasks();
    }
    function renderSortArrows() {
      document.querySelectorAll("th[data-sort]").forEach((th) => {
        const field = th.dataset.sort;
        const arrow = th.querySelector(".sort-arrow");
        if (arrow) arrow.textContent = state.sortField === field ? (state.sortDir === "asc" ? "↑" : "↓") : "";
      });
    }
    function renderMetrics() {
      const total = state.tasks.length;
      const running = state.tasks.filter((t) => t.running).length;
      const failed = state.tasks.filter((t) => t.last_result === "error").length;
      const ok = state.tasks.filter((t) => t.last_result === "success").length;
      $("metrics").innerHTML = [
        ["任务总数", total, "已配置任务", "c-primary"],
        ["运行中", running, "当前活动", "c-warn"],
        ["成功", ok, "最近结果", "c-ok"],
        ["错误", failed, failed > 0 ? "需关注" : "最近结果", failed > 0 ? "c-bad" : ""],
      ].map(([label, value, hint, bar]) => `<div class="panel metric"><div class="metric-bar ${bar}"></div><span class="muted">${label}</span><strong>${value}</strong><span class="muted">${hint}</span></div>`).join("");
    }
    function statusPill(task) {
      const cls = task.running ? "warn" : task.last_result === "error" ? "bad" : task.last_result === "success" ? "ok" : "";
      const resultLabels = { success: "成功", error: "失败" };
      const label = task.running ? "运行中" : resultLabels[task.last_result] || "空闲";
      const icon = task.running ? "↻" : task.last_result === "success" ? "✓" : task.last_result === "error" ? "✗" : "—";
      const dotClass = task.running ? "dot spin" : "dot";
      return `<span class="status ${cls}"><span class="${dotClass}"></span>${icon} ${escapeHtml(label)}</span>`;
    }
    function renderTasks() {
      const rows = sortedTasks();
      const hasFailed = rows.some((t) => t.last_result === "error");
      $("run-failed").classList.toggle("hidden", !hasFailed);
      $("task-rows").innerHTML = rows.map((task) => `
        <tr>
          <td><strong>${escapeHtml(task.module)}:${escapeHtml(task.id)}</strong><div class="muted">${escapeHtml(task.key)}</div></td>
          <td>${escapeHtml(fmt(task.cron))}</td>
          <td>${escapeHtml(fmt(task.next_run_time))}</td>
          <td>${statusPill(task)}</td>
          <td>${escapeHtml(task.last_error || task.last_result || "")}</td>
          <td class="row-actions">${taskButtons(task)}</td>
        </tr>`).join("") || '<tr><td colspan="6"><div class="empty-state">暂无匹配任务</div></td></tr>';
      $("task-cards").innerHTML = rows.map((task) => `
        <div class="panel task-card">
          <h3>${escapeHtml(task.module)}:${escapeHtml(task.id)}</h3>
          ${statusPill(task)}
          <div class="muted">Cron：${escapeHtml(fmt(task.cron))}</div>
          <div class="muted">下次运行：${escapeHtml(fmt(task.next_run_time))}</div>
          <div class="row-actions">${taskButtons(task)}</div>
        </div>`).join("") || '<div class="empty-state">暂无匹配任务</div>';
      renderSortArrows();
    }
    function taskButtons(task) {
      return `<button class="primary run-btn" type="button" data-module="${escapeHtml(task.module)}" data-task-id="${escapeHtml(task.id)}" ${task.running ? "disabled" : ""}>运行</button>
        <button class="history-btn" type="button" data-module="${escapeHtml(task.module)}" data-task-id="${escapeHtml(task.id)}">历史</button>
        <button class="detail-btn ghost" type="button" data-module="${escapeHtml(task.module)}" data-task-id="${escapeHtml(task.id)}">详情</button>`;
    }
    document.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      if (btn.classList.contains("run-btn")) runTask(btn.dataset.module, btn.dataset.taskId, btn);
      else if (btn.classList.contains("history-btn")) loadHistory(btn.dataset.module, btn.dataset.taskId);
      else if (btn.classList.contains("restore-btn")) restoreBackup(btn.dataset.name);
      else if (btn.classList.contains("delete-btn")) deleteBackup(btn.dataset.name);
      else if (btn.classList.contains("detail-btn")) showTaskDetail(btn.dataset.module, btn.dataset.taskId);
    });
    document.querySelectorAll("th[data-sort]").forEach((th) => th.addEventListener("click", () => setSort(th.dataset.sort)));
    async function runTask(moduleName, taskId, btn) {
      if (btn) { btn.disabled = true; btn.textContent = "运行中…"; }
      try {
        await api(`/api/tasks/${encodeURIComponent(moduleName)}/${encodeURIComponent(taskId)}/run`, { method: "POST", headers: {} });
        toast(`${moduleName}:${taskId} 执行成功`, "success");
        await loadTasks();
      } catch (error) {
        toast(error.message, "error");
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "运行"; }
      }
    }
    async function loadHistory(moduleName, taskId) {
      state.historyKey = `${moduleName}:${taskId}`;
      setText("history-title", `运行历史：${moduleName}:${taskId}`);
      $("back-to-tasks").classList.remove("hidden");
      $("run-history").innerHTML = "正在加载…";
      const data = await api(`/api/tasks/${encodeURIComponent(moduleName)}/${encodeURIComponent(taskId)}/runs`);
      $("run-history").innerHTML = data.history.length ? data.history.map((run) => `
        <div class="panel" style="margin-top:10px">
          <strong>${run.success ? '<span class="success-text">成功</span>' : '<span class="error-text">失败</span>'}</strong>
          <span class="muted" style="margin-left:8px">耗时 ${duration(run.started_at, run.finished_at)}</span>
          <div class="muted">${escapeHtml(run.started_at || "")} → ${escapeHtml(run.finished_at || "")}</div>
          <div class="error-text">${escapeHtml(run.error || "")}</div>
        </div>`).join("") : '<div class="empty-state">暂无历史记录</div>';
      showPage("tasks");
    }
    function renderRecent() {
      const items = state.tasks.filter((t) => t.updated_at).sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || "")).slice(0, 8);
      $("recent-activity").innerHTML = items.length ? items.map((t) => `
        <div class="recent-item" data-module="${escapeHtml(t.module)}" data-task-id="${escapeHtml(t.id)}">
          ${statusPill(t)}
          <div><strong>${escapeHtml(t.key)}</strong><div class="recent-module">${escapeHtml(t.module)}</div></div>
          <span class="recent-time">${relTime(t.updated_at)}</span>
        </div>`).join("") : '<div class="empty-state">暂无活动</div>';
      document.querySelectorAll(".recent-item").forEach((el) => {
        el.addEventListener("click", () => { loadHistory(el.dataset.module, el.dataset.taskId); });
      });
    }
    // Config
    async function loadConfig() {
      let raw;
      try {
        raw = await api("/api/config/raw");
      } catch (error) {
        raw = { content: "", redacted: false };
      }
      if (!state.editorDirty) {
        $("config-editor").value = raw.content || "";
        highlightYAML();
      }
      $("config-notice").innerHTML = "保存时会自动备份并原子替换 config.yaml。";
      if (state.editorDirty) {
        $("config-notice").classList.add("warn");
        $("discard-changes").classList.remove("hidden");
        $("config-notice").innerHTML += " <strong>您有未保存的更改。</strong>";
      } else {
        $("config-notice").classList.remove("warn");
        $("discard-changes").classList.add("hidden");
      }
      await loadSummary();
      state.backups = await api("/api/config/backups");
      renderBackups();
    }
    function renderConfigSummary() {
      if (!state.summary) return;
      const counts = state.summary.counts || {};
      const settings = state.summary.settings || {};
      $("config-summary").innerHTML = `
        <div class="muted">路径：${escapeHtml(state.summary.path)}</div>
        <div style="margin-top:10px">Alist2Strm: <strong>${counts.alist2strm || 0}</strong></div>
        <div>通知器：<strong>${counts.notifiers || 0}</strong></div>
        <h3 style="margin-top:14px">Alist2Strm</h3>
        ${(state.summary.alist2strm || []).map((task) => `<div class="notice" style="margin-top:8px"><strong>${escapeHtml(task.id)}</strong><div class="muted">${escapeHtml(task.mode || "")} · ${escapeHtml(task.source_dir || "")} → ${escapeHtml(task.target_dir || "")}</div></div>`).join("") || '<div class="empty-state">暂无任务</div>'}`;
      if (!$("cfg-web-enabled").dataset.frozen) {
        $("cfg-web-enabled").value = String(Boolean(settings.web_enabled));
        $("cfg-web-host").value = settings.web_host || "0.0.0.0";
        $("cfg-web-port").value = settings.web_port || 8000;
        $("cfg-hot-reload").value = String(settings.hot_reload !== false);
        $("cfg-hot-reload-interval").value = settings.hot_reload_interval || 30;
      }
    }
    function renderBackups() {
      $("backups").innerHTML = state.backups.length ? state.backups.map((backup) => `
        <div class="notice" style="margin-top:8px">
          <div style="display:flex; justify-content:space-between; align-items:center">
            <div><strong>${escapeHtml(backup.name)}</strong><div class="muted">${escapeHtml(backup.modified)} · ${backup.size} 字节</div></div>
            <div style="display:flex; gap:6px">
              <button class="restore-btn ghost" type="button" data-name="${escapeHtml(backup.name)}">恢复</button>
              <button class="delete-btn ghost" type="button" data-name="${escapeHtml(backup.name)}" style="color:var(--bad)">删除</button>
            </div>
          </div>
        </div>`).join("") : '<div class="empty-state">暂无备份</div>';
    }
    function showTaskDetail(moduleName, taskId) {
      const task = state.tasks.find((t) => t.module === moduleName && t.id === taskId);
      if (!task) return;
      $("diff-box-content").innerHTML = `
        <h3>${escapeHtml(task.key)}</h3>
        <div class="muted" style="margin-bottom:12px">模块：${escapeHtml(task.module)} · Cron：${escapeHtml(fmt(task.cron))} · 下次运行：${escapeHtml(fmt(task.next_run_time))}</div>
        <pre style="font-size:12px; background:var(--surface-2); padding:12px; border-radius:6px; max-height:50vh; overflow-y:auto; white-space:pre-wrap; word-break:break-all">${escapeHtml(JSON.stringify(task, null, 2))}</pre>
        <div class="toolbar" style="margin-top:14px">
          <button id="detail-close" class="primary" type="button">关闭</button>
        </div>`;
      $("diff-overlay").classList.add("show");
      $("detail-close").onclick = () => $("diff-overlay").classList.remove("show");
    }
    async function saveConfig() {
      const content = $("config-editor").value;
      let raw;
      try { raw = await api("/api/config/raw"); }
      catch (e) { raw = { content: "" }; }
      const oldLines = (raw.content || "").split("\\n");
      const newLines = content.split("\\n");
      const added = newLines.filter((l) => !oldLines.includes(l)).length;
      const removed = oldLines.filter((l) => !newLines.includes(l)).length;
      $("diff-box-content").innerHTML = `
        <h3>确认保存配置？</h3>
        <p>与服务器当前配置对比：</p>
        <p><span class="diff-added">+${added} 行新增</span> · <span class="diff-removed">-${removed} 行删除</span></p>
        <p class="muted">保存后原配置将自动备份。</p>
        <div class="toolbar" style="margin-top:14px">
          <button id="diff-cancel" type="button">取消</button>
          <button id="diff-confirm" class="primary" type="button">确认保存</button>
        </div>`;
      $("diff-overlay").classList.add("show");
      $("diff-confirm").onclick = async () => {
        $("diff-overlay").classList.remove("show");
        await _doSave(content);
      };
      $("diff-cancel").onclick = () => $("diff-overlay").classList.remove("show");
    }
    async function _doSave(content) {
      const btn = $("save-config");
      btn.disabled = true; btn.textContent = "保存中…";
      try {
        const result = await api("/api/config/raw", {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...{} },
          body: JSON.stringify({ content }),
        });
        state.editorDirty = false;
        toast(`已保存。备份：${result.backup || "无"}`, "success");
        await loadConfig();
      } catch (error) {
        toast(error.message, "error");
      } finally {
        btn.disabled = false; btn.textContent = "保存";
      }
    }
    async function validateConfig() {
      const btn = $("validate-config");
      btn.disabled = true; btn.textContent = "校验中…";
      try {
        const result = await api("/api/config/validate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: $("config-editor").value }),
        });
        toast(`YAML 校验通过：${(result.sections || []).join(", ")}`, "success");
      } catch (error) {
        toast(error.message, "error");
      } finally {
        btn.disabled = false; btn.textContent = "校验";
      }
    }
    async function saveSettingsForm() {
      const btn = $("save-settings");
      btn.disabled = true; btn.textContent = "保存中…";
      try {
        const payload = {
          web_enabled: $("cfg-web-enabled").value === "true",
          web_host: $("cfg-web-host").value || "0.0.0.0",
          web_port: Number($("cfg-web-port").value || 8000),
          hot_reload: $("cfg-hot-reload").value === "true",
          hot_reload_interval: Number($("cfg-hot-reload-interval").value || 30),
        };
        const result = await api("/api/config/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...{} },
          body: JSON.stringify(payload),
        });
        toast(`常用设置已保存。备份：${result.backup || "无"}`, "success");
        state.editorDirty = false;
        await loadConfig();
      } catch (error) {
        toast(error.message, "error");
      } finally {
        btn.disabled = false; btn.textContent = "保存常用设置";
      }
    }
    async function restoreBackup(name) {
      if (!confirm(`确认恢复备份 ${name}？当前配置将被覆盖。`)) return;
      try {
        await api(`/api/config/backup/${encodeURIComponent(name)}/restore`, { method: "POST", headers: {} });
        state.editorDirty = false;
        toast(`已恢复备份：${name}`, "success");
        await loadConfig();
      } catch (error) {
        toast(`恢复失败：${error.message}`, "error");
      }
    }
    async function deleteBackup(name) {
      if (!confirm(`确认删除备份 ${name}？此操作不可撤销。`)) return;
      try {
        await api(`/api/config/backup/${encodeURIComponent(name)}`, { method: "DELETE", headers: {} });
        toast(`已删除备份：${name}`, "success");
        await loadConfig();
      } catch (error) {
        toast(`删除失败：${error.message}`, "error");
      }
    }
    // Batch operations
    async function runAll() {
      const toRun = state.tasks.filter((t) => !t.running);
      if (!toRun.length) { toast("没有可运行的任务", "info"); return; }
      let ok = 0, err = 0;
      for (const task of toRun) {
        try {
          await api(`/api/tasks/${encodeURIComponent(task.module)}/${encodeURIComponent(task.id)}/run`, { method: "POST", headers: {} });
          ok++;
        } catch (e) { err++; }
      }
      await loadTasks();
      toast(`已触发：${ok} 成功，${err} 失败`, ok > 0 ? "success" : "error");
    }
    async function runFailed() {
      const failed = state.tasks.filter((t) => t.last_result === "error" && !t.running);
      if (!failed.length) { toast("没有失败的任务", "info"); return; }
      let ok = 0, err = 0;
      for (const task of failed) {
        try {
          await api(`/api/tasks/${encodeURIComponent(task.module)}/${encodeURIComponent(task.id)}/run`, { method: "POST", headers: {} });
          ok++;
        } catch (e) { err++; }
      }
      await loadTasks();
      toast(`重试完毕：${ok} 成功，${err} 失败`, ok > 0 ? "success" : "error");
    }
    // YAML highlight
    function highlightYAML() {
      const text = $("config-editor").value;
      if (!text) { $("hl-backdrop").innerHTML = ""; return; }
      const escaped = escapeHtml(text);
      const highlighted = escaped.split("\\n").map((line) => {
        if (/^\\s*#/.test(line)) return `<span class="hl-comment">${line}</span>`;
        return line.replace(/(\\s*)([\\w-]+)(:)/g, (_, sp, key, col) => {
          const rest = line.slice(sp.length + key.length + col.length);
          if (/^\\s*$/.test(rest)) return `${escapeHtml(sp)}<span class="hl-key">${escapeHtml(key)}</span>${col}`;
          if (/^\\s*(true|false|yes|no|on|off)\\s*$/i.test(rest.trim()))
            return `${escapeHtml(sp)}<span class="hl-key">${escapeHtml(key)}</span>${col}<span class="hl-bool">${escapeHtml(rest)}</span>`;
          if (/^\\s*\\d[\\d.]*\\s*$/.test(rest.trim()))
            return `${escapeHtml(sp)}<span class="hl-key">${escapeHtml(key)}</span>${col}<span class="hl-bool">${escapeHtml(rest)}</span>`;
          if (/^\\s*["'].*["']\\s*$/.test(rest) || /^\\s*\\S/.test(rest))
            return `${escapeHtml(sp)}<span class="hl-key">${escapeHtml(key)}</span>${col}<span class="hl-str">${escapeHtml(rest)}</span>`;
          return `${escapeHtml(sp)}<span class="hl-key">${escapeHtml(key)}</span>${col}${escapeHtml(rest)}`;
        });
      }).join("\\n");
      $("hl-backdrop").innerHTML = highlighted;
    }
    // Log viewer
    async function loadLogs() {
      const lines = $("log-lines").value;
      const level = $("log-level").value;
      try {
        const data = await api(`/api/logs?lines=${lines}${level ? "&level=" + level : ""}`);
        const search = ($("log-search").value || "").toLowerCase();
        let entries = data.entries;
        if (search) entries = entries.filter((l) => l.toLowerCase().includes(search));
        $("log-content").innerHTML = entries.length
          ? entries.map((line) => {
              let cls = "log-line-info";
              if (line.includes("【ERROR】")) cls = "log-line-error";
              else if (line.includes("【WARNING】")) cls = "log-line-warn";
              else if (line.includes("【DEBUG】")) cls = "log-line-debug";
              return `<div class="${cls}">${escapeHtml(line)}</div>`;
            }).join("\\n")
          : '<div class="empty-state">无匹配日志</div>';
      } catch (error) {
        $("log-content").innerHTML = `<div class="error-text">加载失败：${escapeHtml(error.message)}</div>`;
      }
    }
    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key === "r") { e.preventDefault(); loadAll(); }
      if (mod && e.key === "s") { e.preventDefault(); if (state.currentPage === "config") saveConfig(); }
      if (!mod && !e.target.closest("input,textarea,select")) {
        const pages = ["dashboard", "tasks", "config", "logs", "settings"];
        const num = parseInt(e.key);
        if (num >= 1 && num <= pages.length) showPage(pages[num - 1]);
      }
    });
    // Event bindings
    document.querySelectorAll("nav button").forEach((btn) => btn.addEventListener("click", () => showPage(btn.dataset.page)));
    $("refresh").addEventListener("click", loadAll);
    $("module-filter").addEventListener("change", renderTasks);
    $("task-search").addEventListener("input", renderTasks);
    $("view-mode").addEventListener("change", (event) => {
      localStorage.setItem("autofilm_view", event.target.value);
      document.body.dataset.view = event.target.value;
    });
    $("theme-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_theme", event.target.value); applyPrefs(); });
    $("density-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_density", event.target.value); applyPrefs(); });
    $("refresh-select").addEventListener("change", (event) => { localStorage.setItem("autofilm_refresh", event.target.value); applyPrefs(); });
    $("validate-config").addEventListener("click", validateConfig);
    $("save-config").addEventListener("click", saveConfig);
    $("save-settings").addEventListener("click", saveSettingsForm);
    $("run-all").addEventListener("click", runAll);
    $("run-failed").addEventListener("click", runFailed);
    $("back-to-tasks").addEventListener("click", () => {
      state.historyKey = null;
      $("back-to-tasks").classList.add("hidden");
      setText("history-title", "运行历史");
      $("run-history").innerHTML = '<div class="empty-state">请选择一个任务。</div>';
      renderTasks();
    });
    $("clear-history").addEventListener("click", () => {
      $("run-history").innerHTML = '<div class="empty-state">请选择一个任务。</div>';
      $("back-to-tasks").classList.add("hidden");
      setText("history-title", "运行历史");
    });
    $("discard-changes").addEventListener("click", () => { state.editorDirty = false; loadConfig(); });
    $("reset-settings-form").addEventListener("click", () => {
      ["cfg-web-enabled","cfg-web-host","cfg-web-port","cfg-hot-reload","cfg-hot-reload-interval"].forEach((id) => { delete $(id).dataset.frozen; });
      loadConfig();
    });
    $("config-editor").addEventListener("input", () => { state.editorDirty = true; highlightYAML(); });
    $("config-editor").addEventListener("scroll", () => { $("hl-backdrop").scrollTop = $("config-editor").scrollTop; $("hl-backdrop").scrollLeft = $("config-editor").scrollLeft; });
    $("refresh-logs").addEventListener("click", loadLogs);
    $("log-level").addEventListener("change", () => { if (state.currentPage === "logs") loadLogs(); });
    $("log-lines").addEventListener("change", () => { if (state.currentPage === "logs") loadLogs(); });
    $("log-search").addEventListener("input", () => { if (state.currentPage === "logs") loadLogs(); });
    $("diff-overlay").addEventListener("click", (e) => { if (e.target === $("diff-overlay")) $("diff-overlay").classList.remove("show"); });
    ["cfg-web-enabled", "cfg-web-host", "cfg-web-port", "cfg-hot-reload", "cfg-hot-reload-interval"].forEach((id) => {
      $(id).addEventListener("input", () => { $(id).dataset.frozen = "1"; });
    });
    applyPrefs();
    loadAll();
  </script>
</body>
</html>
"""
