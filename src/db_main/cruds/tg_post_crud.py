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
    post = TgPostDbMdl(
        post_id=tg_post.tg_post_id,
        tg_channel_id=tg_post.tg_channel_id,
        tg_pb_date=tg_post.tg_pb_date,
        content=tg_post.content,
        link=str(tg_post.link),
    )
    db.add(post)
    await db.commit()
    return post

async def create_tg_posts(db: AsyncSession, tg_posts: list[TgPostDbMdl]) -> list[TgPostDbMdl]:
    posts: list[TgPostDbMdl] = []
    for tg_post in tg_posts:
        posts.append(tg_post)
        db.add(tg_post)
    await db.commit()
    return posts

async def get_all_id_posts(db: AsyncSession) -> Sequence[int]:
    invoices = await db.execute(select(TgPostDbMdl.post_id))
    return invoices.scalars().all()
