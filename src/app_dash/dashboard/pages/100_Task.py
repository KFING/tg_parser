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
        page_title="TELEGRAM CHANNEL SCRAPER",
        page_icon="👋",
        layout="wide",
    )
    st_no_top_borders()

    st.header("TELEGRAM CHANNEL SCRAPER")
    with st.form("POST"):
        source = st.selectbox("Source", (Source.YOUTUBE, Source.TELEGRAM))
        channel_name = st.text_input("Channel name", help="t.me/CHANNEL_NAME")
        time_period = st.date_input("Select time period", (START_OF_EPOCH, END_OF_EPOCH), START_OF_EPOCH, END_OF_EPOCH, format="MM.DD.YYYY")
        if not st.form_submit_button("find"):
            return
    with st.spinner("wait few seconds..."):
        if isinstance(time_period, tuple) and len(time_period) == 2:
            start_of_epoch = datetime(time_period[0].year, time_period[0].month, time_period[0].day)
            end_of_epoch = datetime(time_period[-1].year, time_period[-1].month, time_period[-1].day)
            await rds.sadd(str(RedisTask.channel_tasks.value), channel_name)
            await rds.rpush(f"{source.value}${channel_name}", str(start_of_epoch), str(end_of_epoch))
            st.write(await rds.lrange(f"{source.value}${channel_name}", 0, -1))

        else:
            st.write("WARNING: time period is invalid")
            return



with log.scope(logger, mdl_name) as _log_extra:
    asyncio.run(main(log_extra=_log_extra))
