from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.tg_post import TgPostDbMdl
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

async def create_tg_posts(db: AsyncSession, tg_posts: list[TgPost]) -> list[TgPost]:
    db_id_posts = await db.execute(select(TgPostDbMdl.post_id))
    id_posts = db_id_posts.scalars().all()
    new_posts: list[TgPost] = []
    for tg_post in tg_posts:
        if tg_post.tg_post_id not in id_posts:
            new_posts.append(tg_post)
    posts: list[TgPost] = []
    for tg_post in tg_posts:
        posts.append(tg_post)

    await db.commit()
    return posts
