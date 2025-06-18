import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime


def get_channel_messages(channel_username):
    """
    Parse messages from a Telegram channel and save them to a JSON file
    """
    # Remove @ symbol if present
    channel_username = channel_username.lstrip('@')

    # Initialize variables
    all_messages = []
    current_id = None  # We'll get the first message ID from the channel
    consecutive_empty_responses = 0
    max_empty_responses = 3

    try:
        # First request to get the latest messages and the first message ID
        url = f"https://t.me/s/{channel_username}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to access channel. Status code: {response.status_code}")
            return None

        # Get messages from the first response
        messages = extract_messages(response.text)
        if not messages:
            print("No messages found in the channel")
            return None

        # Get the highest message ID as our starting point
        current_id = max(msg['id'] for msg in messages if msg['id'] is not None)
        all_messages.extend(messages)
        print(f"Found initial {len(messages)} messages")

        # Continue fetching older messages
        while True:
            url = f"https://t.me/s/{channel_username}/{current_id}"
            response = requests.get(url)

            if response.status_code != 200:
                print(f"Failed to fetch messages. Status code: {response.status_code}")
                break

            messages = extract_messages(response.text)

            if not messages:
                consecutive_empty_responses += 1
                print(f"No messages found for ID {current_id}. Empty responses: {consecutive_empty_responses}")
                if consecutive_empty_responses >= max_empty_responses:
                    print("Reached maximum number of consecutive empty responses. Stopping.")
                    break
            else:
                consecutive_empty_responses = 0
                new_messages = [msg for msg in messages if msg['id'] not in [m['id'] for m in all_messages]]
                all_messages.extend(new_messages)
                print(f"Fetched {len(new_messages)} new messages. Total: {len(all_messages)}")
                current_id = min(msg['id'] for msg in messages if msg['id'] is not None) - 1

            if current_id <= 1:
                print("Reached the beginning of the channel. Stopping.")
                break

            time.sleep(1)  # Delay to avoid hitting rate limits

        # Save messages to file
        if all_messages:
            filename = f'{channel_username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            save_messages_to_json(all_messages, filename)
            return filename

        return None

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


def extract_messages(html_content):
    """
    Extract messages from HTML content using BeautifulSoup
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    messages = []

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
            date = date_elem['datetime'] if date_elem else ''

            # Get text
            text_elem = message_div.find('div', class_='tgme_widget_message_text')
            text = text_elem.get_text(strip=True) if text_elem else ''

            # Get views
            views_elem = message_div.find('span', class_='tgme_widget_message_views')
            views = views_elem.get_text(strip=True) if views_elem else '0'

            # Create message object
            message = {
                'id': int(message_id) if message_id.isdigit() else None,
                'date': date,
                'text': text,
                'views': views,
                'link': f'https://t.me/{channel_name}/{message_id}'
            }

            messages.append(message)

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            continue

    return messages


def save_messages_to_json(messages, filename):
    """
    Save messages to a JSON file, sorted by ID in ascending order
    """
    # Sort messages by ID
    sorted_messages = sorted(messages, key=lambda x: x['id'] if x['id'] is not None else 0)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sorted_messages, f, ensure_ascii=False, indent=2)
    print(f"\nSuccessfully saved {len(messages)} messages to {filename}")


def main():
    """
    Main function to handle user input and start parsing
    """
    print('Telegram Channel Parser (Unofficial)')
    print('--------------------------------')

    while True:
        channel_link = input('\nEnter Telegram channel username or link (or "q" to quit): ').strip()

        if channel_link.lower() == 'q':
            break

        if not channel_link:
            print('Please enter a valid channel username or link')
            continue

        # Extract username from link if full link is provided
        if 't.me/' in channel_link:
            channel_link = channel_link.split('t.me/')[-1].split('/')[0]

        print(f'\nStarting to parse channel: @{channel_link}')

        filename = get_channel_messages(channel_link)

        if filename:
            print('\nParsing completed successfully!')
        else:
            print('\nFailed to parse the channel. Please check the username/link and try again.')

        choice = input('\nWould you like to parse another channel? (y/n): ').strip().lower()
        if choice != 'y':
            break

    print('\nThank you for using Telegram Channel Parser!')


if __name__ == '__main__':
    main()
