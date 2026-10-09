"""Application settings, loaded from environment variables and/or a `.env` file."""

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class NedSettings(BaseSettings):
    """Settings for the NED (Nationaal Energie Dashboard) API client.

    Values are read from environment variables prefixed with `NED_`, e.g.
    `NED_API_KEY=...` in the environment or in a `.env` file at the project root.
    """

    model_config = SettingsConfigDict(
        env_prefix="NED_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr
    base_url: HttpUrl = HttpUrl("https://api.ned.nl/v1")
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0
