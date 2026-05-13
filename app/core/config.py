from pathlib import Path
from os import getenv
from yaml import YAMLError, safe_load
from typing import Any

from app.version import APP_VERSION


class SettingManager:
    """
    系统配置
    """

    # APP 名称
    APP_NAME: str = "Autofilm"
    # APP 版本
    APP_VERSION: str = APP_VERSION
    # 开发者模式
    DEBUG: bool = False

    def __init__(self) -> None:
        """
        初始化 SettingManager 对象
        """
        self.__config_cache: dict[str, Any] | None = None
        self.__config_cache_mtime: float = 0
        self.__mkdir()
        self.__load_mode()

    def __mkdir(self) -> None:
        """
        创建目录
        """
        if not self.CONFIG_DIR.exists():
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not self.LOG_DIR.exists():
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def __load_mode(self) -> None:
        """
        加载模式
        """
        settings = self.__get_section("Settings", {})
        is_dev = settings.get("DEV", False) if isinstance(settings, dict) else False

        self.DEBUG = is_dev

    def __load_config(self) -> dict[str, Any]:
        """
        加载配置文件。缺失或空配置按空配置处理，格式错误明确报错。
        基于文件 mtime 缓存解析结果，避免每次属性访问重复 I/O 和 YAML 解析。
        """
        if not self.CONFIG.exists():
            self.__config_cache = None
            self.__config_cache_mtime = 0
            return {}

        try:
            current_mtime = self.CONFIG.stat().st_mtime
        except OSError:
            current_mtime = 0

        if self.__config_cache is not None and current_mtime <= self.__config_cache_mtime:
            return self.__config_cache

        try:
            with self.CONFIG.open(mode="r", encoding="utf-8") as file:
                data = safe_load(file) or {}
        except YAMLError as e:
            raise RuntimeError(f"配置文件 {self.CONFIG} YAML 解析失败：{e}") from e

        if not isinstance(data, dict):
            raise RuntimeError(f"配置文件 {self.CONFIG} 顶层必须是 YAML 映射")

        self.__config_cache = data
        self.__config_cache_mtime = current_mtime
        return data

    def __get_section(self, name: str, default: Any) -> Any:
        """
        获取配置段，保持缺失字段使用默认值的兼容行为。
        """
        return self.__load_config().get(name, default)

    @staticmethod
    def __env_bool(name: str) -> bool | None:
        value = getenv(name)
        if value is None:
            return None
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def __env_int(name: str) -> int | None:
        value = getenv(name)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @property
    def BASE_DIR(self) -> Path:
        """
        后端程序基础路径 AutoFilm/app
        """
        return Path(__file__).parents[2]

    @property
    def CONFIG_DIR(self) -> Path:
        """
        配置文件路径
        """
        return self.BASE_DIR / "config"

    @property
    def LOG_DIR(self) -> Path:
        """
        日志文件路径
        """
        return self.BASE_DIR / "logs"

    @property
    def STATE_DIR(self) -> Path:
        """
        运行状态文件路径
        """
        state_dir = self.CONFIG_DIR / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir

    @property
    def CONFIG(self) -> Path:
        """
        配置文件
        """
        return self.CONFIG_DIR / "config.yaml"

    @property
    def LOG(self) -> Path:
        """
        日志文件
        """
        if self.DEBUG:
            return self.LOG_DIR / "dev.log"
        else:
            return self.LOG_DIR / "AutoFilm.log"

    @property
    def AlistServerList(self) -> list[dict[str, Any]]:
        alist_server_list = self.__get_section("Alist2StrmList", [])
        return alist_server_list if isinstance(alist_server_list, list) else []

    @property
    def Ani2AlistList(self) -> list[dict[str, Any]]:
        ani2alist_list = self.__get_section("Ani2AlistList", [])
        return ani2alist_list if isinstance(ani2alist_list, list) else []

    @property
    def NotifierList(self) -> list[dict[str, Any]]:
        notifier_list = self.__get_section("NotifierList", [])
        return notifier_list if isinstance(notifier_list, list) else []

    @property
    def HotReloadEnabled(self) -> bool:
        section = self.__get_section("Settings", {})
        if isinstance(section, dict):
            return section.get("hot_reload", True)
        return True

    @property
    def HotReloadInterval(self) -> int:
        section = self.__get_section("Settings", {})
        if isinstance(section, dict):
            value = section.get("hot_reload_interval", 30)
            try:
                return max(5, int(value))
            except (TypeError, ValueError):
                return 30
        return 30

    @property
    def WebEnabled(self) -> bool:
        env_value = self.__env_bool("AUTOFILM_WEB_ENABLED")
        if env_value is not None:
            return env_value
        section = self.__get_section("Settings", {})
        if isinstance(section, dict):
            return bool(section.get("web_enabled", False))
        return False

    @property
    def WebHost(self) -> str:
        env_value = getenv("AUTOFILM_WEB_HOST")
        if env_value:
            return env_value
        section = self.__get_section("Settings", {})
        if isinstance(section, dict):
            return str(section.get("web_host", "0.0.0.0") or "0.0.0.0")
        return "0.0.0.0"

    @property
    def WebPort(self) -> int:
        env_value = self.__env_int("AUTOFILM_WEB_PORT")
        if env_value is not None:
            return min(65535, max(1, env_value))
        section = self.__get_section("Settings", {})
        if isinstance(section, dict):
            value = section.get("web_port", 8000)
            try:
                port = int(value)
            except (TypeError, ValueError):
                return 8000
            return min(65535, max(1, port))
        return 8000


settings = SettingManager()
