from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    database_path: Path = Field(default=PROJECT_ROOT / "data" / "reviews.db", alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def system_prompt_path(self) -> Path:
        return PROJECT_ROOT / "bot" / "prompts" / "system_prompt.txt"

    @property
    def demo_reviews_path(self) -> Path:
        return PROJECT_ROOT / "data" / "demo_reviews.json"


def get_settings() -> Settings:
    return Settings()
