import asyncio
import logging

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.dto.redis_task import RedisTask

logger = logging.getLogger(__name__)

rds = Redis()

async def main(*, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="TELEGRAM WORKER",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("TELEGRAM WORKER")
    with st.form("POST"):
        cow = st.text_input("count of workers", help="t.me/CHANNEL_NAME")
        if not st.form_submit_button("find"):
            return
        await rds.set(RedisTask.counter_of_workers.value, cow)


with log.scope(logger, "Telegram_post") as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
