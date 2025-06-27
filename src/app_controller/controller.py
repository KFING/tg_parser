import logging
from datetime import datetime

from redis.asyncio import Redis

from src.app_api.dependencies import DBM
from src.db_main.cruds import tg_task_crud
from src.dto.redis_models import RedisChannels

from src.dto.tg_task import TgTask, TgTaskStatus, TgTaskEnum
from src.env import settings

rds = Redis()
pubsub = rds.pubsub()


logger = logging.getLogger(__name__)


async def parser_message(message: str) -> tuple[str, datetime, datetime]:
    channel_name, dt_to, dt_from = message.split("$", 2)
    return channel_name, datetime.fromisoformat(dt_to), datetime.fromisoformat(dt_from)


async def main(dbm: DBM, log_extra: dict[str, str]) -> None:

    await pubsub.subscribe(RedisChannels.TG_TASKS.value)

    async with dbm.session() as session:
        while True:
            message = await pubsub.get_message(timeout=10)
            logger.info(
                f" ANSWER EVENT :: GET redis_event_answer -> get message: {type(message['data'])}",
                extra=log_extra,
            )
            if isinstance(message["data"], bytes):
                try:
                    channel_name, dt_to, dt_from = await parser_message(message["data"].decode())
                    logger.info(
                        f" CONTROLLER :: main -> add task to db -- id: {channel_name} -- {datetime.now()}",
                        extra=log_extra,
                    )

                    await tg_task_crud.create_tg_task(session, TgTask(channel_name=channel_name, dt_to=dt_to, dt_from=dt_from, status=TgTaskStatus.free, task=TgTaskEnum.parse))

                    await rds.set(channel_name, TgTaskStatus.free.value)

                except Exception as e:
                    logger.warning(f" ANSWER EVENT :: redis_event_answer -> something wrong -- {datetime.now()} -- warning -- {e}", extra=log_extra)
            else:
                tg_task = await tg_task_crud.get_task_by_status(session, TgTaskStatus.free)
                channel_status = await rds.get(tg_task.channel_name)
                if channel_status == TgTaskStatus.free.value:
                    # стучим по апи парсер и меняем всякую херь
                    await tg_task_crud.update_task_status(session, tg_task, TgTaskStatus.processing)


