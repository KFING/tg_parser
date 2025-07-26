import asyncio
import logging
from datetime import datetime

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders
from src.common.moment import END_OF_EPOCH, START_OF_EPOCH
from src.dto.post import Source
from src.dto.redis_task import RedisTask

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.100_Task"

async def main(*, log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="CHAT WITH CONTENT CREATORS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT WITH CONTENT CREATORS")
    with st.form("CHAT"):
        messsage = st.text_input("message", help="message for ai person")
        if not st.form_submit_button("send"):
            return



with log.scope(logger, mdl_name) as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
