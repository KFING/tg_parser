
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.channel import ChannelDbMdl
from src.dto.post import Post, Source, Channel


async def get_channels_by_source(db: AsyncSession, source: Source) -> list[ChannelDbMdl]:
    channels = await db.execute(select(ChannelDbMdl).where(ChannelDbMdl.source == source))
    return channels.scalars().all()

async def get_channel_by_id(db: AsyncSession, channel_id: int) -> ChannelDbMdl:
    channels = await db.execute(select(ChannelDbMdl).where(ChannelDbMdl.id == channel_id))
    return channels.scalars().first()

async def add_channel(db: AsyncSession, channel: Channel) -> ChannelDbMdl:
    channel = ChannelDbMdl(
        source = channel.source,
        channel_name = channel.channel_name,
        author = channel.author,
        created_channel_at = channel.created_channel_at,
        description = channel.description,
        link = channel.link,
    )
    db.add(channel)
    await db.commit()
    return channel



