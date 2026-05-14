"""Web 配置读写能力。"""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from ruamel.yaml import YAML
from yaml import YAMLError, safe_load

from app.core import settings

_ryml = YAML()
_ryml.preserve_quotes = True
_ryml.width = 4096

SECRET_KEYS = {
    "password",
    "token",
    "bot_token",
    "chat_id",
}


class ConfigPayload(BaseModel):
    content: str = Field(max_length=512_000)


class SettingsPayload(BaseModel):
    hot_reload: bool | None = None
    hot_reload_interval: int | None = None
    web_enabled: bool | None = None
    web_host: str | None = None
    web_port: int | None = None


def read_config_text(reveal: bool = False) -> str:
    if not settings.CONFIG.exists():
        return ""
    content = settings.CONFIG.read_text(encoding="utf-8")
    if reveal:
        return content
    data = load_yaml(content)
    return dump_yaml(redact(data))


def load_yaml(content: str) -> dict[str, Any]:
    try:
        data = safe_load(content) or {}
    except YAMLError as e:
        raise ValueError(f"YAML 解析失败：{e}") from e
    if not isinstance(data, dict):
        raise ValueError("配置顶层必须是 YAML 映射")
    return data


def dump_yaml(data: dict[str, Any]) -> str:
    buf = StringIO()
    _ryml.dump(data, buf)
    return buf.getvalue()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS and item:
                result[key] = "***"
            else:
                result[key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def config_summary() -> dict[str, Any]:
    content = settings.CONFIG.read_text(encoding="utf-8") if settings.CONFIG.exists() else ""
    data = load_yaml(content) if content else {}
    config_settings = data.get("Settings", {})
    alist_tasks = data.get("Alist2StrmList", [])
    notifiers = data.get("NotifierList", [])
    return {
        "path": str(settings.CONFIG),
        "exists": settings.CONFIG.exists(),
        "settings": redact(config_settings if isinstance(config_settings, dict) else {}),
        "counts": {
            "alist2strm": len(alist_tasks) if isinstance(alist_tasks, list) else 0,
            "notifiers": len(notifiers) if isinstance(notifiers, list) else 0,
        },
        "alist2strm": summarize_tasks(alist_tasks),
        "notifiers": summarize_notifiers(notifiers),
    }


def summarize_tasks(tasks: Any) -> list[dict[str, Any]]:
    if not isinstance(tasks, list):
        return []
    result = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "id": item.get("id") or "<未命名>",
                "cron": item.get("cron"),
                "mode": item.get("mode"),
                "source_dir": item.get("source_dir"),
                "target_dir": item.get("target_dir"),
                "sync_server": item.get("sync_server"),
                "incremental": item.get("incremental"),
                "incremental_level": item.get("incremental_level"),
                "max_workers": item.get("max_workers"),
                "scan_concurrency": item.get("scan_concurrency"),
            }
        )
    return result


def summarize_notifiers(notifiers: Any) -> list[dict[str, Any]]:
    if not isinstance(notifiers, list):
        return []
    result = []
    for item in notifiers:
        if isinstance(item, dict):
            result.append(
                {
                    "type": item.get("type"),
                    "enabled": item.get("enabled", True),
                }
            )
    return result


def backup_dir() -> Path:
    path = settings.CONFIG_DIR / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup() -> Path | None:
    if not settings.CONFIG.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = backup_dir() / f"config-{timestamp}.yaml"
    backup_file.write_text(settings.CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    _rotate_backups()
    return backup_file


def _rotate_backups(keep: int = 50) -> None:
    backups = sorted(backup_dir().glob("config-*.yaml"))
    if len(backups) <= keep:
        return
    for path in backups[:-keep]:
        try:
            path.unlink()
        except OSError:
            pass


def list_backups() -> list[dict[str, Any]]:
    if not backup_dir().exists():
        return []
    backups = []
    for path in sorted(backup_dir().glob("config-*.yaml"), reverse=True):
        backups.append(
            {
                "name": path.name,
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )
    return backups


def save_config(content: str) -> dict[str, Any]:
    load_yaml(content)
    backup = create_backup()
    temp_file = settings.CONFIG.with_suffix(".tmp")
    settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_file.write_text(content, encoding="utf-8")
    temp_file.replace(settings.CONFIG)
    return {
        "ok": True,
        "backup": backup.name if backup else None,
        "summary": config_summary(),
    }


def update_settings(payload: SettingsPayload) -> dict[str, Any]:
    if settings.CONFIG.exists():
        with settings.CONFIG.open("r", encoding="utf-8") as f:
            data = _ryml.load(f) or {}
    else:
        data = {}
    if not isinstance(data, dict):
        data = {}
    config_settings = data.get("Settings")
    if not isinstance(config_settings, dict):
        config_settings = {}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            config_settings[key] = value
    data["Settings"] = config_settings
    return save_config(dump_yaml(data))


def restore_backup(name: str) -> dict[str, Any]:
    source = backup_dir() / name
    try:
        resolved_source = source.resolve()
        resolved_backup_dir = backup_dir().resolve()
    except OSError as e:
        raise ValueError(f"备份路径无效：{e}") from e
    if resolved_source.parent != resolved_backup_dir or not resolved_source.exists():
        raise ValueError("备份不存在")
    content = resolved_source.read_text(encoding="utf-8")
    return save_config(content)


def delete_backup(name: str) -> None:
    source = backup_dir() / name
    try:
        resolved_source = source.resolve()
        resolved_backup_dir = backup_dir().resolve()
    except OSError as e:
        raise ValueError(f"备份路径无效：{e}") from e
    if resolved_source.parent != resolved_backup_dir or not resolved_source.exists():
        raise ValueError("备份不存在")
    resolved_source.unlink()
