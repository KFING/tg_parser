import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
from bs4 import BeautifulSoup
from pydantic import HttpUrl
from redis.asyncio import Redis

from src.common.moment import as_utc
from src.dto import redis_models
from src.dto.feed_rec_info import Source, TaskStatus, Post

logger = logging.getLogger(__name__)

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)
rds = Redis(host="redis", port=6379)


async def get_all_messages(consecutive_empty_responses, all_messages, session, channel_name, current_id, max_empty_responses, *, log_extra) -> list[Post]:
    url = f"https://t.me/s/{channel_name}/{current_id}"

    response = await session.get(url)

    if response.status != 200:
        logger.warning(f"Failed to fetch messages. Status code: {response.status}", extra=log_extra)
        return all_messages
    dt_to = await rds.get(redis_models.source_channel_name_dt_to(Source.TELEGRAM, channel_name))
    dt_from = await rds.get(redis_models.source_channel_name_dt_from(Source.TELEGRAM, channel_name))
    utc_dt_to = datetime.fromisoformat(dt_to.decode("utf-8"))
    utc_dt_from = datetime.fromisoformat(dt_from.decode("utf-8"))
    messages = extract_messages(await response.text(), channel_name, as_utc(utc_dt_to), as_utc(utc_dt_from), log_extra=log_extra)

    if not messages:
        consecutive_empty_responses += 1
        logger.warning(f"No messages found for ID {current_id}. Empty responses: {consecutive_empty_responses}", extra=log_extra)
        if consecutive_empty_responses >= max_empty_responses:
            logger.warning("Reached maximum number of consecutive empty responses. Stopping.", extra=log_extra)
            return all_messages
    else:
        consecutive_empty_responses = 0
        new_messages = [msg for msg in messages if msg.post_id not in [m.post_id for m in all_messages]]
        all_messages.extend(new_messages)
        logger.debug(f"Fetched {len(new_messages)} new messages. Total: {len(all_messages)} -- {channel_name}", extra=log_extra)
        current_id = min(msg.post_id for msg in messages if msg.post_id is not None) - 1

    if current_id <= 1:
        logger.warning("Reached the beginning of the channel. Stopping.", extra=log_extra)
        return all_messages

    await asyncio.sleep(0.0001)  # Delay to avoid hitting rate limits
    return await get_all_messages(consecutive_empty_responses, all_messages, session, channel_name, current_id, max_empty_responses, log_extra=log_extra)


async def get_channel_messages(channel_name: str, *, log_extra: dict[str, str]) -> list[Post] | None:
    """
    Parse messages from a Telegram channel and save them to a JSON file
    """
    dt_to = await rds.get(redis_models.source_channel_name_dt_to(Source.TELEGRAM, channel_name))
    if not dt_to:
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        return None
    dt_from = await rds.get(redis_models.source_channel_name_dt_from(Source.TELEGRAM, channel_name))
    if not dt_from:
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        return None

    utc_dt_to = datetime.fromisoformat(dt_to.decode("utf-8"))
    utc_dt_from = datetime.fromisoformat(dt_from.decode("utf-8"))
    all_messages = []
    consecutive_empty_responses = 0
    max_empty_responses = 3
    session = aiohttp.ClientSession()
    try:
        # First request to get the latest messages and the first message ID
        url = f"https://t.me/s/{channel_name}"

        response = await session.get(url)

        if response.status != 200:
            await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
            logger.warning(f"Failed to access channel. Status code: {response.status}", extra=log_extra)
            await session.close()
            return None
        # Get messages from the first response
        html_text = await response.text()
        messages = extract_messages(html_text, channel_name, as_utc(utc_dt_to), as_utc(utc_dt_from), log_extra=log_extra)
        if not messages:
            await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
            logger.debug("No messages found in the channel", extra=log_extra)
            await session.close()
            return None

        # Get the highest message ID as our starting point
        current_id = max(msg.post_id for msg in messages if msg.post_id is not None)
        all_messages.extend(messages)
        logger.debug(f"Found initial {len(messages)} messages", extra=log_extra)

        # Continue fetching older messages
        # while True:
        await get_all_messages(consecutive_empty_responses, all_messages, session, channel_name, current_id, max_empty_responses, log_extra=log_extra)

        await session.close()
        # Save messages to file
        if all_messages:
            return all_messages
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        return None

    except Exception as e:
        logger.warning(f"Error occurred: {e!s}", extra=log_extra)
        await rds.set(redis_models.source_channel_name_status(Source.TELEGRAM, channel_name), TaskStatus.free.value)
        await session.close()
        return None


def extract_messages(html_content: str, channel_id: str, utc_dt_to: datetime, utc_dt_from: datetime, *, log_extra: dict[str, str]) -> list[Post]:
    """
    Extract messages from HTML content using BeautifulSoup
    """
    soup = BeautifulSoup(html_content, "html.parser")
    messages: list[Post] = []

    for message_div in soup.find_all("div", class_="tgme_widget_message"):
        try:
            # Get message ID and channel name
            post_data = message_div.get("data-post", "").split("/")
            if len(post_data) >= 2:
                channel_name, message_id = post_data[-2:]
            else:
                continue

            # Get date
            date_elem = message_div.find("time", class_="time")
            utc_dt = as_utc(datetime.fromisoformat(date_elem["datetime"]) if date_elem else datetime.utcnow())

            if utc_dt >= utc_dt_to:
                """logger.debug(
                    f"get_posts_list_channel({channel_name}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_to({utc_dt_to})", extra=log_extra
                )"""
                continue
            if utc_dt <= utc_dt_from:
                """logger.debug(
                    f"get_posts_list_channel({channel_name}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_from({utc_dt_from})", extra=log_extra
                )"""
                return messages

            # Get text
            text_elem = message_div.find("div", class_="tgme_widget_message_text")
            text = text_elem.get_text(strip=True) if text_elem else ""

            # Get views
            """views_elem = message_div.find('span', class_='tgme_widget_message_views')
            views = views_elem.get_text(strip=True) if views_elem else '0'"""

            # Create message object
            message = Post(
                channel_name=channel_id,
                post_id=str(int(message_id) if message_id.isdigit() else None),
                content=text,
                pb_date=utc_dt,
                link=HttpUrl(f"https://t.me/{channel_name}/{message_id}"),
                media=None,
            )

            messages.append(message)

        except Exception as e:
            logger.warning(f"Error processing message: {e!s}", extra=log_extra)
            continue

    return messages


async def main() -> None:
    """
    Main function to handle user input and start parsing
    """
    logger.debug("Telegram Channel Parser (Unofficial)")
    logger.debug("--------------------------------")

    channel_link = "mychannelkfing"

    logger.debug("Please enter a valid channel username or link")
    logger.debug(f"\nStarting to parse channel: @{channel_link}")

    # filename =  await get_channel_messages(channel_link)


if __name__ == "__main__":
    asyncio.run(main())
