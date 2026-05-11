#!/bin/sh
# 以 root 身份修正挂载目录权限，再以 appuser 身份启动应用
set -e

chown appuser:appuser /config /logs /media 2>/dev/null || true

# 从配置文件中提取 target_dir 并授权（排除系统关键目录）
CONFIG="/config/config.yaml"
if [ -f "$CONFIG" ]; then
    python - <<'PY' | while read -r dir; do
from pathlib import Path
import yaml

config = Path("/config/config.yaml")
try:
    data = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
except Exception:
    data = {}

for item in data.get("Alist2StrmList", []) or []:
    if isinstance(item, dict) and item.get("target_dir"):
        print(item["target_dir"])
PY
        if [ -d "$dir" ]; then
            case "$dir" in
                /|/bin|/sbin|/usr|/lib*|/etc|/boot|/dev|/proc|/sys|/run|/tmp|/var|/opt|/snap|/root)
                    echo "跳过系统目录: $dir"
                    ;;
                *)
                    chown -R appuser:appuser "$dir"
                    echo "已授权目录: $dir"
                    ;;
            esac
        fi
    done
fi

exec gosu appuser python /app/main.py
