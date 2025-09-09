"""
Configuration management for Discord MCP Server.

This module handles loading and validating configuration from environment
variables using Pydantic settings for type safety and validation.
"""

from typing import List, Optional, Set

import structlog
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = structlog.get_logger(__name__)


class DiscordConfig(BaseSettings):
    """Discord-specific configuration settings."""

    # Required Discord credentials
    bot_token: str = Field(
        ...,
        description="Discord bot token",
        min_length=50,  # Discord tokens are typically 59+ characters
    )
    application_id: str = Field(
        ...,
        description="Discord application ID",
        min_length=17,  # Discord snowflakes are 17-19 digits
        max_length=19,
    )

    # Optional access restrictions
    allowed_guilds: Optional[List[str]] = Field(
        default=None, description="Comma-separated list of allowed guild IDs"
    )
    allowed_channels: Optional[List[str]] = Field(
        default=None, description="Comma-separated list of allowed channel IDs"
    )

    @field_validator("allowed_guilds", mode="before")
    @classmethod
    def parse_allowed_guilds(cls, v):
        """Parse comma-separated guild IDs."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return [guild_id.strip()
                    for guild_id in v.split(",") if guild_id.strip()]
        return v

    @field_validator("allowed_channels", mode="before")
    @classmethod
    def parse_allowed_channels(cls, v):
        """Parse comma-separated channel IDs."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return [
                channel_id.strip() for channel_id in v.split(",") if channel_id.strip()
            ]
        return v

    def get_allowed_guilds_set(self) -> Optional[Set[str]]:
        """Get allowed guilds as a set for fast lookup."""
        return set(self.allowed_guilds) if self.allowed_guilds else None

    def get_allowed_channels_set(self) -> Optional[Set[str]]:
        """Get allowed channels as a set for fast lookup."""
        return set(self.allowed_channels) if self.allowed_channels else None


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration."""

    requests_per_second: float = Field(
        default=5.0,
        description="Maximum requests per second to Discord API",
        gt=0,
        le=50,  # Discord's rate limit is typically 50 requests per second
    )
    burst_size: int = Field(
        default=10, description="Maximum burst size for rate limiting", gt=0, le=100
    )

    model_config = {"env_prefix": "RATE_LIMIT_"}


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="json", description="Logging format (json or text)")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = {"json", "text"}
        if v.lower() not in valid_formats:
            raise ValueError(
                f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v.lower()

    model_config = {"env_prefix": "LOG_"}


class ServerConfig(BaseSettings):
    """MCP server configuration."""

    name: str = Field(default="Discord MCP Server", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    debug: bool = Field(default=False, description="Enable debug mode")
    development_mode: bool = Field(
        default=False, description="Enable development mode")

    model_config = {"env_prefix": "SERVER_"}


class Settings(BaseSettings):
    """Main application settings."""

    # Discord configuration
    discord_bot_token: str = Field(...,
                                   description="Discord bot token", min_length=50)
    discord_application_id: str = Field(
        ..., description="Discord application ID", min_length=17, max_length=19
    )
    allowed_guilds: Optional[str] = Field(
        default=None, description="Comma-separated list of allowed guild IDs"
    )
    allowed_channels: Optional[str] = Field(
        default=None, description="Comma-separated list of allowed channel IDs"
    )

    # Rate limiting
    rate_limit_requests_per_second: float = Field(
        default=5.0,
        description="Maximum requests per second to Discord API",
        gt=0,
        le=50,
    )
    rate_limit_burst_size: int = Field(
        default=10, description="Maximum burst size for rate limiting", gt=0, le=100
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json", description="Logging format (json or text)")

    # Server
    server_name: str = Field(
        default="Discord MCP Server", description="Server name")
    server_version: str = Field(default="0.1.0", description="Server version")
    debug: bool = Field(default=False, description="Enable debug mode")
    development_mode: bool = Field(
        default=False, description="Enable development mode")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("allowed_guilds", mode="before")
    @classmethod
    def parse_allowed_guilds(cls, v):
        """Parse comma-separated guild IDs."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v
        return v

    @field_validator("allowed_channels", mode="before")
    @classmethod
    def parse_allowed_channels(cls, v):
        """Parse comma-separated channel IDs."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = {"json", "text"}
        if v.lower() not in valid_formats:
            raise ValueError(
                f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v.lower()

    def get_allowed_guilds_list(self) -> Optional[List[str]]:
        """Get allowed guilds as a list."""
        if self.allowed_guilds is None:
            return None
        return [
            guild_id.strip()
            for guild_id in self.allowed_guilds.split(",")
            if guild_id.strip()
        ]

    def get_allowed_channels_list(self) -> Optional[List[str]]:
        """Get allowed channels as a list."""
        if self.allowed_channels is None:
            return None
        return [
            channel_id.strip()
            for channel_id in self.allowed_channels.split(",")
            if channel_id.strip()
        ]

    def get_allowed_guilds_set(self) -> Optional[Set[str]]:
        """Get allowed guilds as a set for fast lookup."""
        guilds = self.get_allowed_guilds_list()
        return set(guilds) if guilds else None

    def get_allowed_channels_set(self) -> Optional[Set[str]]:
        """Get allowed channels as a set for fast lookup."""
        channels = self.get_allowed_channels_list()
        return set(channels) if channels else None

    def is_guild_allowed(self, guild_id: str) -> bool:
        """Check if a guild ID is allowed."""
        allowed_guilds = self.get_allowed_guilds_set()
        if allowed_guilds is None:
            return True  # No restrictions
        return guild_id in allowed_guilds

    def is_channel_allowed(self, channel_id: str) -> bool:
        """Check if a channel ID is allowed."""
        allowed_channels = self.get_allowed_channels_set()
        if allowed_channels is None:
            return True  # No restrictions
        return channel_id in allowed_channels


def load_settings() -> Settings:
    """Load and validate application settings."""
    try:
        settings = Settings()
        logger.info(
            "Settings loaded successfully",
            server_name=settings.server_name,
            debug_mode=settings.debug,
            development_mode=settings.development_mode,
            log_level=settings.log_level,
            rate_limit_rps=settings.rate_limit_requests_per_second,
            allowed_guilds_count=(
                len(settings.get_allowed_guilds_list())
                if settings.get_allowed_guilds_list()
                else None
            ),
            allowed_channels_count=(
                len(settings.get_allowed_channels_list())
                if settings.get_allowed_channels_list()
                else None
            ),
        )
        return settings
    except Exception as e:
        logger.error("Failed to load settings", error=str(e))
        raise


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = load_settings()
    return _settings
