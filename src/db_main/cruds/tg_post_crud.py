from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.tg_post import TgPostDbMdl
from src.dto.post import Post


async def create_tg_post(db: AsyncSession, tg_post: Post) -> TgPostDbMdl:
    post = TgPostDbMdl(
        post_id=tg_post.post_id,
        tg_channel_id=tg_post.channel_name,
        tg_pb_date=tg_post.tg_pb_date,
        content=tg_post.content,
        link=str(tg_post.link),
    )
    db.add(post)
    await db.commit()
    return post

async def create_tg_posts(db: AsyncSession, tg_posts: list[Post]) -> list[Post]:
    db_id_posts = await db.execute(select(TgPostDbMdl.post_id))
    id_posts = db_id_posts.scalars().all()
    new_posts: list[Post] = []
    for tg_post in tg_posts:
        if tg_post.post_id not in id_posts:
            new_posts.append(tg_post)
    posts: list[Post] = []
    for tg_post in tg_posts:
        posts.append(tg_post)

    await db.commit()
    return posts
