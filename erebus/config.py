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
    telegram_allowed_users: Optional[str] = Field(
        default=None,
        description="Comma-separated Telegram user IDs allowed to interact with the bot",
    )
    telegram_home_channel: Optional[str] = Field(
        default=None,
        description="Telegram chat/channel ID for proactive bot notifications",
    )

    # --- Microsoft Teams ---
    teams_app_id: Optional[str] = Field(default=None, description="Microsoft Teams App ID")
    teams_app_password: Optional[str] = Field(
        default=None, description="Microsoft Teams App Password"
    )

    # --- API Server ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8741)

    # --- Skills ---
    skills_dir: Optional[str] = Field(
        default=None,
        description="Path to additional skills directory (SKILL.md format)",
    )

    # --- Notifications ---
    apprise_default_url: Optional[str] = Field(
        default=None,
        description="Default apprise notification URL (quick single-channel setup)",
    )

    # --- Agent Behaviour ---
    enable_agentic_memory: bool = Field(default=False, description="Enable post-turn memory extraction")
    enable_learning: bool = Field(default=False, description="Enable post-turn user-profile learning")

    # --- Soul / Personality ---
    soul_file: Optional[str] = Field(
        default=None,
        description="Path to SOUL.md personality file",
    )

    # --- Authentication ---
    auth_enabled: bool = Field(default=False, description="Enable authentication middleware")
    auth_provider: str = Field(
        default="github",
        description="Auth provider: 'github' (OAuth) or 'authelia' (forward-auth headers)",
    )
    secret_key: Optional[str] = Field(
        default=None,
        description="Secret key for signing session cookies (generate: openssl rand -hex 32)",
    )

    # GitHub OAuth
    github_client_id: Optional[str] = Field(default=None, description="GitHub OAuth App client ID")
    github_client_secret: Optional[str] = Field(
        default=None, description="GitHub OAuth App client secret"
    )
    github_allowed_logins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed GitHub usernames (empty = allow all)",
    )

    # Authelia forward-auth
    authelia_header_user: str = Field(
        default="Remote-User",
        description="Header name carrying the authenticated username from Authelia",
    )
    authelia_header_name: str = Field(
        default="Remote-Name",
        description="Header name carrying the display name from Authelia",
    )

    # --- API Keys & Endpoints (pass-through for model providers) ---
    # OpenAI / custom OpenAI-compatible
    openai_api_key: Optional[str] = Field(default=None)
    openai_endpoint: Optional[str] = Field(
        default=None, description="Custom base URL for OpenAI-compatible API"
    )

    # Anthropic / Claude
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_endpoint: Optional[str] = Field(
        default=None, description="Custom base URL for Anthropic API"
    )

    # Google
    google_api_key: Optional[str] = Field(default=None)

    # OpenRouter (OpenAI-compatible; set provider to 'openrouter')
    openrouter_api_key: Optional[str] = Field(default=None)

    # Azure AI Foundry
    azure_foundry_endpoint: Optional[str] = Field(
        default=None, description="Azure AI Foundry endpoint URL"
    )
    azure_foundry_api_key: Optional[str] = Field(default=None)
    azure_foundry_api_version: Optional[str] = Field(default=None)

    # Obsidian Local REST API
    obsidian_api_url: Optional[str] = Field(
        default=None,
        description="Obsidian Local REST API base URL (e.g. https://localhost:27124)",
    )
    obsidian_api_key: Optional[str] = Field(
        default=None,
        description="Obsidian Local REST API key (Authorization: Bearer ...)",
    )

    # Agentic Fetch API
    agentic_fetch_url: Optional[str] = Field(
        default=None,
        description="Agentic Fetch API base URL for web search and fetch",
    )


def get_settings() -> ErebusSettings:
    """Return a cached settings instance."""
    return ErebusSettings()
