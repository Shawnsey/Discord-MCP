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
        try:
            self._logger.info("Fetching guild list")

            # Get guilds from Discord API
            guilds = await self._discord_client.get_user_guilds()

            # Filter guilds based on settings
            if self._settings.get_allowed_guilds_set():
                allowed_guilds = self._settings.get_allowed_guilds_set()
                guilds = [g for g in guilds if g["id"] in allowed_guilds]
                self._logger.info(
                    "Filtered guilds by allowed list",
                    total_guilds=len(guilds),
                    allowed_count=len(allowed_guilds),
                )

            if not guilds:
                return "# Discord Guilds\n\nNo guilds found or bot has no access to any guilds."

            # Format guild information
            guild_info = []
            guild_info.append("# Discord Guilds")
            guild_info.append(f"\nFound {len(guilds)} accessible guild(s):\n")

            for guild in guilds:
                guild_info.append(f"## {guild['name']}")
                guild_info.append(f"- **ID**: `{guild['id']}`")
                guild_info.append(
                    f"- **Owner**: {'Yes' if guild.get('owner') else 'No'}"
                )

                # Get additional guild details
                try:
                    guild_details = await self._discord_client.get_guild(guild["id"])
                    guild_info.append(
                        f"- **Member Count**: {guild_details.get('approximate_member_count', 'Unknown')}"
                    )
                    guild_info.append(
                        f"- **Description**: {guild_details.get('description') or 'None'}"
                    )

                    # Add features if any
                    features = guild_details.get("features", [])
                    if features:
                        guild_info.append(f"- **Features**: {', '.join(features)}")

                except DiscordAPIError as e:
                    self._logger.warning(
                        "Failed to get guild details",
                        guild_id=guild["id"],
                        error=str(e),
                    )
                    guild_info.append("- **Details**: Unable to fetch additional details")

                guild_info.append("")  # Empty line between guilds

            result = "\n".join(guild_info)
            self._logger.info("Guild list retrieved successfully", guild_count=len(guilds))
            return result

        except DiscordAPIError as e:
            return self._handle_discord_error(e, "fetching guilds")
        except Exception as e:
            return self._handle_unexpected_error(e, "fetching guilds")

    async def get_channels_formatted(self, guild_id: str) -> str:
        """
        Get a formatted list of channels in a specific Discord guild.

        Args:
            guild_id: The Discord guild (server) ID

        Returns:
            str: Formatted markdown string containing channel information
        """
        try:
            self._logger.info("Fetching channel list", guild_id=guild_id)

            # Check if guild is allowed
            if not self._validate_guild_permission(guild_id):
                return self._get_guild_permission_denied_message(guild_id)

            # Get guild information first
            try:
                guild = await self._discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"# Guild Not Found\n\nGuild with ID `{guild_id}` was not found or bot has no access."
                raise

            # Get channels from Discord API
            channels = await self._discord_client.get_guild_channels(guild_id)

            # Filter channels based on settings
            if self._settings.get_allowed_channels_set():
                allowed_channels = self._settings.get_allowed_channels_set()
                channels = [c for c in channels if c["id"] in allowed_channels]
                self._logger.info(
                    "Filtered channels by allowed list",
                    total_channels=len(channels),
                    allowed_count=len(allowed_channels),
                )

            if not channels:
                return f"# Channels in {guild_name}\n\nNo accessible channels found in this guild."

            # Group channels by type
            channel_types = {
                0: "Text Channels",
                2: "Voice Channels",
                4: "Categories",
                5: "Announcement Channels",
                10: "Announcement Threads",
                11: "Public Threads",
                12: "Private Threads",
                13: "Stage Channels",
                15: "Forum Channels",
            }

            grouped_channels = {}
            for channel in channels:
                channel_type = channel.get("type", 0)
                type_name = channel_types.get(channel_type, f"Type {channel_type}")

                if type_name not in grouped_channels:
                    grouped_channels[type_name] = []
                grouped_channels[type_name].append(channel)

            # Format channel information
            channel_info = []
            channel_info.append(f"# Channels in {guild_name}")
            channel_info.append(f"\nFound {len(channels)} accessible channel(s):\n")

            for type_name, type_channels in grouped_channels.items():
                channel_info.append(f"## {type_name}")

                for channel in type_channels:
                    channel_info.append(f"### {channel['name']}")
                    channel_info.append(f"- **ID**: `{channel['id']}`")
                    channel_info.append(f"- **Type**: {channel.get('type', 0)}")

                    if channel.get("topic"):
                        channel_info.append(f"- **Topic**: {channel['topic']}")

                    if channel.get("parent_id"):
                        channel_info.append(f"- **Category**: {channel['parent_id']}")

                    # Add position info
                    if "position" in channel:
                        channel_info.append(f"- **Position**: {channel['position']}")

                    # Add NSFW flag for text channels
                    if channel.get("nsfw"):
                        channel_info.append("- **NSFW**: Yes")

                    channel_info.append("")  # Empty line between channels

            result = "\n".join(channel_info)
            self._logger.info(
                "Channel list retrieved successfully",
                guild_id=guild_id,
                channel_count=len(channels),
            )
            return result

        except DiscordAPIError as e:
            return self._handle_discord_error(e, "fetching channels")
        except Exception as e:
            return self._handle_unexpected_error(e, "fetching channels")

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
