from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Vizzy Chat API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    database_url: str = Field(default="sqlite+aiosqlite:///./vizzy_chat.db", alias="DATABASE_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_text_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_TEXT_MODEL")
    gemini_image_model: str = Field(default="imagen-3.0-generate-002", alias="GEMINI_IMAGE_MODEL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    history_window: int = Field(default=3, alias="HISTORY_WINDOW")
    auto_reset_db_on_schema_mismatch: bool = Field(
        default=False,
        alias="AUTO_RESET_DB_ON_SCHEMA_MISMATCH",
    )
    mock_stream_delay_ms: int = Field(default=25, alias="MOCK_STREAM_DELAY_MS")
    allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="ALLOWED_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
