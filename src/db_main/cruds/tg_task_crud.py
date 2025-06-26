import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import null, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.tg_task import TgTaskDbMdl
from src.dto.currency import Currency
from src.dto.tg_post import TgPost


async def create_tg_task(db: AsyncSession, tg_task: TgPost) -> TgTaskDbMdl:
    tg_post = TgTaskDbMdl(
        channel_id=tg_task.channel_id,
        status=tg_task.status,
        task=tg_task.task,
    )
    db.add(tg_post)
    await db.commit()
    return tg_post


async def get_task_db(db: AsyncSession, channel_id: str, tg_post_id: int) -> TgTaskDbMdl:
    """invoices = await db.execute(
        select(TgTaskDbMdl).where(
            (TgTaskDbMdl.channel_name == tg_channel_id)
            and (TgTaskDbMdl.post_id == tg_post_id)
        )
    )
    return invoices.scalars().first()"""
    pass
