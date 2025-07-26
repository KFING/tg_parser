import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import httpx
from pydantic import HttpUrl, BaseModel

from src.app_api.dependencies import get_db_main_manager, get_db_main
from src.app_celery.main import app
from src.common.async_utils import run_on_loop
from src.db_main.cruds import tg_post_crud
from src.dto.redis_task import Task
from src.dto.post import Post
from src.env import SCRAPPER_RESULTS_DIR__TELEGRAM

logger = logging.getLogger(__name__)

class InvalidDataException(Exception):
    pass


class TmpListTgPost(BaseModel):
    posts: list[Post]


def parse_data(channel_name: str, posts: list[dict[str, str]]) -> list[Post]:
    tg_posts: list[Post] = []
    try:
        for post in posts:
            tg_posts.append(Post(channel_name=post['channel_name'],
                                 post_id=int(post['post_id']),
                                 content=post['content'],
                                 pb_date=datetime.fromisoformat(post['pb_date']),
                                 link=HttpUrl(post['link']),
                                 media=post['media']))
    except InvalidDataException as e:
        logger.warning(f'CELERY WORKER :: invalid response data for channel -- {channel_name} -- {e}')
    return tg_posts


def heapify(arr: list[Post], n: int, i: int):
    largest = i # Initialize largest as root
    l = 2 * i + 1   # left = 2*i + 1
    r = 2 * i + 2   # right = 2*i + 2

  # Проверяем существует ли левый дочерний элемент больший, чем корень

    if l < n and arr[i].pb_date < arr[l].pb_date:
        largest = l

    # Проверяем существует ли правый дочерний элемент больший, чем корень

    if r < n and arr[largest].pb_date < arr[r].pb_date:
        largest = r

    # Заменяем корень, если нужно
    if largest != i:
        arr[i],arr[largest] = arr[largest],arr[i] # свап

        # Применяем heapify к корню.
        heapify(arr, n, largest)


# Основная функция для сортировки массива заданного размера
def heap_sort(arr: list[Post]):
    n = len(arr)

    # Построение max-heap.
    for i in range(n, -1, -1):
        heapify(arr, n, i)

    # Один за другим извлекаем элементы
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0)


def _save_to_file(tmp_post, tmp_posts):
    tmp = ""
    scrapper_path: Path = (SCRAPPER_RESULTS_DIR__TELEGRAM / tmp_post.channel_tasks / f"{tmp_post.pb_date.year}")
    if (scrapper_path / f"{tmp_post.channel_tasks}__{tmp_post.pb_date.month}.json").exists():
        text = json.load((scrapper_path / f"{tmp_post.channel_tasks}__{tmp_post.pb_date.month}.json").open())
        text_posts = text["posts"]
        if isinstance(text_posts, list):
            for i, post in enumerate(parse_data(tmp_post.channel_tasks, text_posts)):
                tmp_posts.insert(i, post)
            tmp = "TMP"
    scrapper_path.mkdir(parents=True, exist_ok=True)
    (scrapper_path / f"{tmp}{tmp_post.channel_tasks}__{tmp_post.pb_date.month}.json").write_text(
        TmpListTgPost(posts=tmp_posts).model_dump_json(indent=4))
    if tmp == "TMP":
        (scrapper_path / f"{tmp_post.channel_tasks}__{tmp_post.pb_date.month}.json").rename(
            (scrapper_path / f"{tmp}{tmp_post.channel_tasks}__{tmp_post.pb_date.month}.json"))

def save_to_telegram_file(posts: list[Post]) -> None:
    heap_sort(posts)
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
        else:
            # save
            _save_to_file(tmp_post, tmp_posts)
            tmp_posts.clear()
            tmp_posts.append(post)
    try:
        _save_to_file(tmp_posts[-1], tmp_posts)
    except IndexError:
        pass




@app.task(bind=True)
def parse_api(self, channel_name, task) -> None:
    with httpx.Client() as client:
        response = client.post(f"http://localhost:50001/start", data=task, timeout=10000)
        logger.debug(response.status_code)
        if response.status_code != 200:
            return
    text = response.json()
    if not isinstance(text, list):
        logger.debug(f"noooooooooooooooooooooooooooooooooooo -- {text}")
        return
    tg_posts = parse_data(channel_name, text)
    db = run_on_loop(get_db_main())
    posts = run_on_loop(tg_post_crud.create_tg_posts(db, tg_posts))
    save_to_telegram_file(posts)




