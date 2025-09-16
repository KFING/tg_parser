import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, HttpUrl

from src.app_api.dependencies import get_db_main_for_celery
from src.app_celery.main import app
from src.common.async_utils import run_on_loop
from src.db_main.cruds import post_crud
from src.db_main.models.post import PostDbMdl
from src.dto.feed_rec_info import Post, Source
from src.env import SCRAPPER_RESULTS_DIR
from src.service_chat_bot import manager_chat

logger = logging.getLogger(__name__)


class InvalidDataException(Exception):
    pass


class TmpListTgPost(BaseModel):
    posts: list[Post]


def posts_dbmdl_to_posts(all_posts: list[Post], posts_dbmdl: list[PostDbMdl]) -> list[Post]:
    posts: list[Post] = []
    ids_posts_dbmdl = [post_dbmdl.post_id for post_dbmdl in posts_dbmdl]
    for post in all_posts:
        if post.post_id in ids_posts_dbmdl:
            posts.append(post)
    return posts


def parse_data(source: Source, channel_name: str, posts: list[dict[str, str]]) -> list[Post]:
    tg_posts: list[Post] = []
    try:
        for post in posts:
            tg_posts.append(
                Post(
                    source=source,
                    channel_name=post["channel_name"],
                    post_id=post["post_id"],
                    content=post["content"],
                    pb_date=datetime.fromisoformat(post["pb_date"]),
                    link=HttpUrl(post["link"]),
                    # media=post["media"],
                    media=None,
                )
            )
    except InvalidDataException as e:
        logger.warning(f"CELERY WORKER :: invalid response data for channel -- {channel_name} -- {e}")
    return tg_posts


def heapify(arr: list[Post], n: int, i: int):
    largest = i  # Initialize largest as root
    l = 2 * i + 1  # left = 2*i + 1
    r = 2 * i + 2  # right = 2*i + 2

    # Проверяем существует ли левый дочерний элемент больший, чем корень

    if l < n and arr[i].pb_date < arr[l].pb_date:
        largest = l

    # Проверяем существует ли правый дочерний элемент больший, чем корень

    if r < n and arr[largest].pb_date < arr[r].pb_date:
        largest = r

    # Заменяем корень, если нужно
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]  # свап

        # Применяем heapify к корню.
        heapify(arr, n, largest)


def heap_sort(arr: list[Post]):
    n = len(arr)

    # Построение max-heap.
    for i in range(n, -1, -1):
        heapify(arr, n, i)

    # Один за другим извлекаем элементы
    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0)


def _save_to_file_and_to_qdrant(tmp_post: Post, month_posts: list[Post]):
    tmp = ""

    scrapper_path: Path = SCRAPPER_RESULTS_DIR / tmp_post.source.value / tmp_post.channel_name / f"{tmp_post.pb_date.year}"
    scrapper_path_file: Path = scrapper_path / f"{tmp_post.channel_name}__{tmp_post.pb_date.month}.json"
    parse_text_parse = month_posts
    if (scrapper_path / f"{tmp_post.channel_name}__{tmp_post.pb_date.month}.json").exists():
        text = json.load((scrapper_path / f"{tmp_post.channel_name}__{tmp_post.pb_date.month}.json").open())
        text_posts = text["posts"]
        if not isinstance(text_posts, list):
            return
        parse_text_posts = parse_data(tmp_post.source, tmp_post.channel_name, text_posts)
        ids_text_posts = [post.post_id for post in parse_text_posts]
        for post in month_posts:
            if post.post_id not in ids_text_posts:
                parse_text_posts.append(post)
        tmp = "TMP"
        heap_sort(parse_text_posts)

    scrapper_path.mkdir(parents=True, exist_ok=True)
    (scrapper_path / f"{tmp}{tmp_post.channel_name}__{tmp_post.pb_date.month}.json").write_text(TmpListTgPost(posts=parse_text_parse).model_dump_json(indent=4))
    if tmp == "TMP":
        (scrapper_path / f"{tmp}{tmp_post.channel_name}__{tmp_post.pb_date.month}.json").rename(
            scrapper_path / f"{tmp_post.channel_name}__{tmp_post.pb_date.month}.json"
        )
    manager_chat.add_post_to_qdrant(scrapper_path_file)


def save_post(posts: list[Post]) -> None:
    tmp_posts: list[Post] = []
    for post in posts:
        try:
            tmp_post = tmp_posts[-1]
        except IndexError:
            tmp_posts.append(post)
            continue
        if tmp_post.pb_date.month == post.pb_date.month:
            tmp_posts.append(post)
            continue
        # save
        _save_to_file_and_to_qdrant(tmp_post, tmp_posts)
        tmp_posts.clear()
        tmp_posts.append(post)
    try:
        _save_to_file_and_to_qdrant(tmp_posts[-1], tmp_posts)
    except IndexError:
        pass


@app.task(bind=True)
def parse_api(self, channel_name: str, task: dict[str, Any]) -> None:
    with httpx.Client() as client:
        response = client.post("http://localhost:50001/start_parser", data=task, timeout=10000)
        logger.debug(response.status_code)
        if response.status_code != 200:
            return
    text = response.json()
    if not isinstance(text, list):
        return
    posts = parse_data(Source.TELEGRAM, channel_name, text)  # ошибка тут
    db = run_on_loop(get_db_main_for_celery())
    unique_posts = run_on_loop(post_crud.create_posts(db, posts))
    save_post(posts_dbmdl_to_posts(posts, unique_posts))
