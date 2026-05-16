from asyncio import to_thread, Semaphore, TaskGroup
from os import PathLike
from pathlib import Path
from re import compile as re_compile
import traceback

from aiofile import async_open

from app.core import logger
from app.utils import RequestUtils
from app.extensions import VIDEO_EXTS, SUBTITLE_EXTS, IMAGE_EXTS, NFO_EXTS
from app.modules.alist import AlistClient, AlistPath
from app.modules.alist2strm.mode import Alist2StrmMode

class Alist2Strm:
    def __init__(
        self,
        id: str = "",
        url: str = "http://localhost:5244",
        username: str = "",
        password: str = "",
        token: str = "",
        public_url: str = "",
        source_dir: str = "/",
        target_dir: str | PathLike = "",
        flatten_mode: bool = False,
        subtitle: bool = False,
        image: bool = False,
        nfo: bool = False,
        mode: str = "AlistURL",
        overwrite: bool = False,
        other_ext: str = "",
        max_workers: int = 50,
        max_downloaders: int = 5,
        scan_concurrency: int = 3,
        wait_time: float | int = 0,
        sync_server: bool = False,
        sync_ignore: str | None = None,
        smart_protection: dict | None = None,
        incremental: bool = True,
        incremental_level: str = "file",
        **_,
    ) -> None:
        """
        实例化 Alist2Strm 对象

        :param id: 任务标识 ID，默认为空
        :param url: Alist 服务器地址，默认为 "http://localhost:5244"
        :param public_url: 公共访问地址，用于 AlistURL 模式生成 .strm 文件（可选）
        :param username: Alist 用户名，默认为空
        :param password: Alist 密码，默认为空
        :param source_dir: 需要同步的 Alist 的目录，默认为 "/"
        :param target_dir: strm 文件输出目录，默认为当前工作目录
        :param flatten_mode: 平铺模式，将所有 Strm 文件保存至同一级目录，默认为 False
        :param subtitle: 是否下载字幕文件，默认为 False
        :param image: 是否下载图片文件，默认为 False
        :param nfo: 是否下载 .nfo 文件，默认为 False
        :param mode: Strm模式(AlistURL/RawURL/AlistPath)
        :param overwrite: 本地路径存在同名文件时是否重新生成/下载该文件，默认为 False
        :param sync_server: 是否同步服务器，启用后若服务器中删除了文件，也会将本地文件删除，默认为 False
        :param other_ext: 自定义下载后缀，使用西文半角逗号进行分割，默认为空
        :param max_workers: 最大并发数
        :param max_downloaders: 最大同时下载
        :param scan_concurrency: Alist 目录扫描 API 并发数
        :param wait_time: 遍历请求间隔时间，单位为秒，默认为 0
        :param sync_ignore: 同步时忽略的文件正则表达式
        :param smart_protection: 智能保护配置 {enabled: bool, threshold: int, grace_scans: int}
        :param incremental_level: 增量级别，file 仅跳过文件处理，directory 可跳过未变更目录
        """

        self.task_id = id
        self.client = AlistClient(url, username, password, token)
        self.mode = Alist2StrmMode.from_str(mode)
        
        if public_url and not public_url.startswith("http"):
            public_url = "https://" + public_url
        self.public_url = public_url.rstrip("/") if public_url else None

        self.source_dir = self._normalize_remote_dir(source_dir)
        self.target_dir = Path(target_dir)

        self.flatten_mode = flatten_mode
        if flatten_mode:
            subtitle = image = nfo = False

        download_exts: set[str] = set()
        if subtitle:
            download_exts |= SUBTITLE_EXTS
        if image:
            download_exts |= IMAGE_EXTS
        if nfo:
            download_exts |= NFO_EXTS
        if other_ext:
            download_exts |= frozenset(
                self._normalize_ext(ext) for ext in other_ext.split(",") if ext.strip()
            )

        self.download_exts = download_exts
        self.process_file_exts = VIDEO_EXTS | download_exts

        self.overwrite = overwrite
        self.__max_workers = Semaphore(max_workers)
        self.__max_downloaders = Semaphore(max_downloaders)
        self.scan_concurrency = scan_concurrency
        self.wait_time = wait_time
        self.sync_server = sync_server

        if sync_ignore:
            self.sync_ignore_pattern = re_compile(sync_ignore)
        else:
            self.sync_ignore_pattern = None
        
        if smart_protection and smart_protection.get('enabled', False):
            from app.modules.alist2strm.strm_protection import StrmProtectionManager
            threshold = smart_protection.get('threshold', 100)
            grace_scans = smart_protection.get('grace_scans', 3)
            self.strm_protection = StrmProtectionManager(
                self.target_dir, id, threshold, grace_scans
            )
            logger.info(f".strm 保护已启用：阈值={threshold}，宽限期={grace_scans}")
        else:
            self.strm_protection = None

        self.incremental = incremental
        self.incremental_level = str(incremental_level or "file").strip().lower()
        if self.incremental_level not in {"file", "directory"}:
            logger.warning(
                f"未知 incremental_level={incremental_level}，已回退为 file"
            )
            self.incremental_level = "file"

    def _init_scan_state(self) -> None:
        """初始化扫描状态变量、增量清单和计数器。"""
        self.bdmv_collections: dict[str, list[tuple[AlistPath, int]]] = {}
        self.bdmv_largest_files: dict[str, AlistPath] = {}

        if self.incremental:
            from app.modules.alist2strm.manifest import ScanManifest
            self.__manifest = ScanManifest(self.target_dir, self.task_id)
            self.__manifest.load()
            self.__manifest_keys: set[str] = set()
            logger.info(
                f"增量扫描已启用，级别={self.incremental_level}，清单现有 "
                f"{self.__manifest.entry_count} 个条目"
            )
        else:
            self.__manifest = None
            self.__manifest_keys = set()
        self.__skipped_dir_prefixes: set[str] = set()
        self.__scanned_dir_count = 0
        self.__skipped_dir_count = 0
        self.__discovered_file_count = 0
        self.__processed_file_count = 0
        self.processed_local_paths = set()

    def _on_dir_scanned(self, _dir_path: str, items: list[AlistPath]) -> None:
        """目录扫描完成回调：更新统计计数器。"""
        self.__scanned_dir_count += 1
        self.__discovered_file_count += sum(1 for item in items if not item.is_dir)

    def _should_enter_dir(self, path: AlistPath) -> bool:
        """判断是否需要进入目录子树进行扫描。"""
        if (
            self.__manifest is None
            or self.incremental_level != "directory"
            or self.overwrite
        ):
            return True

        dir_key = self.__manifest.dir_key(path.full_path)
        self.__manifest_keys.add(dir_key)
        try:
            if self.__manifest.is_changed(
                dir_key, path.modified_timestamp, path.size
            ):
                self.__manifest.mark_directory(
                    path.full_path, path.modified_timestamp, path.size
                )
                return True
        except ValueError as e:
            logger.warning(
                f"目录 {path.full_path} 修改时间解析失败，改为递归扫描：{e}"
            )
            return True

        self.__skipped_dir_count += 1
        self.__skipped_dir_prefixes.add(path.full_path)
        logger.debug(f"目录 {path.full_path} 未变更，跳过子树扫描")
        return False

    def _file_filter(self, path: AlistPath) -> bool:
        """根据配置判断是否需要处理该文件，并记录本地路径用于后续清理。"""
        if path.is_dir:
            return False

        if path.name in ("Thumbs.db", ".DS_Store") or "@eaDir" in path.full_path.split("/"):
            return False

        if "/BDMV/" in path.full_path.upper() and not self._is_bdmv_file(path):
            logger.debug(f"跳过 BDMV 文件夹内的文件: {path.name}")
            return False

        if path.suffix.lower() not in self.process_file_exts:
            logger.debug(f"文件 {path.name} 不在处理列表中")
            return False

        if self._is_bdmv_file(path):
            self._collect_bdmv_file(path)
            return False

        try:
            local_path = self.__get_local_path(path)
        except OSError as e:
            logger.warning(f"获取 {path.full_path} 本地路径失败：{e}")
            return False

        self.processed_local_paths.add(local_path)

        if self.__manifest is not None:
            self.__manifest_keys.add(path.full_path)

        if self.__manifest is not None and not self.overwrite:
            if not self.__manifest.is_changed(
                path.full_path, path.modified_timestamp, path.size
            ):
                try:
                    if local_path.exists():
                        return False
                except OSError:
                    pass

        if not self.overwrite:
            try:
                local_stat = local_path.stat()
            except OSError:
                return True

            if path.suffix.lower() in IMAGE_EXTS:
                if local_stat.st_size != path.size:
                    logger.warning(
                        f"文件 {local_path.name} 大小不一致（本地: {local_stat.st_size}, 远端: {path.size}），重新下载 {path.full_path}"
                    )
                    return True
            elif path.suffix.lower() in self.download_exts:
                if local_stat.st_mtime < path.modified_timestamp:
                    logger.debug(
                        f"文件 {local_path.name} 已过期，需要重新处理 {path.full_path}"
                    )
                    return True
                if local_stat.st_size != path.size:
                    logger.warning(
                        f"文件 {local_path.name} 大小不一致（本地: {local_stat.st_size}, 远端: {path.size}），重新下载 {path.full_path}"
                    )
                    return True
            logger.debug(
                f"文件 {local_path.name} 已存在，跳过处理 {path.full_path}"
            )
            return False

        return True

    async def _stage1_scan_and_process(self) -> int:
        """第一阶段：遍历 Alist 目录树并处理普通文件。返回处理的文件数。"""
        is_detail = self.mode == Alist2StrmMode.RawURL
        process_count = 0

        async def process_with_limit(path: AlistPath) -> None:
            async with self.__max_workers:
                await self.__file_processer(path)

        async with TaskGroup() as tg:
            async for path in self.client.iter_path(
                dir_path=self.source_dir,
                wait_time=self.wait_time,
                is_detail=is_detail,
                filter=self._file_filter,
                dir_filter=self._should_enter_dir,
                on_directory_scanned=self._on_dir_scanned,
                concurrency=self.scan_concurrency,
            ):
                process_count += 1
                if process_count % 100 == 0:
                    logger.info(f"处理进度：已发现 {process_count} 个待处理文件 ...")
                tg.create_task(process_with_limit(path))

        logger.info(
            f"遍历完成：扫描目录 {self.__scanned_dir_count} 个，"
            f"跳过目录 {self.__skipped_dir_count} 个，"
            f"发现文件 {self.__discovered_file_count} 个，"
            f"待处理文件 {process_count} 个"
        )
        return process_count

    async def _stage2_process_bdmv(self) -> None:
        """第二阶段：处理 BDMV 目录中收集的最大文件。"""
        self._finalize_bdmv_collections()

        bdmv_count = len(self.bdmv_largest_files)
        if bdmv_count == 0:
            return
        logger.info(f"开始处理 {bdmv_count} 个 BDMV 目录")

        for bdmv_root, largest_file in self.bdmv_largest_files.items():
            bdmv_key = f"bdmv:{bdmv_root}"
            if self.__manifest is not None:
                self.__manifest_keys.add(bdmv_key)

            if self.__manifest is not None and not self.overwrite:
                if not self.__manifest.is_changed(
                    bdmv_key, largest_file.modified_timestamp, largest_file.size
                ):
                    local_path = self.__get_local_path(largest_file)
                    self.processed_local_paths.add(local_path)
                    try:
                        if local_path.exists():
                            logger.info(f"BDMV {bdmv_root} 未变更，跳过处理")
                            continue
                    except OSError:
                        pass

            try:
                logger.info(f"处理 BDMV 目录: {bdmv_root}")
                logger.info(f"最大文件: {largest_file.full_path}")

                if self.mode == Alist2StrmMode.RawURL and not largest_file.raw_url:
                    logger.debug(f"重新获取 BDMV 文件详细信息: {largest_file.full_path}")
                    try:
                        updated_path = await self.client.async_api_fs_get(largest_file.full_path)
                        original_full_path = largest_file.full_path
                        largest_file = updated_path
                        largest_file.full_path = original_full_path
                    except Exception as e:
                        logger.warning(f"重新获取 BDMV 文件详细信息失败: {e}")

                await self.__file_processer(largest_file)

                local_path = self.__get_local_path(largest_file)
                self.processed_local_paths.add(local_path)

                if self.__manifest is not None:
                    self.__manifest.mark_processed(
                        bdmv_key,
                        largest_file.modified_timestamp,
                        largest_file.size,
                    )

                logger.info(f"BDMV 文件处理完成: {largest_file.name}")
            except Exception as e:
                logger.error(f"处理 BDMV 文件 {largest_file.full_path} 时出错：{e}")
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                continue

    async def _stage3_cleanup_and_save(self) -> None:
        """第三阶段：清理本地孤立文件并保存扫描清单。"""
        if self.sync_server and self.__skipped_dir_prefixes:
            logger.warning(
                f"本轮目录级增量跳过了 {len(self.__skipped_dir_prefixes)} 个目录，"
                "已跳过本地删除清理，避免误删未遍历子树"
            )
        elif self.sync_server:
            await self.__cleanup_local_files()
            logger.info("清理过期的 .strm 文件完成")

        if self.__manifest is not None:
            self.__manifest.prune_stale(
                self.__manifest_keys, self.__skipped_dir_prefixes
            )
            self.__manifest.save()
            logger.info(f"扫描清单已更新: {self.__manifest.entry_count} 个条目")

    async def run(self) -> None:
        """Alist2Strm 任务主入口。"""
        self._init_scan_state()

        await self._stage1_scan_and_process()
        await self._stage2_process_bdmv()
        await self._stage3_cleanup_and_save()

        logger.info(
            f"文件处理完成：实际处理 {self.__processed_file_count} 个文件"
        )
        logger.info("Alist2Strm 处理完成")

    async def __file_processer(self, path: AlistPath) -> None:
        """
        异步保存文件至本地

        :param path: AlistPath 对象
        """
        local_path = self.__get_local_path(path)
        logger.debug(f"__file_processer: 处理文件 {path.full_path} -> 本地路径 {local_path} | 模式 {self.mode}")

        # 统一的 URL 生成逻辑，BDMV 文件与普通文件使用相同的逻辑
        if self.mode == Alist2StrmMode.AlistURL:
            content = path.download_url
            # 如果定义了 public_url，则替换服务器 URL 为公共访问 URL
            if self.public_url:
                content = content.replace(self.client.url, self.public_url)
        elif self.mode == Alist2StrmMode.RawURL:
            content = path.raw_url
        elif self.mode == Alist2StrmMode.AlistPath:
            content = path.full_path

        logger.debug(f"__file_processer: 初始 content = {content}")

        if not content:
            logger.warning(f"文件 {path.full_path} 的内容为空，跳过处理")
            return

        await to_thread(local_path.parent.mkdir, parents=True, exist_ok=True)

        logger.debug(f"开始处理 {local_path} | 内容: {content}")
        if local_path.suffix == ".strm":
            async with async_open(local_path, mode="w", encoding="utf-8") as file:
                await file.write(content)
            logger.info(f"{local_path.name} 创建成功")
        else:
            async with self.__max_downloaders:
                await RequestUtils.download(path.download_url, local_path)
                logger.info(f"{local_path.name} 下载成功")

        if self.__manifest is not None:
            self.__manifest.mark_processed(
                path.full_path, path.modified_timestamp, path.size
            )
        self.__processed_file_count += 1

    def __get_local_path(self, path: AlistPath) -> Path:
        """
        根据给定的 AlistPath 对象和当前的配置，计算出本地文件路径。

        :param path: AlistPath 对象
        :return: 本地文件路径
        """
        # 检查是否为 BDMV 文件
        if self._is_bdmv_file(path):
            bdmv_root = self._get_bdmv_root_dir(path)
            if bdmv_root and self._should_process_bdmv_file(path):
                # 为 BDMV 文件生成特殊路径
                movie_title = self._get_movie_title_from_bdmv_path(bdmv_root)
                
                if self.flatten_mode:
                    local_path = self.target_dir / f"{movie_title}.strm"
                else:
                    # 计算相对于 source_dir 的路径
                    relative_path = self._relative_remote_path(bdmv_root)
                    
                    # 将 .strm 文件放在电影根目录下，使用电影标题命名
                    local_path = self.target_dir / relative_path / f"{movie_title}.strm"
                
                return local_path

        # 原有逻辑保持不变
        if self.flatten_mode:
            local_path = self.target_dir / path.name
        else:
            relative_path = self._relative_remote_path(path.full_path)
            local_path = self.target_dir / relative_path

        if path.suffix.lower() in VIDEO_EXTS:
            local_path = local_path.with_suffix(".strm")

        return local_path

    @staticmethod
    def _normalize_remote_dir(path: str) -> str:
        """
        规范化 Alist 远端目录，避免末尾斜杠差异影响相对路径计算。
        """
        normalized = "/" + str(path or "/").strip("/")
        return "/" if normalized == "/" else normalized

    @staticmethod
    def _normalize_ext(ext: str) -> str:
        """
        规范化扩展名配置，兼容 ".zip, md" 等写法。
        """
        normalized = ext.strip().lower()
        if not normalized:
            return ""
        return normalized if normalized.startswith(".") else f".{normalized}"

    def _relative_remote_path(self, full_path: str) -> str:
        """
        计算远端路径相对 source_dir 的本地相对路径。
        """
        if self.source_dir == "/":
            return full_path.lstrip("/")

        prefix = self.source_dir.rstrip("/") + "/"
        if full_path == self.source_dir:
            return ""
        if full_path.startswith(prefix):
            return full_path[len(prefix):]
        return full_path.lstrip("/")

    async def __cleanup_local_files(self) -> None:
        """
        删除服务器中已删除的本地的 .strm 文件及其关联文件
        如果文件后缀在 sync_ignore 中，则不会被删除
        """
        logger.info("开始清理本地文件")

        if not self.target_dir.exists():
            logger.warning(f"目标目录不存在，跳过清理：{self.target_dir}")
            return

        if self.flatten_mode:
            all_local_files = [f for f in self.target_dir.iterdir() if f.is_file()]
        else:
            all_local_files = [f for f in self.target_dir.rglob("*") if f.is_file()]

        all_local_files = [
            f for f in all_local_files
            if not (
                f.suffix == ".json"
                and (
                    f.name.startswith(".autofilm_strm_")
                    or f.name.startswith(".autofilm_manifest_")
                )
            )
        ]

        files_to_delete = set(all_local_files) - self.processed_local_paths
        strm_present = None
        if self.strm_protection:
            strm_present = {f for f in self.processed_local_paths if f.suffix == '.strm'}
        
        if not files_to_delete:
            if self.strm_protection:
                self.strm_protection.process(set(), strm_present)
                self.strm_protection.save()
            return
        
        strm_to_delete = {f for f in files_to_delete if f.suffix == '.strm'}
        other_files = files_to_delete - strm_to_delete
        
        if self.strm_protection:
            strm_to_delete_before = len(strm_to_delete)
            strm_to_delete = self.strm_protection.process(strm_to_delete, strm_present)
            self.strm_protection.save()
            if len(strm_to_delete) < strm_to_delete_before:
                from app.utils.notify import send_notification
                await send_notification(
                    "Alist2Strm 保护触发",
                    f"任务 [{self.task_id}]: {strm_to_delete_before} 个文件待删除，"
                    f"{strm_to_delete_before - len(strm_to_delete)} 个被保护延后",
                    "warning",
                )

        files_to_delete = strm_to_delete | other_files
        
        for file_path in files_to_delete:
            try:
                target_root = self.target_dir.resolve()
                resolved_file = file_path.resolve()
                if resolved_file != target_root and target_root not in resolved_file.parents:
                    logger.error(f"跳过目标目录外的文件：{file_path}")
                    continue
            except OSError as e:
                logger.error(f"解析文件路径失败，跳过删除 {file_path}：{e}")
                continue

            # 检查文件是否匹配忽略正则表达式
            if self.sync_ignore_pattern and self.sync_ignore_pattern.search(
                file_path.name
            ):
                logger.debug(f"文件 {file_path.name} 在忽略列表中，跳过删除")
                continue

            try:
                if file_path.exists():
                    await to_thread(file_path.unlink)
                    logger.info(f"删除文件：{file_path}")

                    # 检查并删除空目录
                    parent_dir = file_path.parent
                    while parent_dir != self.target_dir:
                        if any(parent_dir.iterdir()):
                            break  # 目录不为空，跳出循环
                        else:
                            parent_dir.rmdir()
                            logger.info(f"删除空目录：{parent_dir}")
                        parent_dir = parent_dir.parent
            except Exception as e:
                logger.error(f"删除文件 {file_path} 失败：{e}")

    def _is_bdmv_file(self, path: AlistPath) -> bool:
        """
        检查文件是否为 BDMV 结构中的 .m2ts 文件
        
        :param path: AlistPath 对象
        :return: 是否为 BDMV 文件
        """
        return "/BDMV/STREAM/" in path.full_path.upper() and path.suffix.lower() == ".m2ts"

    def _get_bdmv_root_dir(self, path: AlistPath) -> str:
        """
        获取 BDMV 文件的根目录路径
        
        :param path: BDMV 中的文件路径
        :return: BDMV 根目录路径
        """
        full_path = path.full_path
        bdmv_index = full_path.upper().find("/BDMV/")
        if bdmv_index != -1:
            return full_path[:bdmv_index]
        return ""

    def _get_movie_title_from_bdmv_path(self, bdmv_root: str) -> str:
        """
        从 BDMV 根目录路径提取电影标题
        
        :param bdmv_root: BDMV 根目录路径
        :return: 电影标题
        """
        # 获取最后一个目录名作为电影标题
        return Path(bdmv_root).name

    def _collect_bdmv_file(self, path: AlistPath) -> None:
        """
        收集 BDMV 文件信息
        
        :param path: BDMV 中的 .m2ts 文件路径
        """
        bdmv_root = self._get_bdmv_root_dir(path)
        if not bdmv_root:
            return

        if bdmv_root not in self.bdmv_collections:
            self.bdmv_collections[bdmv_root] = []

        # 添加文件信息到集合中
        self.bdmv_collections[bdmv_root].append((path, path.size))
        logger.debug(f"收集 BDMV 文件: {path.full_path}, 大小: {path.size}")

    def _finalize_bdmv_collections(self) -> None:
        """
        完成 BDMV 文件收集，确定每个 BDMV 目录中的最大文件
        """
        for bdmv_root, files in self.bdmv_collections.items():
            if not files:
                continue

            movie_title = self._get_movie_title_from_bdmv_path(bdmv_root)
            logger.info(f"BDMV 目录 '{movie_title}' 中发现 {len(files)} 个 .m2ts 文件:")
            
            # 按大小排序并显示所有文件
            sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
            for i, (file_path, file_size) in enumerate(sorted_files):
                size_mb = file_size / (1024 * 1024)
                status = "✓ 选中" if i == 0 else "  跳过"
                logger.info(f"  {status} {file_path.name}: {size_mb:.1f} MB ({file_size} 字节)")

            # 找出最大的文件
            largest_file = max(files, key=lambda x: x[1])
            self.bdmv_largest_files[bdmv_root] = largest_file[0]
            
            largest_size_mb = largest_file[1] / (1024 * 1024)
            logger.info(f"BDMV 目录 '{movie_title}' 最终选择: {largest_file[0].name} ({largest_size_mb:.1f} MB)")

    def _should_process_bdmv_file(self, path: AlistPath) -> bool:
        """
        检查 BDMV 文件是否应该被处理（即是否为最大文件）
        
        :param path: BDMV 中的 .m2ts 文件路径
        :return: 是否应该处理
        """
        bdmv_root = self._get_bdmv_root_dir(path)
        if not bdmv_root:
            return False

        largest_file = self.bdmv_largest_files.get(bdmv_root)
        return largest_file is not None and largest_file.full_path == path.full_path

