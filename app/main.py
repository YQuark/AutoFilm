import argparse
import asyncio
import logging
import signal
import traceback
from datetime import datetime
from sys import path
from os.path import dirname
from typing import Any

path.append(dirname(dirname(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type:ignore
from apscheduler.triggers.cron import CronTrigger  # type:ignore

from app.core import settings, logger
from app.core.state import TaskStateStore
from app.core.tasks import (
    TaskAlreadyRunningError,
    TaskDefinition,
    TaskRegistry,
    get_task_id,
)
from app.extensions import LOGO
from app.modules import Alist2Strm


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


async def run_module_task(registry: TaskRegistry, definition: TaskDefinition) -> None:
    try:
        await registry.run(definition)
    except TaskAlreadyRunningError as e:
        logger.warning(str(e))
    except Exception as e:
        logger.error(f"{definition.key} 任务执行异常：{e}")
        logger.debug(traceback.format_exc())


async def run_config_task(
    registry: TaskRegistry, module_name: str, config: dict[str, Any], task_cls: type
) -> None:
    task_id = get_task_id(config)
    registry.replace_module(module_name, task_cls, [config])
    definition = registry.get(module_name, task_id)
    if definition is not None:
        await run_module_task(registry, definition)


def add_scheduled_jobs(
    scheduler: AsyncIOScheduler,
    registry: TaskRegistry,
    definitions: list[TaskDefinition],
) -> None:
    for definition in definitions:
        cron = definition.config.get("cron")
        if not cron:
            logger.warning(f"{definition.key} 未设置 cron")
            continue

        try:
            scheduler.add_job(
                run_module_task,
                args=[registry, definition],
                trigger=CronTrigger.from_crontab(cron),
                id=definition.key,
                next_run_time=datetime.now(),
            )
        except Exception as e:
            logger.error(f"{definition.key} 添加失败：{e}")
            logger.debug(traceback.format_exc())
            continue

        logger.info(f"{definition.key} 已被添加至后台任务")


def _reconcile_module(
    scheduler: AsyncIOScheduler,
    registry: TaskRegistry,
    module_name: str,
    task_cls: type,
    old_configs: list[dict[str, Any]],
    new_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """根据新旧配置差异，增删改 scheduler 中的 job。返回新的配置快照。"""
    old_by_id: dict[str, dict[str, Any]] = {get_task_id(c): c for c in old_configs}
    new_by_id: dict[str, dict[str, Any]] = {get_task_id(c): c for c in new_configs}

    for task_id in set(old_by_id) - set(new_by_id):
        job_id = f"{module_name}:{task_id}"
        try:
            scheduler.remove_job(job_id)
            logger.info(f"[热重载] 移除任务: {job_id}")
        except Exception as e:
            logger.warning(f"[热重载] 移除任务 {job_id} 失败: {e}")

    definitions = {
        definition.task_id: definition
        for definition in registry.replace_module(module_name, task_cls, new_configs)
    }

    for task_id, new_config in new_by_id.items():
        job_id = f"{module_name}:{task_id}"
        old_config = old_by_id.get(task_id)
        if old_config is not None and old_config == new_config:
            continue

        if old_config is not None:
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass

        cron = new_config.get("cron")
        if not cron:
            logger.warning(f"[热重载] 任务 {job_id} 未设置 cron，跳过")
            continue

        try:
            definition = definitions[task_id]
            scheduler.add_job(
                run_module_task,
                args=[registry, definition],
                trigger=CronTrigger.from_crontab(cron),
                id=definition.key,
                next_run_time=datetime.now(),
            )
            logger.info(f"[热重载] 任务已更新: {definition.key}")
        except Exception as e:
            logger.error(f"[热重载] 添加任务 {job_id} 失败: {e}")
            logger.debug(traceback.format_exc())

    return list(new_configs.values())


async def _hot_reload_watcher(
    scheduler: AsyncIOScheduler,
    registry: TaskRegistry,
    alist_configs: list[dict[str, Any]],
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

            alist_configs[:] = _reconcile_module(
                scheduler, registry, "Alist2Strm", Alist2Strm, alist_configs, new_alist
            )
        except Exception as e:
            logger.error(f"[热重载] 重载失败: {e}")
            logger.debug(traceback.format_exc())


async def _start_web_server(registry: TaskRegistry, scheduler: AsyncIOScheduler) -> None:
    import uvicorn

    from app.web.server import create_app

    config = uvicorn.Config(
        create_app(registry, scheduler),
        host=settings.WebHost,
        port=settings.WebPort,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    logger.info(f"Web 服务已启用：http://{settings.WebHost}:{settings.WebPort}")
    await server.serve()


async def main() -> None:
    args = parse_args()
    state_store = TaskStateStore(settings.STATE_DIR)
    registry = TaskRegistry(state_store)

    # 手动模式：执行一次后退出
    if args.run or args.run_all:
        target = args.run
        matched = False
        for server in settings.AlistServerList:
            if args.run_all or server.get("id") == target:
                matched = True
                task_id = get_task_id(server)
                logger.info(f"手动执行 Alist2Strm 任务：{task_id}")
                await run_config_task(registry, "Alist2Strm", server, Alist2Strm)
        if args.run and not matched:
            logger.warning(f"未找到 ID 为 {target} 的任务")
        logger.info("手动执行完成")
        return

    # Cron 调度模式
    logger.info(f"AutoFilm {settings.APP_VERSION} 启动中...")
    logger.debug(f"是否开启 DEBUG 模式: {settings.DEBUG}")

    # 设置优雅关闭
    shutdown_event = asyncio.Event()
    background_tasks: list[asyncio.Task] = []

    def _signal_handler() -> None:
        if not shutdown_event.is_set():
            logger.info("收到终止信号，正在优雅关闭...")
            shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler，回退到 signal.signal
            signal.signal(sig, lambda signum, frame: _signal_handler())

    scheduler = AsyncIOScheduler()

    alist_configs: list[dict[str, Any]] = list(settings.AlistServerList)

    if alist_configs:
        logger.info("检测到 Alist2Strm 模块配置，正在添加至后台任务")
        definitions = registry.replace_module("Alist2Strm", Alist2Strm, alist_configs)
        add_scheduled_jobs(scheduler, registry, definitions)
    else:
        logger.warning("未检测到 Alist2Strm 模块配置")

    logging.getLogger("apscheduler.scheduler").addFilter(_MaxInstancesFilter())
    scheduler.start()
    logger.info("AutoFilm 启动完成")

    if settings.HotReloadEnabled:
        logger.info(f"配置文件热重载已启用，检查间隔: {settings.HotReloadInterval}s")
        background_tasks.append(
            asyncio.create_task(
                _hot_reload_watcher(
                    scheduler,
                    registry,
                    alist_configs,
                    settings.HotReloadInterval,
                )
            )
        )
    else:
        logger.info("配置文件热重载已禁用")

    if settings.WebEnabled:
        background_tasks.append(asyncio.create_task(_start_web_server(registry, scheduler)))
    else:
        logger.info("Web 服务已禁用")

    # 等待关闭信号
    await shutdown_event.wait()

    # 优雅关闭流程
    logger.info("正在优雅关闭 AutoFilm...")

    # 1. 关闭 APScheduler
    try:
        scheduler.shutdown(wait=False)
        logger.debug("APScheduler 已关闭")
    except Exception:
        pass

    # 2. 取消所有后台任务
    for task in background_tasks:
        task.cancel()
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)

    logger.info("AutoFilm 已关闭")


if __name__ == "__main__":
    print_logo()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AutoFilm 程序退出！")
