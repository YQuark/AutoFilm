#!/bin/sh
# 以 root 身份修正挂载目录权限，再以 appuser 身份启动应用
set -e

chown appuser:appuser /config /logs /media /fonts 2>/dev/null || true

# 从配置文件中提取 target_dir 并授权（仅允许常见挂载卷路径）
CONFIG="/config/config.yaml"
if [ -f "$CONFIG" ]; then
    awk '/target_dir:/ {gsub(/[" ]/, "", $2); print $2}' "$CONFIG" | while read -r dir; do
        if [ -d "$dir" ]; then
            case "$dir" in
                /media*|/data*|/mnt*|/config*|/logs*)
                    chown -R appuser:appuser "$dir"
                    echo "已授权目录: $dir"
                    ;;
                *)
                    echo "跳过非挂载卷目录: $dir（如需授权请将目录挂载到 /media、/data 或 /mnt 下）"
                    ;;
            esac
        fi
    done
fi

exec gosu appuser python /app/main.py
