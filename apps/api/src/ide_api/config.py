from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="IDE_",
        extra="ignore",
    )

    app_name: str = "Integrated Document Environment API"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+psycopg://ide:ide@localhost:5432/ide"
    session_cookie_name: str = "ide_session"
    session_ttl_seconds: int = 28800
    session_cookie_secure: bool = True
    tectonic_only_cached: bool = False
    object_storage_endpoint_url: str = "https://kr.object.ncloudstorage.com"
    object_storage_bucket: str = "ide"
    object_storage_region: str = "kr-standard"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
    max_upload_size_bytes: int = 250 * 1024 * 1024
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_relationship_model_standard: str = "gpt-5.6-luna"
    openai_relationship_model_complex: str = "gpt-5.6-terra"
    openai_relationship_prompt_version: str = "relationship-analysis-v1"
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
