"""Erebus configuration management using pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    return Path(os.environ.get("EREBUS_DATA_DIR", str(Path.home() / ".erebus")))


class ErebusSettings(BaseSettings):
    """Global settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="EREBUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Data & Storage ---
    data_dir: Path = Field(default_factory=_default_data_dir)

    @property
    def db_path(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return str(self.data_dir / "erebus.db")

    # --- Model Configuration ---
    default_model: str = Field(
        default="openai:gpt-4o",
        description="Default model in provider:model_id format",
    )
    reasoning_model: Optional[str] = Field(
        default=None,
        description="Optional reasoning model for complex thinking",
    )

    # --- Telegram ---
    telegram_token: Optional[str] = Field(default=None, description="Telegram Bot API token")
    telegram_webhook_url: Optional[str] = Field(
        default=None, description="Public HTTPS URL for Telegram webhooks"
    )

    # --- Microsoft Teams ---
    teams_app_id: Optional[str] = Field(default=None, description="Microsoft Teams App ID")
    teams_app_password: Optional[str] = Field(
        default=None, description="Microsoft Teams App Password"
    )

    # --- API Server ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8741)

    # --- Soul / Personality ---
    soul_file: Optional[str] = Field(
        default=None,
        description="Path to SOUL.md personality file",
    )

    # --- API Keys (pass-through for model providers) ---
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    openrouter_api_key: Optional[str] = Field(default=None)


def get_settings() -> ErebusSettings:
    """Return a cached settings instance."""
    return ErebusSettings()
