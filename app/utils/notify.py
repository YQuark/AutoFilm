"""通知模块：支持 Telegram / Bark / Webhook 推送"""

from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import quote

from app.core import logger


class Notifier(ABC):
    """通知器抽象基类"""

    @abstractmethod
    async def send(self, title: str, body: str, level: str = "info") -> bool:
        """发送通知，返回 True 表示成功"""
        ...


class TelegramNotifier(Notifier):
    """Telegram Bot 通知器"""

    def __init__(self, config: dict[str, Any]) -> None:
        self._bot_token = config.get("bot_token", "")
        self._chat_id = config.get("chat_id", "")

    async def send(self, title: str, body: str, level: str = "info") -> bool:
        if not self._bot_token or not self._chat_id:
            logger.warning("[通知] Telegram 缺少 bot_token 或 chat_id")
            return False

        from app.utils.http import RequestUtils

        text = f"*{title}*\n{body}"
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        resp = await RequestUtils.post(
            url, json={"chat_id": self._chat_id, "text": text, "parse_mode": "Markdown"}
        )
        if resp is None or resp.status_code != 200:
            logger.warning(f"[通知] Telegram 发送失败: {resp}")
            return False
        return True


class BarkNotifier(Notifier):
    """Bark (iOS) 通知器"""

    def __init__(self, config: dict[str, Any]) -> None:
        self._url = (config.get("url") or "").rstrip("/")
        self._sound = config.get("sound", "")

    async def send(self, title: str, body: str, level: str = "info") -> bool:
        if not self._url:
            logger.warning("[通知] Bark 缺少 URL")
            return False

        from app.utils.http import RequestUtils

        encoded_title = quote(title, safe="")
        encoded_body = quote(body, safe="")
        url = f"{self._url}/{encoded_title}/{encoded_body}"
        if self._sound:
            url += f"?sound={quote(self._sound, safe='')}"
        resp = await RequestUtils.get(url)
        if resp is None or resp.status_code != 200:
            logger.warning(f"[通知] Bark 发送失败: {resp}")
            return False
        return True


class WebhookNotifier(Notifier):
    """通用 Webhook 通知器"""

    def __init__(self, config: dict[str, Any]) -> None:
        self._url = config.get("url", "")
        self._headers: dict[str, str] = config.get("headers") or {}
        self._template: str | None = config.get("template") or None

    async def send(self, title: str, body: str, level: str = "info") -> bool:
        if not self._url:
            logger.warning("[通知] Webhook 缺少 URL")
            return False

        from app.utils.http import RequestUtils

        if self._template:
            payload_str = (
                self._template.replace("{title}", title)
                .replace("{body}", body)
                .replace("{level}", level)
            )
            import json
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = payload_str
        else:
            payload = {"title": title, "body": body, "level": level}

        extra_headers = self._headers if isinstance(self._headers, dict) else {}
        resp = await RequestUtils.post(self._url, json=payload, headers=extra_headers)
        if resp is None or resp.status_code >= 400:
            logger.warning(f"[通知] Webhook 发送失败: {resp}")
            return False
        return True


_NOTIFIER_REGISTRY: dict[str, type[Notifier]] = {
    "telegram": TelegramNotifier,
    "bark": BarkNotifier,
    "webhook": WebhookNotifier,
}


def register_notifier(name: str, cls: type[Notifier]) -> None:
    """注册自定义通知器类型"""
    _NOTIFIER_REGISTRY[name.lower()] = cls


async def send_notification(
    title: str, body: str, level: str = "info"
) -> None:
    """向所有已启用的通知器发送通知"""

    from app.core import settings

    notifier_list = settings.NotifierList
    if not notifier_list:
        return

    for cfg in notifier_list:
        if not isinstance(cfg, dict):
            continue
        if not cfg.get("enabled", True):
            continue

        ntype = (cfg.get("type") or "").lower()
        nconfig = cfg.get("config")
        if not isinstance(nconfig, dict):
            nconfig = {}

        cls = _NOTIFIER_REGISTRY.get(ntype)
        if cls is None:
            logger.warning(f"[通知] 未知通知器类型: {ntype}")
            continue

        try:
            notifier = cls(nconfig)
            await notifier.send(title, body, level)
        except Exception as e:
            logger.error(f"[通知] {ntype} 通知器异常: {e}")
