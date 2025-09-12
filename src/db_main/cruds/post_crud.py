from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.cruds import channel_crud
from src.db_main.models.post import PostDbMdl
from src.dto.feed_rec_info import Post


async def get_posts_by_channel_id(db: AsyncSession, channel_id: str) -> Sequence[PostDbMdl]:
    posts = await db.execute(select(PostDbMdl).where(PostDbMdl.channel_id == channel_id))
    return posts.scalars().all()

async def get_post_by_id(db: AsyncSession, post_id: int) -> PostDbMdl:
    post = await db.execute(select(PostDbMdl).where(PostDbMdl.id == post_id))
    return post.scalars().first()

async def add_post(db: AsyncSession, post: Post) -> PostDbMdl:
    post = PostDbMdl(
        post_id=post.post_id,
        channel_id=post.channel_name,
        pb_date=post.pb_date,
        link=str(post.link),
    )
    db.add(post)
    await db.commit()
    return post

async def create_posts(db: AsyncSession, posts: list[Post]) -> list[PostDbMdl]:
    old_posts = await get_posts_by_channel_id(db, posts[-1].channel_name)
    channel = await channel_crud.get_channel_by_source_by_channel_name(db, posts[-1].source, posts[-1].channel_name)
    unique_posts: list[PostDbMdl] = []
    for post in posts:
        if post.post_id not in [old_post.id for old_post in old_posts]:
            unique_posts.append(PostDbMdl(post_id=post.post_id,
                             channel_id=channel.id,
                             pb_date=post.pb_date,
                             link=str(post.link), ))
            db.add(unique_posts[-1])
    await db.commit()
    return unique_posts


