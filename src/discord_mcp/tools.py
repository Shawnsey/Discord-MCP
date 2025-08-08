"""
MCP Tools for Discord integration.

This module implements all the write operations (tools) that allow AI assistants
to perform actions on Discord through the Model Context Protocol.
"""

from typing import Optional

import structlog
from mcp.server.fastmcp import FastMCP

from .services import IDiscordService

logger = structlog.get_logger(__name__)


def register_tools(server: FastMCP) -> None:
    """Register all Discord MCP tools with the server."""

    @server.tool(
        name="list_guilds", description="List all guilds registered in the server."
    )
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

    @server.tool(
        name="list_channels", description="List all channels registered in the server."
    )
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

    @server.tool()
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

    @server.tool()
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

    @server.tool()
    async def send_message(
        channel_id: str, content: str, reply_to_message_id: Optional[str] = None
    ) -> str:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: The Discord channel ID to send the message to
            content: The message content to send
            reply_to_message_id: Optional message ID to reply to

        Returns:
            Success message with the sent message ID, or error message
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.send_message(
            channel_id, content, reply_to_message_id
        )

    @server.tool()
    async def send_dm(user_id: str, content: str) -> str:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the DM to
            content: The message content to send

        Returns:
            Success message with the sent message ID, or error message
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.send_direct_message(user_id, content)

    @server.tool()
    async def delete_message(channel_id: str, message_id: str) -> str:
        """
        Delete a message from a Discord channel.

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to delete

        Returns:
            Success message or error message
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.delete_message(channel_id, message_id)

    @server.tool()
    async def edit_message(channel_id: str, message_id: str, new_content: str) -> str:
        """
        Edit a message in a Discord channel (only works for bot's own messages).

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to edit
            new_content: The new content for the message

        Returns:
            Success message or error message
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.edit_message(channel_id, message_id, new_content)

    @server.tool()
    async def read_direct_messages(user_id: str, limit: int = 10) -> str:
        """
        Read direct messages from a DM channel with a specific user.

        Args:
            user_id: The Discord user ID to read DMs with
            limit: Maximum number of messages to retrieve (default: 10, max: 100)

        Returns:
            Formatted list of direct messages or error message
        """
        # Get context from server
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_service: IDiscordService = lifespan_ctx["discord_service"]

        return await discord_service.read_direct_messages(user_id, limit)

    logger.info("Discord MCP tools registered successfully")
