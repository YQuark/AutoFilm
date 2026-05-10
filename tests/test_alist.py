from sys import path
from os.path import dirname

path.append(dirname(dirname(__file__)))

import unittest
import json
import asyncio
from types import SimpleNamespace

from app.modules.alist import AlistClient, AlistPath


class TestAlistPath(unittest.TestCase):
    """
    AlistPath 测试类
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        测试类初始化
        """
        print("开始进行 AlistPath 测试")

    @classmethod
    def tearDownClass(cls) -> None:
        """
        测试类清理
        """
        print("\nAlistPath 测试通过")

    def test_alist_path_initialization_old(self) -> None:
        """
        测试 Alist V3.44 及以下版本响应的 AlistPath 的初始化
        """

        resp = json.loads(r"""
{
    "code": 200,
    "message": "success",
    "data": {
        "content": [
            {
                "name": "[ANi] 學姊是男孩 - 12 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 419322796,
                "is_dir": false,
                "modified": "2024-09-27T04:01:20.652Z",
                "created": "2024-09-27T04:01:20.652Z",
                "sign": "EseTgrOaCW_77IEnPzA5iSvbrrR3ig5sMLMJDS18dcs=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 12 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41XFn6Ln22kSCj6KvMt1_9jFMqFLC_pg3S\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 12 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41XFn6Ln22kSCj6KvMt1_9jFMqFLC_pg3S"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 11 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 352354732,
                "is_dir": false,
                "modified": "2024-09-20T04:01:30.637Z",
                "created": "2024-09-20T04:01:30.637Z",
                "sign": "QPQXGJzSiLRhf4k1pwiTeEZegwB2HoUIbxICxeENU6A=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 11 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41vPqksJwzCHzGdx2Iku9FuJKudr7h5d0j\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 11 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41vPqksJwzCHzGdx2Iku9FuJKudr7h5d0j"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 10 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 308002060,
                "is_dir": false,
                "modified": "2024-09-13T04:01:07.67Z",
                "created": "2024-09-13T04:01:07.67Z",
                "sign": "vKn6tucYavg4qEbJK_51u4X-h3yCKw2--34fiGAgOcA=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 10 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41k2ZCi6KZW1JFiFc9NEMa1470d4-Pj2YD\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 10 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41k2ZCi6KZW1JFiFc9NEMa1470d4-Pj2YD"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 09 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 332720105,
                "is_dir": false,
                "modified": "2024-09-06T04:01:09.724Z",
                "created": "2024-09-06T04:01:09.724Z",
                "sign": "l_yDbrUSrCHV_gxPEJmPUFtCSBPr8bIcX_10zb1oDb0=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 09 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41bHb7WoR8QCEpecaNwY7ISVoYnNSt_tq5\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 09 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41bHb7WoR8QCEpecaNwY7ISVoYnNSt_tq5"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 08 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 328344485,
                "is_dir": false,
                "modified": "2024-08-30T04:01:11.995Z",
                "created": "2024-08-30T04:01:11.995Z",
                "sign": "-RDlJnC--xTMWR7xsESdvJV6URRzdMI7q1P0mufiZhY=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 08 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41IFeOlMYE65DDUW1A36SRo9TouWTPsoLo\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 08 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41IFeOlMYE65DDUW1A36SRo9TouWTPsoLo"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 07 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 291486512,
                "is_dir": false,
                "modified": "2024-08-23T10:31:01.545Z",
                "created": "2024-08-23T10:31:01.545Z",
                "sign": "W8qSCmwzUuS6-021jyBxXOqFDen1d0-WBMyg6fVU0Io=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 07 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp417pRBsM4sCxY4p1mXOKkHllHAjg-E5OSw\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 07 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp417pRBsM4sCxY4p1mXOKkHllHAjg-E5OSw"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 06 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 328188852,
                "is_dir": false,
                "modified": "2024-08-16T04:01:11.149Z",
                "created": "2024-08-16T04:01:11.149Z",
                "sign": "4GrJx4ma36oXGc5iAhoWzpb2R4EtcttRhSlM4Q1Ka7M=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 06 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41cGR3xBkSFGrAiT87_93NVb1ueSYyd8oF\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 06 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41cGR3xBkSFGrAiT87_93NVb1ueSYyd8oF"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 05 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 423854342,
                "is_dir": false,
                "modified": "2024-08-02T04:02:23.632Z",
                "created": "2024-08-02T04:02:23.632Z",
                "sign": "AANDCG5m6LhkQZyLAXbqEsola2pVOrwlnhDh-HKL_a0=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 05 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41WiqLJC_3ItnDMgjbAjwjmMM-lJk1QacM\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 05 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41WiqLJC_3ItnDMgjbAjwjmMM-lJk1QacM"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 04 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 305057639,
                "is_dir": false,
                "modified": "2024-07-26T04:01:32.036Z",
                "created": "2024-07-26T04:01:32.036Z",
                "sign": "ICTRXWMoPFM_CztUmkA8YohqUwmhspe_bw8wdDXAmPM=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 04 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41TbUPlMlaYs5VonmC5hpGnCH-5HOg2gAc\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 04 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41TbUPlMlaYs5VonmC5hpGnCH-5HOg2gAc"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 316813817,
                "is_dir": false,
                "modified": "2024-07-19T04:01:34.103Z",
                "created": "2024-07-19T04:01:34.103Z",
                "sign": "isf7nNVnrZ6DjWLGjVyXG4_Qk-UoahwyOGLTH8ZTeCY=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41PveJ_pJAQI-LlZjHBz8odSAWjS3AeyUz\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41PveJ_pJAQI-LlZjHBz8odSAWjS3AeyUz"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 02 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 352701560,
                "is_dir": false,
                "modified": "2024-07-12T04:01:47.892Z",
                "created": "2024-07-12T04:01:47.892Z",
                "sign": "ythyoG8XkAR9HhwNYvgCzC7oL6sayaXTjB4YJE82a5M=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 02 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41MW6qbtrxmnxSXYBja4Cdgric_QSZMOQy\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 02 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41MW6qbtrxmnxSXYBja4Cdgric_QSZMOQy"
                }
            },
            {
                "name": "[ANi] 學姊是男孩 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
                "size": 331223033,
                "is_dir": false,
                "modified": "2024-07-05T04:06:02.649Z",
                "created": "2024-07-05T04:06:02.649Z",
                "sign": "V-u0gqUZ9J8flRZK5dNzbj5fIIJwL1VyAUmSFWskw-E=:0",
                "thumb": "",
                "type": 2,
                "hashinfo": "{\"sha1\":\"[ANi] 學姊是男孩 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41JrtN_xJzpiI02bOKsT44QnEvYLLMO8sz\"}",
                "hash_info": {
                    "sha1": "[ANi] 學姊是男孩 - 01 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp41JrtN_xJzpiI02bOKsT44QnEvYLLMO8sz"
                }
            }
        ],
        "total": 12,
        "readme": "",
        "header": "",
        "write": true,
        "provider": "ANiOpen"
    }
}
""")
        for item in resp["data"]["content"]:
            path = AlistPath(
                server_url="https://alist.nn.ci",
                base_path="/",
                full_path="/" + item["name"],
                **item,
            )
            self.assertIsInstance(path, AlistPath)
            self.assertEqual(path.name, item["name"])
            self.assertEqual(path.size, item["size"])
            self.assertEqual(path.is_dir, item["is_dir"])
            self.assertEqual(path.modified, item["modified"])
            self.assertEqual(path.created, item["created"])
            self.assertEqual(path.sign, item["sign"])
            self.assertEqual(path.thumb, item["thumb"])
            self.assertEqual(path.type, item["type"])
            self.assertEqual(path.hashinfo, item["hashinfo"])

    def test_alist_path_initialization_new(self) -> None:
        """
        测试 Alist V3.45 及以上版本响应的 AlistPath 的初始化
        """

        resp = json.loads(r"""
            {
  "code": 200,
  "message": "success",
  "data": {
    "content": [
      {
        "id": "",
        "path": "/2024-10/[ANi] 凍牌~地下麻將鬥牌錄~ - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "name": "[ANi] 凍牌~地下麻將鬥牌錄~ - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "size": 293496422,
        "is_dir": false,
        "modified": "2025-04-04T18:25:43+02:00",
        "created": "2025-04-04T18:25:43+02:00",
        "sign": "4zZglYvgsJp2fE_L-w5HFwtbosHzYBlTgLiWXc8n4Q0=:0",
        "thumb": "",
        "type": 2,
        "hashinfo": "null",
        "hash_info": null
      },
      {
        "id": "",
        "path": "/2024-10/[ANi] 轉生成貓咪的大叔 - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "name": "[ANi] 轉生成貓咪的大叔 - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "size": 21076377,
        "is_dir": false,
        "modified": "2025-04-02T13:48:24+02:00",
        "created": "2025-04-02T13:48:24+02:00",
        "sign": "ek9IvP5kjUnxZRZf6E155S8ZJ1OzN2nlSeovx65xjQs=:0",
        "thumb": "",
        "type": 2,
        "hashinfo": "null",
        "hash_info": null
      },
      {
        "id": "",
        "path": "/2024-10/[ANi] 香格里拉・開拓異境～糞作獵手挑戰神作～ 第二季 - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "name": "[ANi] 香格里拉・開拓異境～糞作獵手挑戰神作～ 第二季 - 25 [1080P][Baha][WEB-DL][AAC AVC][CHT].mp4",
        "size": 342674636,
        "is_dir": false,
        "modified": "2025-04-02T13:48:24+02:00",
        "created": "2025-04-02T13:48:24+02:00",
        "sign": "AThUy0dY-RE2sGc8Zh0lqLQw3C4cPM4WOXyVIcSHnt4=:0",
        "thumb": "",
        "type": 2,
        "hashinfo": "null",
        "hash_info": null
      }
    ],
    "total": 3,
    "readme": "",
    "header": "",
    "write": true,
    "provider": "UrlTree"
  }
}
            """)
        for item in resp["data"]["content"]:
            path = AlistPath(
                server_url="https://alist.nn.ci",
                base_path="/",
                full_path="/" + item["name"],
                **item,
            )

            self.assertIsInstance(path, AlistPath)
            self.assertEqual(path.name, item["name"])
            self.assertEqual(path.size, item["size"])
            self.assertEqual(path.is_dir, item["is_dir"])
            self.assertEqual(path.modified, item["modified"])
            self.assertEqual(path.created, item["created"])
            self.assertEqual(path.sign, item["sign"])
            self.assertEqual(path.thumb, item["thumb"])
            self.assertEqual(path.type, item["type"])
            self.assertEqual(path.hashinfo, item["hashinfo"])


class TestAlistClientIterPath(unittest.IsolatedAsyncioTestCase):
    """
    AlistClient.iter_path 测试类
    """

    @staticmethod
    def make_path(full_path: str, is_dir: bool) -> AlistPath:
        return AlistPath(
            server_url="https://alist.example.com",
            base_path="",
            full_path=full_path,
            name=full_path.rstrip("/").split("/")[-1],
            size=0,
            is_dir=is_dir,
            modified="2025-01-01T00:00:00+00:00",
            created="2025-01-01T00:00:00+00:00",
            sign="",
            thumb="",
            type=1 if is_dir else 2,
            hashinfo="",
        )

    async def test_iter_path_limits_scan_concurrency(self) -> None:
        tree = {
            "/": [
                self.make_path("/A", True),
                self.make_path("/B", True),
                self.make_path("/C", True),
            ],
            "/A": [
                self.make_path("/A/A1", True),
                self.make_path("/A/a.mp4", False),
            ],
            "/A/A1": [self.make_path("/A/A1/a1.mp4", False)],
            "/B": [self.make_path("/B/b.mp4", False)],
            "/C": [self.make_path("/C/c.mp4", False)],
        }
        active_requests = 0
        peak_requests = 0

        async def track_request() -> None:
            nonlocal active_requests, peak_requests
            active_requests += 1
            peak_requests = max(peak_requests, active_requests)
            await asyncio.sleep(0.01)
            active_requests -= 1

        async def async_api_fs_list(dir_path: str) -> list[AlistPath]:
            await track_request()
            return tree[dir_path]

        async def async_api_fs_get(path: str) -> AlistPath:
            await track_request()
            result = self.make_path(path, False)
            result.raw_url = f"https://raw.example.com{path}"
            return result

        client = SimpleNamespace(
            async_api_fs_list=async_api_fs_list,
            async_api_fs_get=async_api_fs_get,
        )

        found = []
        async for path in AlistClient.iter_path(
            client,
            dir_path="/",
            wait_time=0,
            is_detail=True,
            concurrency=2,
        ):
            found.append(path)

        self.assertEqual(
            {path.full_path for path in found},
            {"/A/a.mp4", "/A/A1/a1.mp4", "/B/b.mp4", "/C/c.mp4"},
        )
        self.assertLessEqual(peak_requests, 2)
        self.assertTrue(all(path.raw_url for path in found))


if __name__ == "__main__":
    unittest.main()
