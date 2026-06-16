from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://devdesk:devdesk@localhost:5432/devdesk"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"

    access_token_minutes: int = 15
    refresh_token_days: int = 7

    cors_origins: list[str] = ["http://localhost:3000"]

    redis_url: str = "redis://localhost:6379"

    app_base_url: str = "http://localhost:3000"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@devdesk.app"

    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str


@lru_cache
def get_settings() -> Settings:
    return Settings()