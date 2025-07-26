import asyncio
import logging
from datetime import datetime

from redis import Redis

from src.app_api.dependencies import get_db_main_manager
from src.app_celery.main import app
from celery.result import AsyncResult
from src.app_celery.tasks import parse_api
from src.dto.redis_task import RedisTask, Task

rds = Redis()
rds.set(str(RedisTask.counter_of_workers.value), 3)

running_tasks = {}
running_channels = {}

logger = logging.getLogger(__name__)


class InvalidTelegramTask(Exception):
    pass


def serialize_channel_task(task_name: str) -> Task | None:
    try:
        tsk = rds.lrange(task_name, 0, 1)
        if len(tsk) < 2:
            return None
        source, channel_name = task_name.split('$', maxsplit=1)
        tg_task = Task(
            source=source,
            channel_name=channel_name,
            dt_from=datetime.fromisoformat(tsk[0].decode("utf-8")),
            dt_to=datetime.fromisoformat(tsk[1].decode("utf-8")),
        )
        rds.lrem(task_name, 1, tsk[1])
        rds.lrem(task_name, 1, tsk[0])
        return tg_task
    except InvalidTelegramTask:
        logger.warning('Invalid Task parameters')


def running_new_task_worker(tsk: Task):

    global running_tasks
    global running_channels

    result = parse_api.delay(tsk.channel_name, tsk.model_dump_json(indent=4))
    running_tasks[result.id] = result
    running_channels[result.id] = tsk.channel_name

    return result


@app.task
def manager_task():
    global running_tasks
    global running_channels

    cow_redis = rds.get(str(RedisTask.counter_of_workers.value))
    if isinstance(cow_redis.decode("utf-8"), str):
        cow = int(cow_redis.decode("utf-8"))
    else:
        cow = 3
    byte_tasks = rds.smembers(str(RedisTask.channel_tasks.value))
    if not byte_tasks:
        return
    tasks = [task.decode("utf-8") for task in byte_tasks]
    logger.debug(f"[{datetime.now()}] Manager is running")

    finished = [tid for tid, r in running_tasks.items() if AsyncResult(tid).ready()]

    for tid in finished:
        logger.debug(f"task finished {tid}")
        running_tasks.pop(tid)
        channel_name = running_channels.pop(tid)
        tsk = serialize_channel_task(channel_name)
        if not tsk:
            continue
        result = running_new_task_worker(tsk)
        logger.debug(f"Running new task: {result.id} :: {channel_name}")

    for i in range(cow - len(running_tasks.items())):
        for item in running_channels.items():
            if not str(item) in tasks:
                continue
            tasks.remove(str(item))
        if not tasks:
            return
        task = tasks.pop()
        tsk = serialize_channel_task(task)
        if not tsk:
            continue
        result = running_new_task_worker(tsk)
        logger.debug(f"Running new task: {result.id} :: {task}")

