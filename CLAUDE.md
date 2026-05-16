# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 构建与开发命令

```bash
# 安装依赖（Python 3.12）
pip install -r requirements.txt

# 运行应用
python app/main.py

# 手动执行指定 ID 的任务（执行完退出）
python app/main.py --run <task-id>

# 手动执行所有任务（执行完退出）
python app/main.py --run-all

# 代码检查
ruff check app/ --per-file-ignores="__init__.py:F401"

# 类型检查
mypy app/ --ignore-missing-imports --explicit-package-bases

# 运行全部测试
python -m unittest discover -s tests -v

# 运行单个测试文件
python -m unittest tests.test_config -v

# 安全扫描
bandit -r app/ -ll

# 依赖审计
pip-audit -r requirements.txt
```

## 项目架构

AutoFilm 通过扫描 Alist 目录为 Emby/Jellyfin 生成 `.strm` 直链文件，同时可按配置下载字幕、图片、NFO 及自定义后缀文件。版本号定义于 `app/version.py`。

### 入口 (`app/main.py`)

基于 `apscheduler` (`AsyncIOScheduler`) 的异步主程序。三种运行模式：
- **Cron 模式**（默认）：从 `config.yaml` 注册 Alist2Strm 定时任务。
- **`--run` / `--run-all`**：执行一次后退出。
- **Web 服务**（可选）：当 `AUTOFILM_WEB_ENABLED=true` 或 `web_enabled: True` 时启动 uvicorn。

生命周期：SIGTERM/SIGINT → 优雅关闭调度器、取消后台任务。`_hot_reload_watcher()` 协程监控 `config.yaml` 的 mtime，变更时增量重建 scheduler job，无需重启。
`main.py` 开头 `path.append(dirname(dirname(__file__)))` 将仓库根目录加入 `sys.path`，所有导入使用 `from app.xxx` 绝对路径。

### 核心 (`app/core/`)

- **`config.py`**：`SettingManager` 单例。加载 `config/config.yaml`，基于文件 mtime 缓存解析结果。属性包括 `AlistServerList`（支持环境变量覆盖如 `AUTOFILM_ALIST_{ID}_TOKEN`）、`NotifierList`、`WebEnabled`/`WebHost`/`WebPort`（环境变量 `AUTOFILM_WEB_ENABLED` 等）、`HotReloadEnabled`/`HotReloadInterval`。
- **`tasks.py`**：`TaskRegistry` 以 `{模块名}:{任务ID}` 为键管理 `TaskDefinition`。`run()` 获取异步锁防并发，发送开始/完成/失败通知，委托执行 `task_cls(**config).run()`。`replace_module()` 用于热重载时重建任务定义。
- **`state.py`**：`TaskStateStore` 将运行历史持久化到 `config/state/tasks.json`，通过临时文件 + rename 实现原子写入。
- **`log.py`**：自定义 `Formatter`（基于 click 的彩色控制台输出）+ `TRFileHandler`（每日轮换，保留 30 天）。

### 模块 (`app/modules/`)

- **`alist2strm/alist2strm.py`**：`Alist2Strm` 类是唯一的业务模块。`run()` 三阶段流水线：
  1. `_stage1_scan_and_process()`：`AlistClient.iter_path()` 异步遍历目录树，`_file_filter` 根据后缀、BDMV 收集、增量清单、覆盖策略过滤文件，通过 `__file_processer` 写 `.strm` 或下载资源。
  2. `_stage2_process_bdmv()`：每个 BDMV 蓝光目录选最大 `.m2ts` 文件，以电影标题命名生成 `.strm`。
  3. `_stage3_cleanup_and_save()`：`sync_server` 时清理远端已删除的本地孤立文件（目录级增量跳过子树时跳过清理），更新扫描清单。

  三种 `.strm` 模式（`Alist2StrmMode`）：`AlistURL`（Alist 内部下载链接）、`RawURL`（直链）、`AlistPath`（原始路径字符串）。`public_url` 可替换 AlistURL 中的服务器地址。

- **`alist2strm/manifest.py`**：`ScanManifest` 持久化文件扫描元数据，增量扫描时比对 `mtime + size` 跳过未变更文件/目录。Key 格式：文件路径 / `bdmv:` 前缀 / `dir:` 前缀。
- **`alist2strm/strm_protection.py`**：`StrmProtectionManager` 计数组件，待删除文件数超过阈值后需累积多个扫描周期才实际删除，防止 Alist 故障导致大量 `.strm` 被误删。
- **`alist/v3/client.py`**：`AlistClient` 使用 `Multiton` 元类（按 `(url, username)` 去重实例）。Token 管理带异步锁自动刷新。`iter_path()` 为异步生成器，支持配置并发数的目录 API 调用。
- **`alist/v3/path.py`**：`AlistPath` pydantic 模型，表示远端文件/目录。

### Web (`app/web/`)

- **`server.py`**：`create_app()` 构建 FastAPI 实例，内置 `_RateLimiter` 滑动窗口限流中间件（GET 120次/分，写 30次/分，任务触发 10次/分）。端点：`/health`、`/api/tasks`、`/api/tasks/{module}/{id}/run`、`/api/tasks/{module}/{id}/runs`、`/api/tasks/{module}/{id}/runs/latest`、`/api/config/*`、`/api/logs`、`/`（SPA 控制台）。
- **`ui.py`**：`render_index()` 返回完整的内联 HTML/CSS/JS SPA（无构建步骤）。支持任务仪表盘、搜索/筛选/排序、运行历史、YAML 编辑器（正则语法高亮）、Toast 通知、键盘快捷键。
- **`config_api.py`**：`read_config_text()` 返回原始或脱敏 YAML。`save_config()` 校验后创建时间戳备份（最多 50 个），通过临时文件原子替换。`update_settings()` 合并 Settings 字段，使用 `ruamel.yaml` 保留注释。`SECRET_KEYS` 在 API 响应中遮盖密码/令牌。

### 工具 (`app/utils/`)

- **`http.py`**：`HTTPClient` 封装 `httpx`（HTTP/2，指数退避重试 3 次）。`download()` 对 >128MB 文件使用并行分片下载（Range 请求）。`RequestUtils` 提供全局单例访问。
- **`notify.py`**：`send_notification()` 向所有已启用通知器推送。内置 `telegram`（Bot API）、`bark`（iOS 推送）、`webhook`（自定义 JSON POST，支持 `{title}/{body}/{level}` 模板替换）。可通过 `register_notifier()` 注册自定义通知器。
- **`retry.py`**：`Retry` 类提供 `sync_retry` / `async_retry` 装饰器，指数退避 `delay * backoff^attempt`。

### 配置文件 (`config/config.yaml`)

顶层键：`Settings`（DEV、web_enabled、web_host、web_port、hot_reload、hot_reload_interval）、`Alist2StrmList`（列表，每项含 id、cron、url、source_dir、target_dir、mode 等）、`NotifierList`（{type, enabled, config} 列表）。旧键 `Ani2AlistList` 已被忽略（v2.2.0 移除 Ani2Alist 模块）。敏感字段（token、password）可通过环境变量覆盖 `AUTOFILM_ALIST_{处理后的ID}_{字段名}`。

### 测试

`tests/` 使用 `unittest` 框架。测试通过 `TempSettingManager` 子类覆盖 `BASE_DIR` 属性实现隔离，使用 `TemporaryDirectory` 和 `unittest.mock.patch`。运行全部：`python -m unittest discover -s tests -v`。运行单个：`python -m unittest tests.test_config -v`。

### Docker

`Dockerfile` 基于 `python:3.12.7-slim-bookworm`，以非 root 用户 `appuser` 运行，通过 `entrypoint.sh` 启动。Docker Compose 挂载 `./config`、`./media`、`./logs`，暴露 8000 端口，健康检查访问 `/health`。

### CI (`.github/workflows/ci.yaml`)

PR 到 `main` 触发 5 个 job：`lint`（ruff）、`test`（unittest）、`audit`（pip-audit）、`type-check`（mypy）、`security-lint`（bandit）。全部使用 Python 3.12。
