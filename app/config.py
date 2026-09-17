import os
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    app_name: str = "Customer Support Agent API"
    app_version: str = "1.0.0"

    # ------------------------------------------------------------------
    # Qwen / DashScope
    # ------------------------------------------------------------------

    qwen_model: str = "qwen3.7-max-2026-05-17"
    qwen_language: str = "English"

    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/api/v1"

    qwen_compatible_base_url: str = (
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )

    qwen_api_key: str = Field(
        ...,
        min_length=1,
        validation_alias="DASHSCOPE_API_KEY",
    )

    # LangSmith tracing is opt-in so local development does not require an
    # external tracing account.
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANGSMITH_API_KEY",
            "LANGCHAIN_API_KEY",
        ),
    )
    langsmith_project: str = "customer-support-agent"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    jwt_secret_key: str = Field(
        ...,
        min_length=32,
        validation_alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()


# ----------------------------------------------------------------------
# Backward-compatible module-level configuration
# ----------------------------------------------------------------------
#
# Existing imports such as:
#
#     from app.config import QWEN_MODEL
#
# continue to work without changing the rest of the application.
# ----------------------------------------------------------------------

_settings = get_settings()

QWEN_MODEL = _settings.qwen_model
QWEN_LANGUAGE = _settings.qwen_language
QWEN_BASE_URL = _settings.qwen_base_url
QWEN_COMPATIBLE_BASE_URL = _settings.qwen_compatible_base_url
QWEN_API_KEY = _settings.qwen_api_key

LANGSMITH_TRACING = _settings.langsmith_tracing
LANGSMITH_API_KEY = _settings.langsmith_api_key
LANGSMITH_PROJECT = _settings.langsmith_project
LANGSMITH_ENDPOINT = _settings.langsmith_endpoint

if LANGSMITH_TRACING or LANGSMITH_API_KEY:
    if not LANGSMITH_API_KEY:
        raise RuntimeError(
            "LANGSMITH_API_KEY is required when LANGSMITH_TRACING=true"
        )
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT

JWT_SECRET_KEY = _settings.jwt_secret_key
JWT_ALGORITHM = _settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.access_token_expire_minutes

CORS_ORIGINS = _settings.cors_origins
