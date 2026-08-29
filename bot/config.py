from datetime import date
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import pytz


class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    TIMEZONE_NAME: str = "Europe/Kyiv"
    SEMESTER_START_DATE: date = date(2026, 9, 1)
    DATABASE_PATH: Path = Path("bot_database.sqlite3")
    SCHEDULE_FILE_PATH: Path = Path(__file__).parent / "data" / "schedule.json"
    DEFAULT_NOTIFY_MINUTES: int = 10
    WEB_ENABLED: bool = True
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8080
    PORT: int | None = None

    @property
    def effective_web_port(self) -> int:
        return self.PORT if self.PORT is not None else self.WEB_PORT


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def timezone(self):
        return pytz.timezone(self.TIMEZONE_NAME)


config = Settings()
