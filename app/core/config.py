from pathlib import Path
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
        """
        if not self.CONFIG.exists():
            return {}

        try:
            with self.CONFIG.open(mode="r", encoding="utf-8") as file:
                data = safe_load(file) or {}
        except YAMLError as e:
            raise RuntimeError(f"配置文件 {self.CONFIG} YAML 解析失败：{e}") from e

        if not isinstance(data, dict):
            raise RuntimeError(f"配置文件 {self.CONFIG} 顶层必须是 YAML 映射")
        return data

    def __get_section(self, name: str, default: Any) -> Any:
        """
        获取配置段，保持缺失字段使用默认值的兼容行为。
        """
        return self.__load_config().get(name, default)

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
            return max(5, int(section.get("hot_reload_interval", 30)))
        return 30


settings = SettingManager()
