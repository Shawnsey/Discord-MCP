"""
Discord Service Implementation.

This module provides the concrete implementation of the IDiscordService interface,
centralizing all Discord API operations and eliminating code duplication between
tools and resources.
"""

from typing import Optional

import structlog

from ..config import Settings
from ..discord_client import DiscordAPIError, DiscordClient
from .interfaces import IDiscordService


class DiscordService(IDiscordService):
    """
    Concrete implementation of Discord service operations.

    This service provides centralized Discord API operations with consistent
    error handling, logging, and permission validation. It eliminates code
    duplication between tools and resources by providing a single source of
    truth for Discord operations.
    """

    def __init__(
        self,
        discord_client: DiscordClient,
        settings: Settings,
        logger: structlog.stdlib.BoundLogger,
    ) -> None:
        """
        Initialize the Discord service with required dependencies.

        Args:
            discord_client: The Discord API client for making requests
            settings: Application settings including permissions and configuration
            logger: Structured logger for consistent logging across operations
        """
        self._discord_client = discord_client
        self._settings = settings
        self._logger = logger

    async def get_guilds_formatted(self) -> str:
        """
        Get a formatted list of accessible Discord guilds.

        Returns:
            str: Formatted markdown string containing guild information
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def get_channels_formatted(self, guild_id: str) -> str:
        """
        Get a formatted list of channels in a specific Discord guild.

        Args:
            guild_id: The Discord guild (server) ID

        Returns:
            str: Formatted markdown string containing channel information
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def get_messages_formatted(self, channel_id: str, limit: int = 50) -> str:
        """
        Get a formatted list of recent messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID
            limit: Maximum number of messages to retrieve (default: 50)

        Returns:
            str: Formatted markdown string containing message information
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def get_user_info_formatted(self, user_id: str) -> str:
        """
        Get formatted information about a Discord user.

        Args:
            user_id: The Discord user ID

        Returns:
            str: Formatted markdown string containing user information
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def send_message(
        self, channel_id: str, content: str, reply_to_message_id: Optional[str] = None
    ) -> str:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: The Discord channel ID to send the message to
            content: The message content to send
            reply_to_message_id: Optional message ID to reply to

        Returns:
            str: Success message with the sent message ID, or error message
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def send_direct_message(self, user_id: str, content: str) -> str:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the DM to
            content: The message content to send

        Returns:
            str: Success message with the sent message ID, or error message
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def read_direct_messages(self, user_id: str, limit: int = 10) -> str:
        """
        Read direct messages from a DM channel with a specific user.

        Args:
            user_id: The Discord user ID to read DMs with
            limit: Maximum number of messages to retrieve (default: 10, max: 100)

        Returns:
            str: Formatted list of direct messages or error message
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def delete_message(self, channel_id: str, message_id: str) -> str:
        """
        Delete a message from a Discord channel.

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to delete

        Returns:
            str: Success message or error message
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    async def edit_message(
        self, channel_id: str, message_id: str, new_content: str
    ) -> str:
        """
        Edit a message in a Discord channel (only works for bot's own messages).

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to edit
            new_content: The new content for the message

        Returns:
            str: Success message or error message
        """
        # Implementation will be added in the next phase
        raise NotImplementedError("Method implementation pending")

    # Private helper methods for error handling and permission validation
    # These will be implemented in the next tasks

    def _handle_discord_error(self, error: DiscordAPIError, operation: str) -> str:
        """
        Centralized error handling for Discord API errors.

        Args:
            error: The Discord API error that occurred
            operation: Description of the operation that failed

        Returns:
            str: Formatted error message for user display
        """
        error_msg = f"Discord API error while {operation}: {str(error)}"
        self._logger.error(
            f"Discord API error in {operation}",
            error=str(error),
            status_code=getattr(error, "status_code", None),
            operation=operation,
        )
        return f"# Error\n\n{error_msg}"

    def _handle_unexpected_error(self, error: Exception, operation: str) -> str:
        """
        Centralized error handling for unexpected errors.

        Args:
            error: The unexpected error that occurred
            operation: Description of the operation that failed

        Returns:
            str: Formatted error message for user display
        """
        error_msg = f"Unexpected error while {operation}: {str(error)}"
        self._logger.error(
            f"Unexpected error in {operation}",
            error=str(error),
            error_type=type(error).__name__,
            operation=operation,
        )
        return f"# Error\n\n{error_msg}"

    def _validate_guild_permission(self, guild_id: str) -> bool:
        """
        Validate if the bot has permission to access a specific guild.

        Args:
            guild_id: The Discord guild ID to validate

        Returns:
            bool: True if access is allowed, False otherwise
        """
        return self._settings.is_guild_allowed(guild_id)

    def _validate_channel_permission(self, channel_id: str) -> bool:
        """
        Validate if the bot has permission to access a specific channel.

        Args:
            channel_id: The Discord channel ID to validate

        Returns:
            bool: True if access is allowed, False otherwise
        """
        return self._settings.is_channel_allowed(channel_id)

    def _check_allowed_guilds(self, guild_id: str) -> bool:
        """
        Check if a guild is in the allowed guilds list.

        Args:
            guild_id: The Discord guild ID to check

        Returns:
            bool: True if guild is allowed, False otherwise
        """
        return self._settings.is_guild_allowed(guild_id)

    def _check_allowed_channels(self, channel_id: str) -> bool:
        """
        Check if a channel is in the allowed channels list.

        Args:
            channel_id: The Discord channel ID to check

        Returns:
            bool: True if channel is allowed, False otherwise
        """
        return self._settings.is_channel_allowed(channel_id)

    def _get_guild_permission_denied_message(self, guild_id: str) -> str:
        """
        Get formatted permission denied message for guild access.

        Args:
            guild_id: The Discord guild ID that was denied

        Returns:
            str: Formatted permission denied message
        """
        return f"# Access Denied\n\nAccess to guild `{guild_id}` is not permitted."

    def _get_channel_permission_denied_message(self, channel_id: str) -> str:
        """
        Get formatted permission denied message for channel access.

        Args:
            channel_id: The Discord channel ID that was denied

        Returns:
            str: Formatted permission denied message
        """
        return f"# Access Denied\n\nAccess to channel `{channel_id}` is not permitted."

    def _get_guild_containing_channel_permission_denied_message(
        self, channel_id: str
    ) -> str:
        """
        Get formatted permission denied message for guild containing channel.

        Args:
            channel_id: The Discord channel ID whose guild was denied

        Returns:
            str: Formatted permission denied message
        """
        return f"# Access Denied\n\nAccess to guild containing channel `{channel_id}` is not permitted."
