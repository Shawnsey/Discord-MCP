"""
Content Formatter Service.

This module provides the ContentFormatter class that handles all Discord content
formatting operations. It is responsible for converting Discord API data structures
into formatted markdown strings for display, operating independently of Discord API
clients and focusing solely on presentation logic.
"""

from typing import Optional

from ..config import Settings


class ContentFormatter:
    """
    Handles all Discord content formatting operations.

    This class is responsible for converting Discord API data structures
    into formatted markdown strings for display. It operates independently
    of Discord API clients and focuses solely on presentation logic.

    The ContentFormatter provides a clean separation between business logic
    (handled by DiscordService) and presentation logic (handled here),
    improving testability, maintainability, and reusability.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Initialize the content formatter.

        Args:
            settings: Optional settings for formatting configuration.
                     If not provided, default formatting behavior will be used.
        """
        self._settings = settings

    def format_guild_info(self, guilds: list) -> str:
        """
        Format guild information into a consistent markdown structure.

        This method formats guild data into markdown without requiring Discord API calls.
        It handles empty guild lists and missing data gracefully by providing sensible
        defaults and fallback values.

        Args:
            guilds: List of guild dictionaries from Discord API

        Returns:
            str: Formatted markdown string containing guild information
        """
        if not guilds:
            return "# Discord Guilds\n\nNo guilds found or bot has no access to any guilds."

        guild_info = ["# Discord Guilds", f"Found {len(guilds)} guild(s):\n"]

        for i, guild in enumerate(guilds, 1):
            guild_id = guild.get("id", "Unknown")
            guild_name = guild.get("name", "Unknown Guild")
            member_count = guild.get("approximate_member_count", "Unknown")
            owner = guild.get("owner", False)
            permissions = guild.get("permissions", "0")

            guild_info.append(f"## {i}. {guild_name}")
            guild_info.append(f"- **Guild ID**: `{guild_id}`")
            guild_info.append(f"- **Members**: {member_count}")
            guild_info.append(
                f"- **Bot is Owner**: {'Yes' if owner else 'No'}")
            guild_info.append(f"- **Permissions**: `{permissions}`")

            # Add features if available
            features = guild.get("features", [])
            if features:
                guild_info.append(f"- **Features**: {', '.join(features[:5])}")
                if len(features) > 5:
                    guild_info.append(f"  (and {len(features) - 5} more)")

            guild_info.append("")  # Empty line between guilds

        return "\n".join(guild_info)

    def format_channel_info(self, channels: list, guild_name: str) -> str:
        """
        Format channel information into a consistent markdown structure.

        This method centralizes channel formatting logic to ensure consistent
        output across all operations that display channel information.

        Args:
            channels: List of channel dictionaries from Discord API
            guild_name: Name of the guild containing these channels

        Returns:
            str: Formatted markdown string containing channel information
        """
        if not channels:
            return f"# Channels in {guild_name}\n\nNo accessible channels found in this guild."

        # Group channels by type
        channel_types = {}
        for channel in channels:
            channel_type = channel.get("type", 0)
            type_name = {
                0: "Text Channels",
                2: "Voice Channels",
                4: "Categories",
                5: "Announcement Channels",
                13: "Stage Channels",
                15: "Forum Channels",
            }.get(channel_type, "Other Channels")

            if type_name not in channel_types:
                channel_types[type_name] = []
            channel_types[type_name].append(channel)

        channel_info = [
            f"# Channels in {guild_name}",
            f"Found {len(channels)} channel(s):\n",
        ]

        # Display channels grouped by type
        for type_name, type_channels in channel_types.items():
            channel_info.append(f"## {type_name}")

            for channel in type_channels:
                channel_id = channel.get("id", "Unknown")
                channel_name = channel.get("name", "Unknown Channel")
                topic = channel.get("topic", "")
                nsfw = channel.get("nsfw", False)

                channel_info.append(f"- **#{channel_name}** (`{channel_id}`)")
                if topic:
                    truncated_topic = self.truncate_content(topic, 100)
                    channel_info.append(f"  - Topic: {truncated_topic}")
                if nsfw:
                    channel_info.append("  - 🔞 NSFW Channel")

            channel_info.append("")  # Empty line between types

        return "\n".join(channel_info)

    def format_message_info(self, messages: list, channel_name: str) -> str:
        """
        Format message information into a consistent markdown structure.

        This method centralizes message formatting logic to ensure consistent
        output across all operations that display message information.

        Args:
            messages: List of message dictionaries from Discord API
            channel_name: Name of the channel containing these messages

        Returns:
            str: Formatted markdown string containing message information
        """
        if not messages:
            return (
                f"# Messages in #{channel_name}\n\nNo messages found in this channel."
            )

        message_info = [
            f"# Messages in #{channel_name}",
            f"Retrieved {len(messages)} message(s):\n",
            "=" * 60 + "\n",
        ]

        for i, message in enumerate(messages, 1):
            author = message.get("author", {})
            author_name = self.format_user_display_name(author)
            content = message.get("content", "(no text content)")
            timestamp = self.format_timestamp(message.get("timestamp", ""))
            message_id = message.get("id", "Unknown")

            message_info.append(f"**{i:2d}.** [{timestamp}] {author_name}")
            message_info.append(f"     Message ID: `{message_id}`")

            # Handle message content
            if content and content.strip():
                formatted_content = self.truncate_content(content, 500)
                message_info.append(f"     💬 {formatted_content}")
            else:
                message_info.append("     💬 (no text content)")

            # Check for embeds
            embeds = message.get("embeds", [])
            if embeds:
                message_info.append(f"     📎 {len(embeds)} embed(s)")

            # Check for attachments
            attachments = message.get("attachments", [])
            if attachments:
                message_info.append(f"     📁 {len(attachments)} attachment(s)")

            # Check for reactions
            reactions = message.get("reactions", [])
            if reactions:
                message_info.append(f"     ⭐ {len(reactions)} reaction(s)")

            message_info.append("")  # Empty line between messages

        return "\n".join(message_info)

    def format_user_info(self, user: dict, user_id: str = None) -> str:
        """
        Format user information into a consistent markdown structure.

        This method centralizes user info formatting logic to ensure consistent
        output across all operations that display user information.

        Args:
            user: User dictionary from Discord API
            user_id: Optional user ID if not available in user dict

        Returns:
            str: Formatted markdown string containing user information
        """
        user_id = user.get("id", user_id or "Unknown")
        username = user.get("username", "Unknown User")
        discriminator = user.get("discriminator", "0000")
        display_name = self.format_user_display_name(user)

        user_info = [
            f"# User Information: {display_name}",
            f"- **User ID**: `{user_id}`",
            f"- **Username**: {username}",
        ]

        # Add discriminator if not the new format
        if discriminator != "0":
            user_info.append(f"- **Discriminator**: #{discriminator}")

        # Add global display name if available
        global_name = user.get("global_name")
        if global_name and global_name != username:
            user_info.append(f"- **Display Name**: {global_name}")

        # Add bot status
        is_bot = user.get("bot", False)
        user_info.append(f"- **Bot Account**: {'Yes' if is_bot else 'No'}")

        # Add system status
        is_system = user.get("system", False)
        if is_system:
            user_info.append("- **System Account**: Yes")

        # Add verification status
        verified = user.get("verified")
        if verified is not None:
            user_info.append(f"- **Verified**: {'Yes' if verified else 'No'}")

        # Add avatar information
        avatar = user.get("avatar")
        if avatar:
            user_info.append("- **Has Avatar**: Yes")

        # Add account creation date if we can calculate it
        try:
            from datetime import datetime, timezone

            # Discord snowflake epoch (January 1, 2015)
            discord_epoch = 1420070400000
            timestamp = ((int(user_id) >> 22) + discord_epoch) / 1000
            created_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            user_info.append(
                f"- **Account Created**: {
                    created_date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
        except (ValueError, TypeError):
            pass  # Skip if we can't calculate the date

        return "\n".join(user_info)

    def format_user_display_name(self, user: dict) -> str:
        """
        Format a consistent user display name from user data.

        Args:
            user: Discord user object containing user information

        Returns:
            str: Formatted display name following Discord's naming conventions
        """
        if not user:
            return "@Unknown User"

        username = user.get("username", "Unknown User")
        global_name = user.get("global_name")
        discriminator = user.get("discriminator", "0")

        # Handle new Discord username system (no discriminator) vs legacy
        # system
        if discriminator == "0" or discriminator == "0000":
            # New system: use global_name if available, otherwise username
            if global_name and global_name != username:
                return f"{global_name} (@{username})"
            else:
                return f"@{username}"
        else:
            # Legacy system: use username#discriminator format
            if global_name and global_name != username:
                return f"{global_name} ({username}#{discriminator})"
            else:
                return f"{username}#{discriminator}"

    def format_timestamp(self, timestamp: str) -> str:
        """
        Format a Discord timestamp string into a consistent, readable format.

        Args:
            timestamp: ISO timestamp string from Discord API

        Returns:
            str: Formatted timestamp string in a consistent format
        """
        if not timestamp:
            return "Unknown time"

        # Convert non-string input to string
        if not isinstance(timestamp, str):
            timestamp = str(timestamp)

        try:
            from datetime import datetime

            # Handle various timestamp formats
            if timestamp.endswith("Z"):
                # ISO format with Z suffix
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif "+" in timestamp or timestamp.endswith("UTC"):
                # Already has timezone info
                dt = datetime.fromisoformat(
                    timestamp.replace("UTC", "").strip())
            else:
                # Assume UTC if no timezone info
                dt = datetime.fromisoformat(timestamp)

            # Format as consistent string
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, AttributeError):
            # Note: In a standalone ContentFormatter, we don't have access to logger
            # This preserves the exact behavior from DiscordService but without logging
            # The calling service can handle logging if needed
            return timestamp

    def truncate_content(self, content: str, max_length: int = 100) -> str:
        """
        Truncate content to a specified maximum length with ellipsis.

        Args:
            content: The content string to truncate
            max_length: Maximum length before truncation (default: 100)

        Returns:
            str: Truncated content with ellipsis if needed
        """
        if not content:
            return ""

        content = str(content).strip()

        if len(content) <= max_length:
            return content

        # Handle edge case where max_length is too small for ellipsis
        if max_length <= 3:
            return "..."

        # Truncate and add ellipsis
        return content[: max_length - 3] + "..."
