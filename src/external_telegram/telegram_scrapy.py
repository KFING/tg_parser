import asyncio
import logging

import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timezone

from pydantic import HttpUrl

from src.common.moment import as_utc
from src.dto.tg_post import TgPost
from src.env import SCRAPPER_RESULTS_DIR_TELEGRAM_RAW

logger = logging.getLogger(__name__)

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)

async def get_channel_messages(channel_id: str, utc_dt_to: datetime = END_OF_EPOCH, utc_dt_from: datetime = START_OF_EPOCH) -> list[TgPost] | None:
    """
    Parse messages from a Telegram channel and save them to a JSON file
    """
    all_messages = []
    consecutive_empty_responses = 0
    max_empty_responses = 3

    try:

        # First request to get the latest messages and the first message ID
        url = f"https://t.me/s/{channel_id}"
        session = aiohttp.ClientSession()
        response = await session.get(url)


        if response.status != 200:
            logger.warning(f"Failed to access channel. Status code: {response.status}")
            return None
        print(type(utc_dt_to))
        # Get messages from the first response
        messages = extract_messages(await response.text(), channel_id, as_utc(utc_dt_to), as_utc(utc_dt_from))
        if not messages:
            logger.debug("No messages found in the channel")
            return None

        # Get the highest message ID as our starting point
        current_id = max(msg['id'] for msg in messages if msg['id'] is not None)
        all_messages.extend(messages)
        logger.debug(f"Found initial {len(messages)} messages")

        # Continue fetching older messages
        while True:
            url = f"https://t.me/s/{channel_id}/{current_id}"

            response = await session.get(url)

            if response.status != 200:
                logger.warning(f"Failed to fetch messages. Status code: {response.status}")
                break

            messages = extract_messages(await response.text(), channel_id, as_utc(utc_dt_to), as_utc(utc_dt_from))

            if not messages:
                consecutive_empty_responses += 1
                logger.warning(f"No messages found for ID {current_id}. Empty responses: {consecutive_empty_responses}")
                if consecutive_empty_responses >= max_empty_responses:
                    logger.warning("Reached maximum number of consecutive empty responses. Stopping.")
                    break
            else:
                consecutive_empty_responses = 0
                new_messages = [msg for msg in messages if msg['id'] not in [m['id'] for m in all_messages]]
                all_messages.extend(new_messages)
                logger.debug(f"Fetched {len(new_messages)} new messages. Total: {len(all_messages)}")
                current_id = min(msg['id'] for msg in messages if msg['id'] is not None) - 1

            if current_id <= 1:
                logger.warning("Reached the beginning of the channel. Stopping.")
                break

            time.sleep(1)  # Delay to avoid hitting rate limits

        # Save messages to file
        if all_messages:
            filename = f'{channel_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            save_messages_to_json(all_messages, filename)
            return all_messages

    except Exception as e:
        logger.warning(f"Error occurred: {str(e)}")
        return None


def extract_messages(html_content: str, channel_id: str, utc_dt_to: datetime, utc_dt_from: datetime) -> list[TgPost]:
    """
    Extract messages from HTML content using BeautifulSoup
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    messages: list[TgPost] = []

    for message_div in soup.find_all('div', class_='tgme_widget_message'):
        try:
            # Get message ID and channel name
            post_data = message_div.get('data-post', '').split('/')
            if len(post_data) >= 2:
                channel_name, message_id = post_data[-2:]
            else:
                continue

            # Get date
            date_elem = message_div.find('time', class_='time')
            utc_dt = as_utc(date_elem['datetime'] if date_elem else datetime.utcnow())

            if utc_dt_to >= utc_dt:
                """logger.debug(
                    f"get_posts_list_channel({channel_id}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_to({utc_dt_to})", extra=log_extra
                )"""
                continue
            if utc_dt > utc_dt_from:
                """logger.debug(
                    f"get_posts_list_channel({channel_id}) it={i} msg_id={post.video_id} :: dt({utc_dt}) not fit to dt_from({utc_dt_from})", extra=log_extra
                )"""
                return messages


            # Get text
            text_elem = message_div.find('div', class_='tgme_widget_message_text')
            text = text_elem.get_text(strip=True) if text_elem else ''

            # Get views
            """views_elem = message_div.find('span', class_='tgme_widget_message_views')
            views = views_elem.get_text(strip=True) if views_elem else '0'"""

            # Create message object
            message = TgPost(
                tg_channel_id=channel_id,
                tg_post_id=int(message_id) if message_id.isdigit() else None,
                content=text,
                pb_date=utc_dt,
                link=HttpUrl(f'https://t.me/{channel_name}/{message_id}')
            )

            messages.append(message)

        except Exception as e:
            logger.warning(f"Error processing message: {str(e)}")
            continue

    return messages


def save_messages_to_json(messages, filename):
    """
    Save messages to a JSON file, sorted by ID in ascending order
    """
    # Sort messages by ID
    sorted_messages = sorted(messages, key=lambda x: x['id'] if x['id'] is not None else 0)
    (SCRAPPER_RESULTS_DIR_TELEGRAM_RAW / filename).write_text(json.dumps(sorted_messages, indent=2))

    logger.debug(f"\nSuccessfully saved {len(messages)} messages to {filename}")


async def main():
    """
    Main function to handle user input and start parsing
    """
    logger.debug('Telegram Channel Parser (Unofficial)')
    logger.debug('--------------------------------')

    while True:
        channel_link = input('\nEnter Telegram channel username or link (or "q" to quit): ').strip()

        if channel_link.lower() == 'q':
            break

        if not channel_link:
            logger.debug('Please enter a valid channel username or link')
            continue

        # Extract username from link if full link is provided
        if 't.me/' in channel_link:
            channel_link = channel_link.split('t.me/')[-1].split('/')[0]

        logger.debug(f'\nStarting to parse channel: @{channel_link}')

        filename =  await get_channel_messages(channel_link)

        if filename:
            logger.debug('\nParsing completed successfully!')
        else:
            logger.debug('\nFailed to parse the channel. Please check the username/link and try again.')

        choice = input('\nWould you like to parse another channel? (y/n): ').strip().lower()
        if choice != 'y':
            break

    logger.debug('\nThank you for using Telegram Channel Parser!')


if __name__ == '__main__':
    asyncio.run(main())
