import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import null, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.tg_post import TgPostDbMdl
from src.dto.currency import Currency
from src.dto.tg_post import TgPost


async def create_tg_post(db: AsyncSession, tg_post: TgPost) -> TgPostDbMdl:
    tg_post = TgPostDbMdl(
        post_id=tg_post.tg_post_id,
        tg_channel_id=tg_post.tg_channel_id,
        tg_pb_date=tg_post.tg_pb_date,
        content=tg_post.content,
        link=str(tg_post.link),
    )
    db.add(tg_post)
    await db.commit()
    return tg_post


async def get_post_by_channel_id_and_post_id(db: AsyncSession, tg_channel_id: str, tg_post_id: int) -> TgPostDbMdl:
    invoices = await db.execute(
        select(TgPostDbMdl).where(
            (TgPostDbMdl.tg_channel_id == tg_channel_id)
            and (TgPostDbMdl.post_id == tg_post_id)
        )
    )
    return invoices.scalars().first()
