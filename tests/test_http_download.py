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

    async def test_range_download_copies_headers_per_chunk(self) -> None:
        body = b"abcdefghij"
        seen_ranges: list[str] = []
        seen_custom_headers: list[str] = []
        old_min_size = HTTPClient.MINI_STREAM_SIZE
        HTTPClient.MINI_STREAM_SIZE = 1

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "HEAD":
                return httpx.Response(
                    200,
                    headers={
                        "Content-Length": str(len(body)),
                        "Accept-Ranges": "bytes",
                    },
                )

            range_header = request.headers.get("Range", "")
            seen_ranges.append(range_header)
            seen_custom_headers.append(request.headers.get("X-Test", ""))
            start, end = range_header.removeprefix("bytes=").split("-")
            return httpx.Response(206, content=body[int(start) : int(end) + 1])

        try:
            self.client = HTTPClient()
            self.client._HTTPClient__async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

            with TemporaryDirectory() as temp_dir:
                output = Path(temp_dir) / "file.bin"
                headers = {"X-Test": "ok"}
                await self.client.download(
                    "https://example.com/file.bin",
                    output,
                    chunk_num=2,
                    headers=headers,
                )

                self.assertEqual(output.read_bytes(), body)
                self.assertEqual(set(seen_ranges), {"bytes=0-4", "bytes=5-9"})
                self.assertEqual(seen_custom_headers, ["ok", "ok"])
                self.assertNotIn("Range", headers)
        finally:
            HTTPClient.MINI_STREAM_SIZE = old_min_size


if __name__ == "__main__":
    unittest.main()
