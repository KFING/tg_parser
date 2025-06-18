import logging
import os
import pathlib
from enum import Enum, unique
from pathlib import Path
from typing import Final

from pydantic import HttpUrl, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings

ROOT_PATH = Path(__file__).parent.parent


ENV_IS_TEST = os.environ.get("ENV", None) == "test"

logger = logging.getLogger(__name__)


@unique
class AppName(Enum):
    app_api = "app_api"
    app_celery = "app_celery"
    app_dash = "app_dash"

    @property
    def app_directory(self) -> pathlib.Path:
        return ROOT_PATH / "src" / self.value


@unique
class AppEnv(Enum):
    CI = "ci"
    TEST = "test"
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    ROOT_PATH: Path = ROOT_PATH
    LOG_LVL: LogLevel = LogLevel.INFO

    SENTRY_DSN: str = ""

    ENV: AppEnv = AppEnv.PROD
    app: AppName  # must be set in constructor

    SECRET_KEY: SecretStr

    MAIN_DB_URL: SecretStr = SecretStr("")
    CACHE_DB_URL: SecretStr = SecretStr("")

    CELERY_BACKEND: SecretStr = SecretStr("")
    CELERY_BROKER: SecretStr = SecretStr("")

    TG_API_ID: SecretStr
    TG_API_HASH: SecretStr
    TG_PHONE: SecretStr
    TG_PASSWORD: SecretStr

    INSTAGRAM_USERNAME: SecretStr
    INSTAGRAM_PASSWORD: SecretStr

    KEYCLOAK_URL: HttpUrl
    KEYCLOAK_URL_GET_CLIENT_TOKEN: HttpUrl
    KEYCLOAK_ADMIN_REALM_NAME: str
    KEYCLOAK_FEEDRECCO_REALM_NAME: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_SECRET_KEY: SecretStr
    KEYCLOAK_ADMIN_USERNAME: str
    KEYCLOAK_ADMIN_PASSWORD: SecretStr

    DB_URL: PostgresDsn

    PADDLE_CLIENT_SECRET_KEY: SecretStr
    PADDLE_CLIENT_TEST_SECRET_KEY: SecretStr
    PADDLE_TRANSACTION_PAID_NOTIFICATION_SECRET: SecretStr

    CUSTOMER_SITE_ID: SecretStr
    CUSTOMER_API_KEY: SecretStr

    GOOGLE_API_KEY: SecretStr

    @property
    def is_local(self) -> bool:
        return self.ENV == AppEnv.LOCAL

    @property
    def is_testing(self) -> bool:
        return self.ENV in {AppEnv.CI, AppEnv.TEST}

    @property
    def is_prod(self) -> bool:
        return self.ENV == AppEnv.PROD

    class Config:  # pyright: ignore
        env_file = ROOT_PATH / ".env" if not ENV_IS_TEST else ROOT_PATH / ".env.test"


# TODO: replace with right app
settings: Final = Settings(app=AppName.app_api)  # pyright: ignore

SCRAPPER_RESULTS_DIR_TELEGRAM_RAW = settings.ROOT_PATH / ".var" / "data" / "telegram" / "raw"

SCRAPPER_RESULTS_DIR_TELEGRAM_RAW.mkdir(exist_ok=True, parents=True)


