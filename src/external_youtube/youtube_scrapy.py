import logging
from collections.abc import AsyncIterator, Iterator
from datetime import datetime

from pydantic import HttpUrl
from pytubefix import Channel, YouTube
from redis.asyncio import Redis

from src.common.moment import as_utc
from src.dto import redis_models
from src.dto.feed_rec_info import (
    MediaFormat,
    RawPostMediaExt,
    Source,
)
from src.dto.post import Post
from src.errors import NotFoundChannelScrapperError, NotFoundPostScrapperError, fmt_err

logger = logging.getLogger(__name__)
rds = Redis(host="redis", port=6379)


class YouTubeNotFoundChannelScrapperError(NotFoundChannelScrapperError):
    src: Source = Source.YOUTUBE


class YouTubeNotFoundPostScrapperError(NotFoundPostScrapperError):
    src: Source = Source.YOUTUBE


def get_short_media_info(post: YouTube) -> list[RawPostMediaExt]:
    media: list[RawPostMediaExt] = []
    for quality in sorted((stream.resolution for stream in post.streams.filter(type="video")), key=lambda s: int(s.split("p")[0])):
        try:
            stream = post.streams.filter(res=quality).first()
            if stream is not None:
                media.append(
                    RawPostMediaExt(
                        preview=None,
                        url=HttpUrl(stream.url),  # pyright: ignore
                        format=MediaFormat.MP4,
                        quality_raw=quality,
                        downloaded_file=None,
                        captions=[],
                        timeline=[],
                    )
                )
            else:
                logger.debug(f"media with quality: {quality} :: {MediaFormat.MP4} has some problem")
        except Exception:
            logger.debug(f"media with quality: {quality} :: {MediaFormat.MP4} has some problem")
    for quality in sorted((stream.abr for stream in post.streams.filter(type="audio")), key=lambda s: int(s.split("kbps")[0])):
        try:
            stream = post.streams.filter(abr=quality).first()
            if stream is not None:
                media.append(
                    RawPostMediaExt(
                        preview=None,
                        url=HttpUrl(stream.url),  # pyright: ignore
                        format=MediaFormat.MP3,
                        quality_raw=quality,
                        downloaded_file=None,
                        captions=[],
                        timeline=[],
                    )
                )
            else:
                logger.debug(f"media with quality: {quality} :: {MediaFormat.MP3} has some problem")
        except Exception:
            logger.debug(f"media with quality: {quality} :: {MediaFormat.MP3} has some problem")
    return media


async def _get_posts_list(
    it: Iterator[tuple[int, YouTube]], channel_name: str, utc_dt_to: datetime, utc_dt_from: datetime, *, log_extra: dict[str, str]
) -> AsyncIterator[Post]:
    i = 0
    while True:
        try:
            i, post = next(it)
            if not post.publish_date:
                logger.warning(f"get_posts_list_channel({channel_name}) : publish date is not valid", extra=log_extra)
                continue
            utc_dt_from = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_from(Source.YOUTUBE, channel_name))))
            utc_dt_to = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_to(Source.YOUTUBE, channel_name))))
            utc_dt = as_utc(post.publish_date)
            if utc_dt_to >= utc_dt:
                logger.debug(
                    f"get_posts_list_channel({channel_name}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_to({utc_dt_to})", extra=log_extra
                )
                continue
            if utc_dt > utc_dt_from:
                logger.debug(
                    f"get_posts_list_channel({channel_name}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_from({utc_dt_from})", extra=log_extra
                )
                break
            media = get_short_media_info(post)
            yield Post(
                channel_name=channel_name,
                post_id=post.video_id,
                content=post.title,
                pb_date=utc_dt,
                link=HttpUrl(f"http://youtube.com/watch?v={post.video_id}"),  # pyright: ignore
                media=[x for x in media if x is not None],  # TODO: add list of all media available for short view
            )
            logger.debug(f"get_posts_list({channel_name}) : progress {i:0>4} : {post.video_id}", extra=log_extra)
        except StopIteration:
            break
        except Exception as e:
            logger.error(f"wrong youtube content {fmt_err(e)}", extra=log_extra, exc_info=e)
            continue
    logger.info(f"get_posts_list_channel found {i + 1} posts", extra=log_extra)


async def get_channel_posts_list(channel_name: str, *, log_extra: dict[str, str]) -> AsyncIterator[Post]:
    try:
        utc_dt_from = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_from(Source.YOUTUBE, channel_name))))
        utc_dt_to = as_utc(datetime.fromisoformat(await rds.get(redis_models.source_channel_name_dt_to(Source.YOUTUBE, channel_name))))
        logger.debug(f"get_channel_posts_list({channel_name}) -> start {utc_dt_from}...{utc_dt_to}", extra=log_extra)
        channel = Channel(f"https://www.youtube.com/@{channel_name}")
    except Exception as e:
        logger.warning(f"has problem with youtube channel :: {channel_name}, error :: {fmt_err(e)}", extra=log_extra, exc_info=e)
        raise YouTubeNotFoundChannelScrapperError(channel_name) from e
    return _get_posts_list(enumerate(channel.videos), channel_name, utc_dt_from, utc_dt_to, log_extra=log_extra)
