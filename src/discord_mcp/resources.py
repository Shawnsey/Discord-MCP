"""
MCP Resources for Discord integration.

This module implements all the read-only resources that expose Discord data
to AI assistants through the Model Context Protocol.
"""

from typing import Any, Dict, List

import structlog
from mcp.server.fastmcp import Context, FastMCP

from .config import Settings
from .discord_client import DiscordAPIError, DiscordClient
from .services import IDiscordService

logger = structlog.get_logger(__name__)


def register_resources(server: FastMCP) -> None:
    """Register all Discord MCP resources with the server."""

    @server.resource("guilds://")
    async def list_guilds() -> str:
        """
        List all Discord guilds (servers) the bot has access to.

        Returns a formatted list of guilds with their basic information
        including ID, name, member count, and permissions.
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.get_guilds_formatted()

    @server.resource("channels://{guild_id}")
    async def list_channels(guild_id: str) -> str:
        """
        List all channels in a specific Discord guild.

        Args:
            guild_id: The Discord guild (server) ID

        Returns a formatted list of channels with their information
        including ID, name, type, topic, and permissions.
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.get_channels_formatted(guild_id)

    @server.resource("messages://{channel_id}")
    async def get_messages(channel_id: str) -> str:
        """
        Get recent messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID

        Returns a formatted list of recent messages with author information,
        timestamps, and content.
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.get_messages_formatted(channel_id)

    @server.resource("user://{user_id}")
    async def get_user_info(user_id: str) -> str:
        """
        Get information about a Discord user.

        Args:
            user_id: The Discord user ID

        Returns formatted user information including username, avatar,
        and other available details.
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.get_user_info_formatted(user_id)

    logger.info("Discord MCP resources registered successfully")
