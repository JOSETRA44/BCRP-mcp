from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BCRPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    cache_ttl: int = Field(default=300, alias="BCRP_CACHE_TTL", ge=0)
    timeout: float = Field(default=30.0, alias="BCRP_TIMEOUT", gt=0)
    max_retries: int = Field(default=3, alias="BCRP_MAX_RETRIES", ge=0, le=10)
    language: Literal["esp", "ing"] = Field(default="esp", alias="BCRP_LANGUAGE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache(maxsize=1)
def get_settings() -> BCRPSettings:
    return BCRPSettings()
