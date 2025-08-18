import asyncio
import logging

import streamlit as st
from redis.asyncio import Redis

from src import log
from src.app_dash.utils.streamlit import st_no_top_borders

logger = logging.getLogger(__name__)

rds = Redis()
mdl_name = "src.app_dash.dashboard.pages.100_Task"


async def main(log_extra: dict[str, str]) -> None:
    st.set_page_config(
        page_title="CHAT WITH CONTENT CREATORS",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("CHAT WITH CONTENT CREATORS")
    with st.form("CHAT"):
        messsage = st.chat_input("message", help="message for ai person")
        if not st.form_submit_button("send"):
            return
        st.write(f'U: {messsage}')


with log.scope(logger, mdl_name) as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
