"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Facebook / Instagram
    facebook_app_secret: str = ""
    instagram_page_access_token: str = "YOUR_PAGE_ACCESS_TOKEN_HERE"
    instagram_page_id: str = "YOUR_PAGE_ID_HERE"
    webhook_verify_token: str = "bukhari_sales_verify_2024"

    # Telegram
    telegram_bot_token: str = "5781872713:AAGxR-kw4lHufPQFwCWyYozRpz2cS8t53H4"

    # OpenAI
    openai_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://bukhari:bukhari_sales_2024@localhost:5432/bukhari_sales"

    # App
    app_url: str = "https://sales.gonzo.ink"
    graph_api_version: str = "v21.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def graph_api_base(self) -> str:
        return f"https://graph.facebook.com/{self.graph_api_version}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
