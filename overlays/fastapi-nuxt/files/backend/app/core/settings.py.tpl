from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "${PROJECT_NAME}"
    database_url: str = "postgresql+asyncpg://app:change-me@database:5432/${DATABASE_NAME}"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: list[str] = ["http://localhost:${FRONTEND_PORT}"]


settings = Settings()

