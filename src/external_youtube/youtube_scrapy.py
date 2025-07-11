import asyncio
import logging
from asyncio import Task
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta
from datetime import time as dt_time
from pathlib import Path
from typing import cast

import aiohttp
from pydantic import HttpUrl
from pytubefix import Channel, Playlist, Stream, YouTube

from src.common.async_utils import sync_to_async
from src.common.moment import as_utc, utcnow
from src.dto.download_post_recipe import DownloadPostContentRecipe, DownloadQuality
from src.dto.feed_rec_info import (
    FeedRecPostCaption,
    FeedRecPostContent,
    FeedRecPostFull,
    FeedRecPostShort,
    FeedRecPostTimeLine,
    Lang,
    MediaFormat,
    RawPostMedia,
    RawPostMediaExt,
    Source,
)
from src.env import SCRAPPER_RESULTS_DIR__YOUTUBE, SCRAPPER_TMP_MEDIA_DIR
from src.errors import NotFoundChannelScrapperError, NotFoundPostScrapperError, fmt_err

logger = logging.getLogger(__name__)


class YouTubeNotFoundChannelScrapperError(NotFoundChannelScrapperError):
    src: Source = Source.YOUTUBE


class YouTubeNotFoundPostScrapperError(NotFoundPostScrapperError):
    src: Source = Source.YOUTUBE


def get_captions(post: YouTube, lang: Lang, *, log_extra: dict[str, str]) -> list[FeedRecPostCaption]:
    try:
        try:
            capt = post.captions[lang.value]
        except Exception:
            logger.debug(f"download_post({post.video_id}) -> no captions(lang={lang.value}) found", extra=log_extra)
            try:
                capt = post.captions[f"a.{lang.value}"]
            except Exception:
                logger.debug(f"download_post({post.video_id}) -> no auto_captions(lang={lang.value}) found", extra=log_extra)
                return []
        results = []
        cur_time = None
        cur_txt = None
        for i, ln in enumerate(str(capt.generate_srt_captions()).splitlines()):
            if (i + 1) % 4 == 3:
                cur_txt = ln
            elif (i + 1) % 4 == 2:
                t = dt_time.fromisoformat(ln.split(" ")[0])
                cur_time = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
            elif (i + 1) % 4 == 0:
                if cur_txt is not None and cur_time is not None:
                    results.append((cur_time, cur_txt))
                cur_txt = None
                cur_time = None
        if cur_txt is not None and cur_time is not None:
            results.append((cur_time, cur_txt))
        return [FeedRecPostCaption(lang=lang, raw=str(capt), parsed=results)]
    except Exception as e:
        logger.exception(e, exc_info=True, extra=log_extra)
        return []


def get_timeline(post: YouTube, lang: Lang) -> list[FeedRecPostTimeLine]:
    return [FeedRecPostTimeLine(lang=lang, raw=str(post.chapters), parsed=[(timedelta(seconds=ch.start_seconds), ch.title) for ch in post.chapters])]


@sync_to_async
def download_media_content(
    post: YouTube,
    channel_id: str,
    post_id: str,
    stream: Stream,
    quality: DownloadQuality,
    captions_recipe: bool,
    title_recipe: bool,
    lang: Lang,
    mf: MediaFormat,
    *,
    preview: RawPostMedia | None = None,
    log_extra: dict[str, str],
) -> RawPostMediaExt | None:
    logger.info(f"Downloading media content for {mf.name} -> start", extra=log_extra)
    new_file = SCRAPPER_RESULTS_DIR__YOUTUBE / channel_id / post_id / f"{post_id}.{quality.value}.{mf.value}"
    captions = []
    timelines = []
    if captions_recipe:
        captions = get_captions(post, lang, log_extra=log_extra)
    if title_recipe:
        timelines = get_timeline(post, lang)
    proto = RawPostMediaExt(
        preview=preview,
        url=HttpUrl(stream.url),  # pyright: ignore
        format=mf,
        quality_raw=stream.resolution if mf == MediaFormat.MP4 else stream.abr,
        downloaded_file=None,
        captions=captions,
        timeline=timelines,
    )
    if new_file.exists():
        proto.downloaded_file = new_file
        return proto

    path = None
    try:
        fpref = utcnow().strftime("tmp_%Y%m%d%H%M%S_")
        if downloaded_file := stream.download(output_path=str(SCRAPPER_TMP_MEDIA_DIR), mp3=mf == MediaFormat.MP3, filename_prefix=fpref, skip_existing=True):
            path = Path(downloaded_file)
        else:
            return proto
    except Exception as e:
        logger.warning(f"Downloading media content for {mf.name} -> failed : {fmt_err(e)}", exc_info=e, extra=log_extra)
        return proto

    assert path is not None  # only for mypy

    new_file.parent.mkdir(exist_ok=True, parents=True)
    if not new_file.exists():
        path.rename(new_file)
    else:
        path.unlink()

    proto.downloaded_file = new_file

    logger.info(f"Downloading media content for {mf.name} -> finish", extra=log_extra)
    return proto


async def download_preview_media_requests(channel_id: str, post_id: str, url: str, mf: MediaFormat, *, log_extra: dict[str, str]) -> RawPostMedia | None:
    logger.info(f"Downloading media content with requests for {mf.name} -> start", extra=log_extra)
    new_file = SCRAPPER_RESULTS_DIR__YOUTUBE / channel_id / post_id / f"preview.{mf.value}"

    proto = RawPostMedia(
        url=HttpUrl(url),  # pyright: ignore
        # error: "Annotated" cannot be instantiated (reportCallIssue)
        format=mf,
        downloaded_file=None,
    )
    if new_file.exists():
        proto.downloaded_file = new_file
        return proto

    path = None
    try:
        save_path = SCRAPPER_TMP_MEDIA_DIR / f"preview.{mf.value}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    Path(save_path).write_bytes(content)
                if save_path:
                    path = Path(save_path)
                else:
                    return proto
    except Exception as e:
        logger.warning(f"Downloading media content for {mf.name} -> failed : {fmt_err(e)}", exc_info=e, extra=log_extra)
        return proto

    assert path is not None  # only for mypy

    new_file.parent.mkdir(exist_ok=True, parents=True)
    if not new_file.exists():
        path.rename(new_file)
    else:
        path.unlink()

    proto.downloaded_file = new_file

    logger.info(f"Downloading media content for {mf.name} -> finish", extra=log_extra)
    return proto


def get_audio_link(post: YouTube, quality: DownloadQuality, *, log_extra: dict[str, str]) -> Stream | None:
    logger.debug(f"get_audio_link({post.video_id})", extra=log_extra)
    try:
        qualities = sorted((stream.abr for stream in post.streams.filter(type="audio")), key=lambda s: int(s.split("kbps")[0]))
        match quality:
            case quality.LOW:
                index = 0
            case quality.MEDIUM:
                index = len(qualities) // 2
            case quality.BEST:
                index = -1
            case _:
                raise NotImplementedError
        return post.streams.filter(abr=qualities[index]).first()
    except Exception as e:
        logger.warning(f"has problem with audio content on post :: {post.video_id}", e, extra=log_extra)
        return None


def get_video_link(post: YouTube, quality: DownloadQuality, *, log_extra: dict[str, str]) -> Stream | None:
    logger.debug(f"get_video_link({post.video_id})", extra=log_extra)
    try:
        qualities = sorted((stream.resolution for stream in post.streams.filter(type="video")), key=lambda s: int(s.split("p")[0]))
        match quality:
            case quality.LOW:
                index = 0
            case quality.MEDIUM:
                index = len(qualities) // 2
            case quality.BEST:
                index = -1
            case _:
                raise NotImplementedError
        return post.streams.filter(res=qualities[index]).first()
    except Exception as e:
        logger.warning(f"has problem with video content on post :: {post.video_id}", e, extra=log_extra)
        return None


def get_preview_image_link(post: YouTube) -> str:
    return cast(str, post.thumbnail_url)


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


def get_contents(post: YouTube, lang: Lang) -> list[FeedRecPostContent]:
    return [FeedRecPostContent(lang=lang, content=cast(str, post.description))]


async def download_post(post_id: str, recipe: DownloadPostContentRecipe, *, log_extra: dict[str, str]) -> FeedRecPostFull | None:
    logger.debug(f"download_post({post_id}) -> start", extra=log_extra)
    try:
        post = YouTube(f"http://youtube.com/watch?v={post_id}&hl={recipe.lang.value}")  # TODO: add geo link and cookies
    except Exception as e:
        logger.error(f"download_post({post_id}) -> has problem with youtube post :: {post_id}", e, extra=log_extra)
        raise YouTubeNotFoundPostScrapperError(post_id) from e

    media_download_tasks: list[Task[RawPostMediaExt | None]] = []
    channel_id = str(post.channel_id)

    # TODO: download all media --No with pytube
    if recipe.download_audio_quality is not None:
        audio_link = get_audio_link(post, recipe.download_audio_quality, log_extra=log_extra)
        if audio_link is not None:
            logger.debug(f"download_post({post_id}) -> get_audio_link :: {audio_link.url}", extra=log_extra)
            media_download_tasks.append(
                asyncio.create_task(
                    download_media_content(
                        post,
                        channel_id,
                        post_id,
                        audio_link,
                        recipe.download_audio_quality,
                        recipe.captions,
                        recipe.timeline,
                        recipe.lang,
                        MediaFormat.MP3,
                        log_extra=log_extra,
                    )
                )
            )

    if recipe.download_video_quality is not None:
        video_link = get_video_link(post, recipe.download_video_quality, log_extra=log_extra)
        if video_link is not None:
            logger.debug(f"download_post({post_id}) -> get_video_link :: {video_link.url}", extra=log_extra)

            logger.debug(f"download_post({post_id}) -> downloaded preview image -> start", extra=log_extra)
            preview: RawPostMedia | None = None
            if recipe.download_preview_image:
                preview = await download_preview_media_requests(channel_id, post_id, post.thumbnail_url, MediaFormat.JPG, log_extra=log_extra)
            logger.debug(f"download_post({post_id}) -> downloaded preview image -> finish", extra=log_extra)

            media_download_tasks.append(
                asyncio.create_task(
                    download_media_content(
                        post,
                        channel_id,
                        post_id,
                        video_link,
                        recipe.download_video_quality,
                        recipe.captions,
                        recipe.timeline,
                        recipe.lang,
                        MediaFormat.MP4,
                        preview=preview,
                        log_extra=log_extra,
                    )
                )
            )
    media: list[RawPostMediaExt | None] = await asyncio.gather(*media_download_tasks)
    logger.info(f"download_post({post_id}) -> finish", extra=log_extra)
    return FeedRecPostFull(
        src=Source.YOUTUBE,
        channel_id=post.channel_id,
        post_id=post_id,
        url=HttpUrl(f"http://youtube.com/watch?v={post_id}"),  # pyright: ignore
        title=cast(str, post.title),
        posted_at=cast(datetime, post.publish_date),
        contents=get_contents(post, recipe.lang),
        media=[x for x in media if x is not None],
    )


async def _get_posts_list(
    it: Iterator[tuple[int, YouTube]], channel_id: str, utc_dt_to: datetime, utc_dt_from: datetime, *, log_extra: dict[str, str]
) -> AsyncIterator[FeedRecPostShort]:
    i = 0
    while True:
        try:
            i, post = next(it)
            if not post.publish_date:
                logger.warning(f"get_posts_list_channel({channel_id}) : publish date is not valid", extra=log_extra)
                continue
            utc_dt = as_utc(post.publish_date)
            if utc_dt_to >= utc_dt:
                logger.debug(
                    f"get_posts_list_channel({channel_id}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_to({utc_dt_to})", extra=log_extra
                )
                continue
            if utc_dt > utc_dt_from:
                logger.debug(
                    f"get_posts_list_channel({channel_id}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_from({utc_dt_from})", extra=log_extra
                )
                break
            media = get_short_media_info(post)
            yield FeedRecPostShort(
                src=Source.YOUTUBE,
                channel_id=channel_id,
                post_id=post.video_id,
                url=HttpUrl(f"http://youtube.com/watch?v={post.video_id}"),  # pyright: ignore
                title=post.title,
                posted_at=utc_dt,
                media=[x for x in media if x is not None],  # TODO: add list of all media available for short view
            )
            logger.debug(f"get_posts_list({channel_id}) : progress {i:0>4} : {post.video_id}", extra=log_extra)
        except StopIteration:
            break
        except Exception as e:
            logger.error(f"wrong youtube content {fmt_err(e)}", extra=log_extra, exc_info=e)
            continue
    logger.info(f"get_posts_list_channel found {i + 1} posts", extra=log_extra)


async def get_channel_posts_list(channel_id: str, dt_from: datetime, dt_to: datetime, *, log_extra: dict[str, str]) -> AsyncIterator[FeedRecPostShort]:
    logger.debug(f"get_channel_posts_list({channel_id}) -> start {dt_from}...{dt_to}", extra=log_extra)
    utc_dt_to = as_utc(dt_to)
    utc_dt_from = as_utc(dt_from)
    try:
        channel = Channel(f"https://www.youtube.com/@{channel_id}")
    except Exception as e:
        logger.warning(f"has problem with youtube channel :: {channel_id}, error :: {fmt_err(e)}", extra=log_extra, exc_info=e)
        raise YouTubeNotFoundChannelScrapperError(channel_id) from e
    return _get_posts_list(enumerate(channel.videos), channel_id, utc_dt_from, utc_dt_to, log_extra=log_extra)


async def get_playlist_posts_list(
    playlist_id: str,
    dt_from: datetime,
    dt_to: datetime,
    *,
    log_extra: dict[str, str],
) -> AsyncIterator[FeedRecPostShort]:
    logger.debug(f"get_playlist_posts_list({playlist_id}) -> start {dt_from}...{dt_to}", extra=log_extra)
    utc_dt_to = as_utc(dt_to)
    utc_dt_from = as_utc(dt_from)
    try:
        playlist = Playlist(f"https://www.youtube.com/playlist?list={playlist_id}")
    except Exception as e:
        logger.error(f"has problem with youtube playlist :: {playlist_id}, error :: {e}", exc_info=e, extra=log_extra)
        raise YouTubeNotFoundChannelScrapperError(playlist_id) from e
    return _get_posts_list(enumerate(playlist.videos), playlist_id, utc_dt_from, utc_dt_to, log_extra=log_extra)
