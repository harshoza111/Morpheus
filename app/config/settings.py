"""
Application settings loaded from environment variables / .env file.

Uses pydantic-settings so every value is validated at startup.
Add new configuration knobs here; they will be automatically read
from the environment or .env file.

Usage:
    from app.config import get_settings
    settings = get_settings()
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------------------------------------------------------------------- #
#  Resolve project root (one level above the `app/` package).                  #
# --------------------------------------------------------------------------- #
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Immutable, validated application configuration.

    Every field can be overridden by an environment variable of the same
    (upper-case) name.  Values are also read from the `.env` file at the
    project root.
    """

    # -- General ------------------------------------------------------------- #
    APP_NAME: str = "Morpheus"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # -- Database ------------------------------------------------------------ #
    # Default SQLite path lives next to the project root.
    DATABASE_URL: str = f"sqlite:///{_PROJECT_ROOT / 'morpheus.db'}"

    # -- Gemini API (placeholder for future integration) --------------------- #
    GEMINI_API_KEY: str = ""

    # -- Pydantic-settings configuration ------------------------------------- #
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore unknown env vars
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    Using `lru_cache` ensures the .env file is read only once and the
    same object is reused throughout the application lifetime.
    """
    return Settings()
