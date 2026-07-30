from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

for env_path in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
    if env_path.exists():
        load_dotenv(env_path)
        break


class Settings(BaseSettings):
    app_name: str = "ci-cd-dashboard"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    log_level: str = "INFO"
    github_token: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 25
    smtp_username: str | None = None
    smtp_password: str | None = None
    from_email: str | None = None
    to_email: str | None = None
    smtp_recipients: str | None = None
    email_alerts_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
