"""
Discord Service Interface Definition.

This module defines the abstract interface for Discord operations,
providing a contract that the concrete DiscordService must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IDiscordService(ABC):
    """
    Abstract interface for Discord service operations.

    This interface defines all the Discord operations that can be performed
    through the service layer, providing a clean abstraction over the Discord API.
    """

    @abstractmethod
    async def get_guilds_formatted(self) -> str:
        """
        Get a formatted list of accessible Discord guilds.

        Returns:
            str: Formatted markdown string containing guild information
        """
        pass

    @abstractmethod
    async def get_channels_formatted(self, guild_id: str) -> str:
        """
        Get a formatted list of channels in a specific Discord guild.

        Args:
            guild_id: The Discord guild (server) ID

        Returns:
            str: Formatted markdown string containing channel information
        """
        pass

    @abstractmethod
    async def get_messages_formatted(
            self, channel_id: str, limit: int = 50) -> str:
        """
        Get a formatted list of recent messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID
            limit: Maximum number of messages to retrieve (default: 50)

        Returns:
            str: Formatted markdown string containing message information
        """
        pass

    @abstractmethod
    async def get_user_info_formatted(self, user_id: str) -> str:
        """
        Get formatted information about a Discord user.

        Args:
            user_id: The Discord user ID

        Returns:
            str: Formatted markdown string containing user information
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def send_direct_message(self, user_id: str, content: str) -> str:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the DM to
            content: The message content to send

        Returns:
            str: Success message with the sent message ID, or error message
        """
        pass

    @abstractmethod
    async def read_direct_messages(self, user_id: str, limit: int = 10) -> str:
        """
        Read direct messages from a DM channel with a specific user.

        Args:
            user_id: The Discord user ID to read DMs with
            limit: Maximum number of messages to retrieve (default: 10, max: 100)

        Returns:
            str: Formatted list of direct messages or error message
        """
        pass

    @abstractmethod
    async def delete_message(self, channel_id: str, message_id: str) -> str:
        """
        Delete a message from a Discord channel.

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to delete

        Returns:
            str: Success message or error message
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def timeout_user(
        self,
        guild_id: str,
        user_id: str,
        duration_minutes: int,
        reason: Optional[str] = None,
    ) -> str:
        """
        Timeout a user in a Discord server for a specified duration.

        Args:
            guild_id: The Discord guild (server) ID
            user_id: The Discord user ID to timeout
            duration_minutes: Duration of timeout in minutes (1-40320, max 28 days)
            reason: Optional reason for the timeout

        Returns:
            str: Success message with timeout details or error message
        """
        pass

    @abstractmethod
    async def untimeout_user(
        self, guild_id: str, user_id: str, reason: Optional[str] = None
    ) -> str:
        """
        Remove timeout from a user in a Discord server.

        Args:
            guild_id: The Discord guild (server) ID
            user_id: The Discord user ID to remove timeout from
            reason: Optional reason for removing the timeout

        Returns:
            str: Success message or error message
        """
        pass

    @abstractmethod
    async def kick_user(
        self, guild_id: str, user_id: str, reason: Optional[str] = None
    ) -> str:
        """
        Kick a user from a Discord server.

        Args:
            guild_id: The Discord guild (server) ID
            user_id: The Discord user ID to kick
            reason: Optional reason for the kick

        Returns:
            str: Success message or error message
        """
        pass

    @abstractmethod
    async def ban_user(
        self,
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None,
        delete_message_days: int = 0,
    ) -> str:
        """
        Ban a user from a Discord server with optional message deletion.

        Args:
            guild_id: The Discord guild (server) ID
            user_id: The Discord user ID to ban
            reason: Optional reason for the ban
            delete_message_days: Number of days of messages to delete (0-7, default: 0)

        Returns:
            str: Success message or error message
        """
        pass
