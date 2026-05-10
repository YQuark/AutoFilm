import argparse
import asyncio
import logging
from datetime import datetime
from sys import path
from os.path import dirname

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


async def main() -> None:
    args = parse_args()

    # 手动模式：执行一次后退出
    if args.run or args.run_all:
        target = args.run
        for server in settings.AlistServerList:
            if args.run_all or server.get("id") == target:
                logger.info(f"手动执行 Alist2Strm 任务：{server['id']}")
                await Alist2Strm(**server).run()
        for server in settings.Ani2AlistList:
            if args.run_all or server.get("id") == target:
                logger.info(f"手动执行 Ani2Alist 任务：{server['id']}")
                await Ani2Alist(**server).run()
        for poster in settings.LibraryPosterList:
            if args.run_all or poster.get("id") == target:
                logger.info(f"手动执行 LibraryPoster 任务：{poster['id']}")
                await LibraryPoster(**poster).run()
        logger.info("手动执行完成")
        return

    # Cron 调度模式
    logger.info(f"AutoFilm {settings.APP_VERSION} 启动中...")
    logger.debug(f"是否开启 DEBUG 模式: {settings.DEBUG}")

    scheduler = AsyncIOScheduler()

    if settings.AlistServerList:
        logger.info("检测到 Alist2Strm 模块配置，正在添加至后台任务")
        for server in settings.AlistServerList:
            cron = server.get("cron")
            if cron:
                scheduler.add_job(
                    Alist2Strm(**server).run,
                    trigger=CronTrigger.from_crontab(cron),
                    next_run_time=datetime.now(),
                )
                logger.info(f"{server['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{server['id']} 未设置 cron")
    else:
        logger.warning("未检测到 Alist2Strm 模块配置")

    if settings.Ani2AlistList:
        logger.info("检测到 Ani2Alist 模块配置，正在添加至后台任务")
        for server in settings.Ani2AlistList:
            cron = server.get("cron")
            if cron:
                scheduler.add_job(
                    Ani2Alist(**server).run,
                    trigger=CronTrigger.from_crontab(cron),
                    next_run_time=datetime.now(),
                )
                logger.info(f"{server['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{server['id']} 未设置 cron")
    else:
        logger.warning("未检测到 Ani2Alist 模块配置")

    if settings.LibraryPosterList:
        logger.info("检测到 LibraryPoster 模块配置，正在添加至后台任务")
        for poster in settings.LibraryPosterList:
            cron = poster.get("cron")
            if cron:
                scheduler.add_job(
                    LibraryPoster(**poster).run,
                    trigger=CronTrigger.from_crontab(cron),
                    next_run_time=datetime.now(),
                )
                logger.info(f"{poster['id']} 已被添加至后台任务")
            else:
                logger.warning(f"{poster['id']} 未设置 cron")
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
