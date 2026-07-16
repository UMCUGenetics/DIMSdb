from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DATABASE_POOL_RECYCLE: int = 25000
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    APP_HUMAN_READABLE_NAME: str = "sampledb"
    APP_HOSTNAME: str = "localhost:8443"  # Without protocol, but with the port

    JWT_EXPIRATION_TTL_USERS: float = 30  # JWT Expiretime in minutes
    JWT_EXPIRATION_TTL_CLIENTS: float = 5  # JWT Expiretime in minutes
    JWT_SECRET: Annotated[str, Field(min_length=32)] = "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_OF_AT_LEAST_32_CHARACTERS"
    JWT_ALGORITHM: str = "HS256"
    JWT_COOKIE_KEY: str = "SH_API_JWT"
    JWT_COOKIE_DOMAIN: Annotated[str, Field(min_length=1)] = "localhost"
    JWT_COOKIE_PATH: str = "/"

    MAIL_HOST: str = ""
    MAIL_PORT: int = 25
    MAIL_FROM_ADDRESS: str = ""

    model_config = SettingsConfigDict(env_file=str(f"{Path(__file__).resolve().parents[2]}/.env"))

settings = Settings()
