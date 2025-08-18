"""
Discord MCP Services Package.

This package contains the service layer implementation for Discord operations,
providing a clean abstraction over the Discord API client and eliminating
code duplication between tools and resources through comprehensive refactoring.
"""

from .discord_service import DiscordService
from .interfaces import IDiscordService

__all__ = [
    "IDiscordService",
    "DiscordService",
]
