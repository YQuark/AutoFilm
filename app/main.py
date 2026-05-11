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
from app.modules import Alist2Strm, Ani2Alist
from app.utils.notify import send_notification


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
    await send_notification(
        f"{module_name} 任务开始", f"任务 [{task_id}] 开始执行"
    )
    try:
        await task.run()
        await send_notification(
            f"{module_name} 任务完成", f"任务 [{task_id}] 执行成功", "success"
        )
    except Exception as e:
        logger.error(f"{module_name} 任务 {task_id} 执行失败：{e}")
        logger.debug(traceback.format_exc())
        await send_notification(
            f"{module_name} 任务失败",
            f"任务 [{task_id}] 执行失败：{e}",
            "error",
        )


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
                id=task_id,
                next_run_time=datetime.now(),
            )
        except Exception as e:
            logger.error(f"{module_name} 任务 {task_id} 添加失败：{e}")
            logger.debug(traceback.format_exc())
            continue

        logger.info(f"{task_id} 已被添加至后台任务")


def _reconcile_module(
    scheduler: AsyncIOScheduler,
    module_name: str,
    task_cls: type,
    old_configs: list[dict[str, Any]],
    new_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """根据新旧配置差异，增删改 scheduler 中的 job。返回新的配置快照。"""
    old_by_id: dict[str, dict[str, Any]] = {get_task_id(c): c for c in old_configs}
    new_by_id: dict[str, dict[str, Any]] = {get_task_id(c): c for c in new_configs}

    for task_id in set(old_by_id) - set(new_by_id):
        try:
            scheduler.remove_job(task_id)
            logger.info(f"[热重载] 移除任务: {task_id}")
        except Exception as e:
            logger.warning(f"[热重载] 移除任务 {task_id} 失败: {e}")

    for task_id, new_config in new_by_id.items():
        old_config = old_by_id.get(task_id)
        if old_config is not None and old_config == new_config:
            continue

        if old_config is not None:
            try:
                scheduler.remove_job(task_id)
            except Exception:
                pass

        cron = new_config.get("cron")
        if not cron:
            logger.warning(f"[热重载] 任务 {task_id} 未设置 cron，跳过")
            continue

        try:
            task = task_cls(**new_config)
            scheduler.add_job(
                run_module_task,
                args=[module_name, task_id, task],
                trigger=CronTrigger.from_crontab(cron),
                id=task_id,
                next_run_time=datetime.now(),
            )
            logger.info(f"[热重载] 任务已更新: {task_id}")
        except Exception as e:
            logger.error(f"[热重载] 添加任务 {task_id} 失败: {e}")
            logger.debug(traceback.format_exc())

    return list(new_configs.values())


async def _hot_reload_watcher(
    scheduler: AsyncIOScheduler,
    alist_configs: list[dict[str, Any]],
    ani_configs: list[dict[str, Any]],
    interval: int,
) -> None:
    """后台协程：监控 config.yaml 文件变更并重建 scheduler job"""
    try:
        last_mtime = settings.CONFIG.stat().st_mtime
    except OSError:
        logger.warning("[热重载] 无法读取配置文件状态，热重载已禁用")
        return

    while True:
        await asyncio.sleep(interval)
        try:
            current_mtime = settings.CONFIG.stat().st_mtime
        except OSError:
            continue

        if current_mtime <= last_mtime:
            continue

        logger.info("[热重载] 检测到配置文件变更，正在重载任务...")
        last_mtime = current_mtime

        try:
            new_alist = settings.AlistServerList
            new_ani = settings.Ani2AlistList

            alist_configs[:] = _reconcile_module(
                scheduler, "Alist2Strm", Alist2Strm, alist_configs, new_alist
            )
            ani_configs[:] = _reconcile_module(
                scheduler, "Ani2Alist", Ani2Alist, ani_configs, new_ani
            )
        except Exception as e:
            logger.error(f"[热重载] 重载失败: {e}")
            logger.debug(traceback.format_exc())


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
        if args.run and not matched:
            logger.warning(f"未找到 ID 为 {target} 的任务")
        logger.info("手动执行完成")
        return

    # Cron 调度模式
    logger.info(f"AutoFilm {settings.APP_VERSION} 启动中...")
    logger.debug(f"是否开启 DEBUG 模式: {settings.DEBUG}")

    scheduler = AsyncIOScheduler()

    alist_configs: list[dict[str, Any]] = list(settings.AlistServerList)
    ani_configs: list[dict[str, Any]] = list(settings.Ani2AlistList)

    if alist_configs:
        logger.info("检测到 Alist2Strm 模块配置，正在添加至后台任务")
        add_scheduled_jobs(scheduler, alist_configs, "Alist2Strm", Alist2Strm)
    else:
        logger.warning("未检测到 Alist2Strm 模块配置")

    if ani_configs:
        logger.info("检测到 Ani2Alist 模块配置，正在添加至后台任务")
        add_scheduled_jobs(scheduler, ani_configs, "Ani2Alist", Ani2Alist)
    else:
        logger.warning("未检测到 Ani2Alist 模块配置")

    logging.getLogger("apscheduler.scheduler").addFilter(_MaxInstancesFilter())
    scheduler.start()
    logger.info("AutoFilm 启动完成")

    if settings.HotReloadEnabled:
        logger.info(f"配置文件热重载已启用，检查间隔: {settings.HotReloadInterval}s")
        asyncio.create_task(
            _hot_reload_watcher(
                scheduler,
                alist_configs,
                ani_configs,
                settings.HotReloadInterval,
            )
        )
    else:
        logger.info("配置文件热重载已禁用")

    await asyncio.Event().wait()


if __name__ == "__main__":
    print_logo()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AutoFilm 程序退出！")
