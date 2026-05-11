import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.utils.http import HTTPClient


class TestHTTPClientDownload(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        if hasattr(self, "client"):
            await self.client.close_async_client()
            self.client.close_sync_client()

    async def test_download_without_range_support_uses_single_stream(self) -> None:
        body = b"hello world"

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "HEAD":
                return httpx.Response(200, headers={"Content-Length": str(len(body))})
            self.assertNotIn("Range", request.headers)
            return httpx.Response(200, content=body)

        self.client = HTTPClient()
        self.client._HTTPClient__async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "file.bin"
            await self.client.download("https://example.com/file.bin", output, chunk_num=4)

            self.assertEqual(output.read_bytes(), body)

    async def test_download_rejects_size_mismatch(self) -> None:
        body = b"short"

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "HEAD":
                return httpx.Response(200, headers={"Content-Length": "99"})
            return httpx.Response(200, content=body)

        self.client = HTTPClient()
        self.client._HTTPClient__async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "file.bin"

            with self.assertRaisesRegex(RuntimeError, "文件大小不一致"):
                await self.client.download("https://example.com/file.bin", output, chunk_num=1)


if __name__ == "__main__":
    unittest.main()
