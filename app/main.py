import argparse
import asyncio
import logging
import traceback
from datetime import datetime
from sys import path
from os.path import dirname
from typing import Any

path.append(dirname(dirname(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type:ignore
from apscheduler.triggers.cron import CronTrigger  # type:ignore

from app.core import settings, logger
from app.extensions import LOGO
from app.modules import Alist2Strm, Ani2Alist, LibraryPoster


class _MaxInstancesFilter(logging.Filter):
    """抑制 APScheduler max_instances 跳过日志（任务执行时间超过 cron 间隔时的正常行为）"""

    def filter(self, record: logging.LogRecord) -> bool:
        return "maximum number of running instances reached" not in record.getMessage()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoFilm - 媒体自动化工具")
    parser.add_argument("--run", type=str, metavar="ID", help="立即执行指定 ID 的任务（执行完退出）")
    parser.add_argument("--run-all", action="store_true", help="立即执行所有任务（执行完退出）")
    return parser.parse_args()


def print_logo() -> None:
    print(LOGO)
    print(f" {settings.APP_NAME} {settings.APP_VERSION} ".center(65, "="))
    print("")


def get_task_id(config: dict[str, Any]) -> str:
    return str(config.get("id") or "<未命名>")


async def run_module_task(module_name: str, task_id: str, task: Any) -> None:
    try:
        await task.run()
    except Exception as e:
        logger.error(f"{module_name} 任务 {task_id} 执行失败：{e}")
        logger.debug(traceback.format_exc())


async def run_config_task(
    module_name: str, config: dict[str, Any], task_cls: type
) -> None:
    task_id = get_task_id(config)
    try:
        task = task_cls(**config)
    except Exception as e:
        logger.error(f"{module_name} 任务 {task_id} 初始化失败：{e}")
        logger.debug(traceback.format_exc())
        return
    await run_module_task(module_name, task_id, task)


def add_scheduled_jobs(
    scheduler: AsyncIOScheduler,
    configs: list[dict[str, Any]],
    module_name: str,
    task_cls: type,
) -> None:
    for config in configs:
        task_id = get_task_id(config)
        cron = config.get("cron")
        if not cron:
            logger.warning(f"{task_id} 未设置 cron")
            continue

        try:
            task = task_cls(**config)
            scheduler.add_job(
                run_module_task,
                args=[module_name, task_id, task],
                trigger=CronTrigger.from_crontab(cron),
                next_run_time=datetime.now(),
            )
        except Exception as e:
            logger.error(f"{module_name} 任务 {task_id} 添加失败：{e}")
            logger.debug(traceback.format_exc())
            continue

        logger.info(f"{task_id} 已被添加至后台任务")


async def main() -> None:
    args = parse_args()

    # 手动模式：执行一次后退出
    if args.run or args.run_all:
        target = args.run
        matched = False
        for server in settings.AlistServerList:
            if args.run_all or server.get("id") == target:
                matched = True
                task_id = get_task_id(server)
                logger.info(f"手动执行 Alist2Strm 任务：{task_id}")
                await run_config_task("Alist2Strm", server, Alist2Strm)
        for server in settings.Ani2AlistList:
            if args.run_all or server.get("id") == target:
                matched = True
                task_id = get_task_id(server)
                logger.info(f"手动执行 Ani2Alist 任务：{task_id}")
                await run_config_task("Ani2Alist", server, Ani2Alist)
        for poster in settings.LibraryPosterList:
            if args.run_all or poster.get("id") == target:
                matched = True
                task_id = get_task_id(poster)
                logger.info(f"手动执行 LibraryPoster 任务：{task_id}")
                await run_config_task("LibraryPoster", poster, LibraryPoster)
        if args.run and not matched:
            logger.warning(f"未找到 ID 为 {target} 的任务")
        logger.info("手动执行完成")
        return

    # Cron 调度模式
    logger.info(f"AutoFilm {settings.APP_VERSION} 启动中...")
    logger.debug(f"是否开启 DEBUG 模式: {settings.DEBUG}")

    scheduler = AsyncIOScheduler()

    if settings.AlistServerList:
        logger.info("检测到 Alist2Strm 模块配置，正在添加至后台任务")
        add_scheduled_jobs(scheduler, settings.AlistServerList, "Alist2Strm", Alist2Strm)
    else:
        logger.warning("未检测到 Alist2Strm 模块配置")

    if settings.Ani2AlistList:
        logger.info("检测到 Ani2Alist 模块配置，正在添加至后台任务")
        add_scheduled_jobs(scheduler, settings.Ani2AlistList, "Ani2Alist", Ani2Alist)
    else:
        logger.warning("未检测到 Ani2Alist 模块配置")

    if settings.LibraryPosterList:
        logger.info("检测到 LibraryPoster 模块配置，正在添加至后台任务")
        add_scheduled_jobs(
            scheduler, settings.LibraryPosterList, "LibraryPoster", LibraryPoster
        )
    else:
        logger.warning("未检测到 LibraryPoster 模块配置")

    logging.getLogger("apscheduler.scheduler").addFilter(_MaxInstancesFilter())
    scheduler.start()
    logger.info("AutoFilm 启动完成")

    await asyncio.Event().wait()


if __name__ == "__main__":
    print_logo()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AutoFilm 程序退出！")
