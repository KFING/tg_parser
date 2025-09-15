from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_main.models.channel import ChannelDbMdl
from src.dto.feed_rec_info import Channel, Source


async def get_channel_by_source_by_channel_name(db: AsyncSession, source: Source, channel_name: str) -> ChannelDbMdl:
    channels = await db.execute(select(ChannelDbMdl).where((ChannelDbMdl.source == source) and (ChannelDbMdl.channel_name == channel_name)))
    return channels.scalars().first()


async def get_channels_by_source(db: AsyncSession, source: Source) -> Sequence[ChannelDbMdl]:
    channels = await db.execute(select(ChannelDbMdl).where(ChannelDbMdl.source == source))
    return channels.scalars().all()


async def get_channel_by_id(db: AsyncSession, channel_db_id: str) -> ChannelDbMdl:
    channels = await db.execute(select(ChannelDbMdl).where(ChannelDbMdl.id == channel_db_id))
    return channels.scalars().first()


async def add_channel(db: AsyncSession, channel: Channel) -> ChannelDbMdl:
    channel = ChannelDbMdl(
        source=channel.source,
        channel_name=channel.channel_name,
        created_channel_at=channel.created_channel_at,
        description=channel.description,
        link=str(channel.link),
    )
    db.add(channel)
    await db.commit()
    return channel
