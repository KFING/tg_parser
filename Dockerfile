FROM python:3.12 AS builder
COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry

COPY .env.template .env.test srv ./
COPY src/parser_app_api src/cli_scrapper src/common src/const  src/dto src/external_youtube src/external_telegram ./

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --no-interaction --no-ansi





CMD ["uvicorn", "src.app_api.main:get_app", \
    "--timeout-graceful-shutdown", "10", \
    "--limit-max-requests", "1024", \
    "--loop", "asyncio", \
    "--use-colors", \
    "--reload", \
    "--host", "0.0.0.0", \
    "--port", "40001", \
    "--log-level", "error", \
    "--no-access-log"]
