from datetime import datetime

from pydantic import BaseModel

from app.utils import URLUtils


class AlistPath(BaseModel):
    """
    Alist 文件/目录对象
    """

    server_url: str  # 服务器地址
    base_path: str  # 用户基础路径（用于计算文件/目录在 Alist 服务器上的绝对地址）
    full_path: str  # 相对用户根文件/目录路径

    id: str | None = None  # 文件/目录 ID（Alist V3.45）
    path: str | None = None  # 相对存储器根目录的文件/目录路径（Alist V3.45）
    name: str  # 文件/目录名称
    size: int  # 文件大小
    is_dir: bool  # 是否为目录
    modified: str  # 修改时间
    created: str  # 创建时间
    sign: str  # 签名
    thumb: str  # 缩略图
    type: int  # 类型
    hashinfo: str  # 哈希信息（字符串）

    # g/api/fs/get 返回新增的字段（详细信息）
    raw_url: str | None = None  # 原始地址

    @property
    def abs_path(self) -> str:
        """
        文件/目录在 Alist 服务器上的绝对路径
        """
        return self.base_path.rstrip("/") + self.full_path

    @property
    def download_url(self) -> str:
        """
        文件下载地址
        """
        if self.sign:
            url = self.server_url + "/d" + self.abs_path + "?sign=" + self.sign
        else:
            url = self.server_url + "/d" + self.abs_path

        return URLUtils.encode(url)

    @property
    def suffix(self) -> str:
        """
        文件后缀
        """
        if self.is_dir:
            return ""
        name = self.name
        dot_index = name.rfind(".")
        if dot_index <= 0:
            return ""
        return name[dot_index:]

    def __parse_timestamp(self, time_str: str) -> float:
        """
        解析时间字符串得到时间的时间戳
        """
        dt = datetime.fromisoformat(time_str)
        return dt.timestamp()

    @property
    def modified_timestamp(self) -> float:
        """
        获得修改时间的时间戳
        """
        return self.__parse_timestamp(self.modified)