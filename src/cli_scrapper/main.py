import argparse
import asyncio
import logging
from argparse import ArgumentParser
from datetime import datetime

from telethon import TelegramClient

from src import log
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.dto.download_post_recipe import DownloadPostContentRecipe, DownloadQuality
from src.dto.feed_rec_info import FeedRecPostFull, FeedRecPostShort, Lang, Source, TmpListFeedRecPostShort
from src.env import SCRAPPER_RESULTS_DIR, SCRAPPER_SESSION_DIR__TELEGRAM, settings
from src.external_telegram import telegram_scrapy

logger = logging.getLogger(__name__)

def save_to_disk(info: FeedRecPostFull) -> None:
    (SCRAPPER_RESULTS_DIR / info.src.value / info.channel_id / info.post_id).mkdir(exist_ok=True, parents=True)
    (SCRAPPER_RESULTS_DIR / info.src.value / info.channel_id / info.post_id / f"{info.post_id}.json").write_text(info.model_dump_json(indent=4))


def save_to_disk_posts_short(info: list[FeedRecPostShort], channel_id: str) -> None:
    (SCRAPPER_RESULTS_DIR / info[0].src.value / channel_id).mkdir(exist_ok=True, parents=True)
    (SCRAPPER_RESULTS_DIR / info[0].src.value / channel_id / f"{channel_id}.json").write_text(TmpListFeedRecPostShort(posts=info).model_dump_json(indent=4))


async def get_channel_posts_youtube(channel_id: str, *, dt_from: datetime, dt_to: datetime, log_extra: dict[str, str]) -> list[FeedRecPostShort]:
    return [i async for i in await youtube_scrapy.get_channel_posts_list(channel_id, dt_from=dt_from, dt_to=dt_to, log_extra=log_extra)]


async def get_playlist_posts_youtube(playlist_id: str, *, dt_from: datetime, dt_to: datetime, log_extra: dict[str, str]) -> list[FeedRecPostShort]:
    return [i async for i in await youtube_scrapy.get_playlist_posts_list(playlist_id, dt_from=dt_from, dt_to=dt_to, log_extra=log_extra)]


async def download_post_youtube(post_id: str, recipe: DownloadPostContentRecipe, *, log_extra: dict[str, str]) -> FeedRecPostFull | None:
    return await youtube_scrapy.download_post(post_id=post_id, recipe=recipe, log_extra=log_extra)


async def get_channel_posts_telegram(channel_id: str, dt_from: datetime, dt_to: datetime, *, log_extra: dict[str, str]) -> list[FeedRecPostShort]:
    tg = TelegramClient(SCRAPPER_SESSION_DIR__TELEGRAM / "telegram", int(settings.TG_API_ID.get_secret_value()), settings.TG_API_HASH.get_secret_value())
    await tg.start(phone=settings.TG_PHONE.get_secret_value(), password=settings.TG_PASSWORD.get_secret_value())  # pyright: ignore
    return [i async for i in telegram_scrapy.get_posts_list(tg, channel_id, dt_from, dt_to, log_extra=log_extra)]


async def download_post_telegram(post_id: str, recipe: DownloadPostContentRecipe, *, log_extra: dict[str, str]) -> FeedRecPostFull | None:
    tg = TelegramClient(SCRAPPER_SESSION_DIR__TELEGRAM / "telegram", int(settings.TG_API_ID.get_secret_value()), settings.TG_API_HASH.get_secret_value())
    await tg.start(phone=settings.TG_PHONE.get_secret_value(), password=settings.TG_PASSWORD.get_secret_value())  # pyright: ignore
    return await telegram_scrapy.download_post(tg, post_id, recipe, log_extra=log_extra)


async def get_channel_posts_instagram(channel_id: str, *, dt_from: datetime, dt_to: datetime, log_extra: dict[str, str]) -> list[FeedRecPostShort]:
    insta_username = settings.INSTAGRAM_USERNAME.get_secret_value()
    insta_password = settings.INSTAGRAM_PASSWORD.get_secret_value()
    loader = Instaloader()
    is_logged_in = True
    try:
        loader.load_session_from_file(insta_username, filename=str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
        is_logged_in = False
    except Exception as e:
        logger.info(f"download_post_instagram({insta_username}) :: session doesnt found", exc_info=e, extra=log_extra)
    if is_logged_in:
        try:
            try:
                loader.login(insta_username, insta_password)
                loader.save_session_to_file(str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
            except TwoFactorAuthRequiredException:
                loader.two_factor_login(input("code for insta: "))
                loader.save_session_to_file(str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
        except Exception as e:
            logger.error(e, exc_info=e, extra=log_extra)
    return [i async for i in instagram_scrapy.get_posts_list(loader, channel_id, dt_from=dt_from, dt_to=dt_to, log_extra=log_extra)]


async def download_post_instagram(post_id: str, recipe: DownloadPostContentRecipe, *, log_extra: dict[str, str]) -> FeedRecPostFull | None:
    insta_username = settings.INSTAGRAM_USERNAME.get_secret_value()
    insta_password = settings.INSTAGRAM_PASSWORD.get_secret_value()
    loader = Instaloader()
    is_logged_in = True
    try:
        loader.load_session_from_file(insta_username, filename=str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
        is_logged_in = False
    except Exception as e:
        logger.info(f"download_post_instagram({insta_username}) :: session dont found", exc_info=e, extra=log_extra)
    if is_logged_in:
        try:
            try:
                loader.login(insta_username, insta_password)
                loader.save_session_to_file(str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
            except TwoFactorAuthRequiredException:
                loader.two_factor_login(input("code for insta: "))
                loader.save_session_to_file(str(SCRAPPER_SESSION_DIR__INSTAGRAM / insta_username))
        except Exception as e:
            logger.error(e, exc_info=e, extra=log_extra)
    return await instagram_scrapy.download_post(
        loader=loader,
        post_id=post_id,
        recipe=recipe,
        log_extra=log_extra,
    )


async def main() -> None:  # noqa: PLR0915, C901
    parser = ArgumentParser()
    sub_parser = parser.add_subparsers(dest="cmd", required=True)
    get_post_info_parser = sub_parser.add_parser("download_post")
    get_post_info_parser.add_argument("--source", dest="src", type=Source, required=True, choices=list(Source))
    get_post_info_parser.add_argument("--title", dest="content_title", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--description", dest="content_description", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--captions", dest="content_captions", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--timeline", dest="content_timeline", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--preview", dest="content_preview", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--document", dest="content_document", action=argparse.BooleanOptionalAction, default=True)
    get_post_info_parser.add_argument("--video_quality", dest="content_video_quality", type=DownloadQuality, choices=list(DownloadQuality), default=None)
    get_post_info_parser.add_argument("--image_quality", dest="content_image_quality", type=DownloadQuality, choices=list(DownloadQuality), default=None)
    get_post_info_parser.add_argument("--audio_quality", dest="content_audio_quality", type=DownloadQuality, choices=list(DownloadQuality), default=None)
    get_post_info_parser.add_argument("--lang", dest="content_lang", type=lambda x: Lang.__members__[x.upper()], choices=list(Lang), default="en")
    get_post_info_parser.add_argument("post_ids", nargs="+", type=str)

    get_channel_posts_parser = sub_parser.add_parser("get_channel_posts")
    get_channel_posts_parser.add_argument("--source", dest="src", type=Source, required=True, choices=list(Source))
    get_channel_posts_parser.add_argument("--from", dest="from_dt", type=datetime.fromisoformat, default=None)
    get_channel_posts_parser.add_argument("channel_ids", nargs="+", type=str)

    args = parser.parse_args()
    # for youtube, channel: id, post: id. For instagram, channel: name, post: id. For telegram, channel: id, post: link.
    with log.scope(logger, "cli_scrapper") as log_extra:
        match args.cmd:
            case "get_channel_posts":  # don't like it
                logger.info(f"get ids in {args.channel_ids} - start", extra=log_extra)
                for channel in args.channel_ids:
                    try:
                        match args.src:
                            case Source.YOUTUBE:
                                info = await get_channel_posts_youtube(channel, dt_from=START_OF_EPOCH, dt_to=END_OF_EPOCH, log_extra=log_extra)
                                save_to_disk_posts_short(info, channel)
                            case Source.TELEGRAM:
                                info = await get_channel_posts_telegram(channel, dt_from=START_OF_EPOCH, dt_to=END_OF_EPOCH, log_extra=log_extra)
                                save_to_disk_posts_short(info, channel)
                            case Source.INSTAGRAM:
                                info = await get_channel_posts_instagram(channel, dt_from=START_OF_EPOCH, dt_to=END_OF_EPOCH, log_extra=log_extra)
                                save_to_disk_posts_short(info, channel)
                            case _:
                                raise NotImplementedError(f"{args.src} not implemented")
                    except Exception as e:  # TODO: add right exception
                        # print(e)
                        # print(traceback.format_exc())
                        logger.warning(f"download - error : {type(e).__name__} :: {e}", extra=log_extra)
                    else:
                        logger.info("download - done without errors", extra=log_extra)
            case "download_post":
                for i, post_id in enumerate(args.post_ids):
                    logger.info(f"[{i + 1}/{len(args.post_ids)}] download {post_id} - start", extra=log_extra)
                    recipe = DownloadPostContentRecipe(
                        content=args.content_description,
                        captions=args.content_captions,
                        timeline=args.content_timeline,
                        download_preview_image=args.content_preview,
                        download_document=args.content_document,
                        download_video_quality=args.content_video_quality,
                        download_audio_quality=args.content_audio_quality,
                        download_image_quality=args.content_image_quality,
                        lang=args.content_lang,
                    )
                    try:
                        match args.src:
                            case Source.YOUTUBE:
                                youtube_post = await download_post_youtube(post_id, recipe, log_extra=log_extra)
                                if youtube_post:
                                    save_to_disk(youtube_post)
                            case Source.TELEGRAM:
                                tg_post = await download_post_telegram(post_id, recipe, log_extra=log_extra)
                                if tg_post:
                                    save_to_disk(tg_post)
                            case Source.INSTAGRAM:
                                insta_post = await download_post_instagram(post_id, recipe, log_extra=log_extra)
                                if insta_post:
                                    save_to_disk(insta_post)
                            case _:
                                raise NotImplementedError(f"{args.src} not implemented")
                    except Exception as e:  # TODO: add right exception
                        # print(e)
                        # print(traceback.format_exc())
                        logger.warning(f"[{i + 1}/{len(args.post_ids)}] download {post_id} - error : {type(e).__name__} :: {e}", extra=log_extra)
                    else:
                        logger.info(f"[{i + 1}/{len(args.post_ids)}] download {post_id} - done without errors", extra=log_extra)


if __name__ == "__main__":
    asyncio.run(main())
