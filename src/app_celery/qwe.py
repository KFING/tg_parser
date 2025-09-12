from datetime import datetime

import httpx

from src.dto.feed_rec_info import Source, Task
from src.parser_app_api.models.request_models.feed_rec_request_info import ParsingParametersApiMdl

task = ParsingParametersApiMdl(
    source=Source.TELEGRAM,
    channel_name="masterbinarylog",
    dt_to=datetime.now(),
    dt_from=datetime.now(),
)
with httpx.Client() as client:
    response = client.post("http://localhost:50001/start_parser", data=task.model_dump_json())
