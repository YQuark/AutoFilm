from urllib.parse import quote, unquote


class URLUtils:
    """
    URL 相关工具
    """

    SAFE_WORD = ";/?:@=&"

    @classmethod
    def encode(cls, url: str) -> str:
        """
        URL 编码
        """
        return quote(url, safe=cls.SAFE_WORD)

    @staticmethod
    def decode(strings: str) -> str:
        """
        URL 解码
        """
        return unquote(strings)

