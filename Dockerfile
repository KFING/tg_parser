FROM python:3.12 AS builder
COPY pyproject.toml poetry.lock ./

COPY pyproject.docker.toml ./pyproject.toml

RUN pip install --no-cache-dir poetry

COPY .env.template .env.test srv ./
COPY src/parser_app_api/  ./src/parser_app_api/
COPY src/cli_scrapper/ ./src/cli_scrapper/
COPY src/const/ ./src/const/
COPY src/dto/ ./src/dto/
COPY src/external_youtube/ ./src/external_youtube/
COPY src/external_telegram/ ./src/external_telegram/
COPY src/log.py ./src/
COPY src/env.py ./src/
COPY src/errors.py ./src/
COPY srv/ ./srv/

COPY src/common/__init__.py ./src/common/
COPY src/common/array_utils.py ./src/common/
COPY src/common/async_utils.py ./src/common/
COPY src/common/moment.py ./src/common/
COPY src/common/pydantic_utils.py ./src/common/

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --no-interaction --no-ansi

RUN pip install uvicorn




CMD ["python", "-m", "uvicorn", "src.parser_app_api.main:get_app", \
    "--timeout-graceful-shutdown", "10", \
    "--limit-max-requests", "1024", \
    "--loop", "asyncio", \
    "--use-colors", \
    "--reload", \
    "--host", "0.0.0.0", \
    "--port", "40001", \
    "--log-level", "error", \
    "--no-access-log"]
