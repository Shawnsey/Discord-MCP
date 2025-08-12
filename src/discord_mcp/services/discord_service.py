"""
Discord Service Implementation.

This module provides the concrete implementation of the IDiscordService interface,
centralizing all Discord API operations and eliminating code duplication between
tools and resources.
"""

from datetime import datetime, timedelta
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
                    guild_info.append(
                        "- **Details**: Unable to fetch additional details"
                    )

                guild_info.append("")  # Empty line between guilds

            result = "\n".join(guild_info)
            self._logger.info(
                "Guild list retrieved successfully", guild_count=len(guilds)
            )
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
        try:
            self._logger.info("Fetching messages", channel_id=channel_id, limit=limit)

            # Validate channel permission
            if not self._validate_channel_permission(channel_id):
                return f"# Access Denied\n\nAccess to channel `{channel_id}` is not permitted."

            # Get channel information first
            try:
                channel = await self._discord_client.get_channel(channel_id)
                channel_name = channel["name"]
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not self._validate_guild_permission(guild_id):
                    return f"# Access Denied\n\nAccess to guild containing channel `{channel_id}` is not permitted."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"# Channel Not Found\n\nChannel with ID `{channel_id}` was not found or bot has no access."
                raise

            # Get messages from Discord API
            messages = await self._discord_client.get_channel_messages(
                channel_id, limit=limit
            )

            if not messages:
                return f"# Messages in #{channel_name}\n\nNo messages found in this channel."

            # Format message information
            message_info = []
            message_info.append(f"# Messages in #{channel_name}")
            message_info.append(f"\nShowing {len(messages)} recent message(s):\n")

            # Messages are returned in reverse chronological order, so reverse to show oldest first
            messages.reverse()

            for message in messages:
                author = message.get("author", {})
                timestamp = message.get("timestamp", "")
                content = message.get("content", "")

                # Format timestamp
                if timestamp:
                    # Convert ISO timestamp to readable format
                    from datetime import datetime

                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except:
                        formatted_time = timestamp
                else:
                    formatted_time = "Unknown time"

                message_info.append(
                    f"## Message from {author.get('username', 'Unknown User')}"
                )
                message_info.append(
                    f"- **Author**: {author.get('username', 'Unknown')} (`{author.get('id', 'Unknown')}`)"
                )
                message_info.append(f"- **Time**: {formatted_time}")
                message_info.append(
                    f"- **Message ID**: `{message.get('id', 'Unknown')}`"
                )

                if content:
                    message_info.append(f"- **Content**:")
                    message_info.append(f"  ```")
                    message_info.append(f"  {content}")
                    message_info.append(f"  ```")
                else:
                    message_info.append("- **Content**: *(No text content)*")

                # Add attachment info if any
                attachments = message.get("attachments", [])
                if attachments:
                    message_info.append(
                        f"- **Attachments**: {len(attachments)} file(s)"
                    )
                    for attachment in attachments:
                        message_info.append(
                            f"  - {attachment.get('filename', 'Unknown file')}"
                        )

                # Add embed info if any
                embeds = message.get("embeds", [])
                if embeds:
                    message_info.append(f"- **Embeds**: {len(embeds)} embed(s)")

                message_info.append("")  # Empty line between messages

            result = "\n".join(message_info)
            self._logger.info(
                "Messages retrieved successfully",
                channel_id=channel_id,
                message_count=len(messages),
            )
            return result

        except DiscordAPIError as e:
            return self._handle_discord_error(e, "fetching messages")
        except Exception as e:
            return self._handle_unexpected_error(e, "fetching messages")

    async def get_user_info_formatted(self, user_id: str) -> str:
        """
        Get formatted information about a Discord user.

        Args:
            user_id: The Discord user ID

        Returns:
            str: Formatted markdown string containing user information
        """
        try:
            self._logger.info("Fetching user info", user_id=user_id)

            # Get user information from Discord API
            try:
                user = await self._discord_client.get_user(user_id)
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return (
                        f"# User Not Found\n\nUser with ID `{user_id}` was not found."
                    )
                raise

            # Format user information
            user_info = []
            user_info.append(f"# User: {user.get('username', 'Unknown')}")
            user_info.append("")

            user_info.append(f"- **Username**: {user.get('username', 'Unknown')}")
            user_info.append(f"- **User ID**: `{user.get('id', user_id)}`")

            # Add discriminator if it exists (legacy Discord usernames)
            if user.get("discriminator") and user.get("discriminator") != "0":
                user_info.append(f"- **Discriminator**: #{user['discriminator']}")

            # Add display name if different from username
            if user.get("global_name") and user.get("global_name") != user.get(
                "username"
            ):
                user_info.append(f"- **Display Name**: {user['global_name']}")

            # Add bot status
            if user.get("bot"):
                user_info.append("- **Type**: Bot")
            else:
                user_info.append("- **Type**: User")

            # Add system user status
            if user.get("system"):
                user_info.append("- **System User**: Yes")

            # Add avatar information
            if user.get("avatar"):
                avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"
                user_info.append(f"- **Avatar**: [View Avatar]({avatar_url})")
            else:
                user_info.append("- **Avatar**: Default avatar")

            # Add banner if available
            if user.get("banner"):
                banner_url = f"https://cdn.discordapp.com/banners/{user['id']}/{user['banner']}.png"
                user_info.append(f"- **Banner**: [View Banner]({banner_url})")

            # Add accent color if available
            if user.get("accent_color"):
                user_info.append(f"- **Accent Color**: #{user['accent_color']:06x}")

            # Add public flags if available
            if user.get("public_flags"):
                user_info.append(f"- **Public Flags**: {user['public_flags']}")

            result = "\n".join(user_info)
            self._logger.info("User info retrieved successfully", user_id=user_id)
            return result

        except DiscordAPIError as e:
            return self._handle_discord_error(e, "fetching user info")
        except Exception as e:
            return self._handle_unexpected_error(e, "fetching user info")

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
        try:
            self._logger.info(
                "Sending message to channel",
                channel_id=channel_id,
                content_length=len(content),
                reply_to=reply_to_message_id,
            )

            # Validate inputs
            if not content or not content.strip():
                return "❌ Error: Message content cannot be empty."

            if len(content) > 2000:
                return f"❌ Error: Message content too long ({len(content)} characters). Discord limit is 2000 characters."

            # Check if channel is allowed
            if not self._validate_channel_permission(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access and get guild info
            try:
                channel = await self._discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not self._validate_guild_permission(guild_id):
                    return f"❌ Error: Access to guild containing channel `{channel_id}` is not permitted."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Channel `{channel_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access channel `{channel_id}`."
                else:
                    return f"❌ Error: Failed to access channel: {str(e)}"

            # Prepare message data
            message_data = {}
            if reply_to_message_id:
                message_data["message_reference"] = {
                    "message_id": reply_to_message_id,
                    "channel_id": channel_id,
                }

            # Send the message
            try:
                result = await self._discord_client.send_message(
                    channel_id=channel_id,
                    content=content,
                    message_reference=message_data.get("message_reference"),
                )

                message_id = result.get("id")
                timestamp = result.get("timestamp", "")

                success_msg = f"✅ Message sent successfully to #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Content**: {content[:100]}{'...' if len(content) > 100 else ''}"
                if reply_to_message_id:
                    success_msg += f"\n- **Reply to**: `{reply_to_message_id}`"
                if timestamp:
                    success_msg += f"\n- **Sent at**: {timestamp}"

                self._logger.info(
                    "Message sent successfully",
                    channel_id=channel_id,
                    message_id=message_id,
                    reply_to=reply_to_message_id,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to send messages in #{channel_name}."
                elif e.status_code == 404:
                    if reply_to_message_id:
                        return f"❌ Error: Reply target message `{reply_to_message_id}` not found."
                    else:
                        return f"❌ Error: Channel `{channel_id}` not found."
                else:
                    return f"❌ Error: Failed to send message: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while sending message: {str(e)}"
            self._logger.error(
                "Unexpected error in send_message", channel_id=channel_id, error=str(e)
            )
            return error_msg

    async def send_direct_message(self, user_id: str, content: str) -> str:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the DM to
            content: The message content to send

        Returns:
            str: Success message with the sent message ID, or error message
        """
        try:
            self._logger.info(
                "Sending DM to user", user_id=user_id, content_length=len(content)
            )

            # Validate inputs
            if not content or not content.strip():
                return "❌ Error: Message content cannot be empty."

            if len(content) > 2000:
                return f"❌ Error: Message content too long ({len(content)} characters). Discord limit is 2000 characters."

            # Get user information to validate and get username
            try:
                user = await self._discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")

                # Check if user is a bot (some bots don't accept DMs)
                if (
                    user.get("bot")
                    and user.get("id") != self._settings.discord_application_id
                ):
                    self._logger.warning(
                        "Attempting to DM another bot",
                        user_id=user_id,
                        username=username,
                    )

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Send the DM
            try:
                result = await self._discord_client.send_dm(user_id, content)

                message_id = result.get("id")
                timestamp = result.get("timestamp", "")

                success_msg = f"✅ Direct message sent successfully to {username}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Recipient**: {username} (`{user_id}`)"
                success_msg += f"\n- **Content**: {content[:100]}{'...' if len(content) > 100 else ''}"
                if timestamp:
                    success_msg += f"\n- **Sent at**: {timestamp}"

                self._logger.info(
                    "DM sent successfully",
                    user_id=user_id,
                    username=username,
                    message_id=message_id,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Cannot send DM to {username}. User may have DMs disabled or blocked the bot."
                elif e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found or cannot create DM channel."
                else:
                    return f"❌ Error: Failed to send DM: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while sending DM: {str(e)}"
            self._logger.error(
                "Unexpected error in send_direct_message", user_id=user_id, error=str(e)
            )
            return error_msg

    async def read_direct_messages(self, user_id: str, limit: int = 10) -> str:
        """
        Read direct messages from a DM channel with a specific user.

        Args:
            user_id: The Discord user ID to read DMs with
            limit: Maximum number of messages to retrieve (default: 10, max: 100)

        Returns:
            str: Formatted list of direct messages or error message
        """
        try:
            self._logger.info("Reading direct messages", user_id=user_id, limit=limit)

            # Validate inputs
            if limit < 1 or limit > 100:
                return "❌ Error: Limit must be between 1 and 100."

            # Get user information
            try:
                user_info = await self._discord_client.get_user(user_id)
                username = user_info.get("username", "Unknown")
                discriminator = user_info.get("discriminator", "0000")
                if discriminator != "0000":
                    display_name = f"{username}#{discriminator}"
                else:
                    display_name = username

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Create or get existing DM channel
            try:
                dm_channel = await self._discord_client.create_dm_channel(user_id)
                dm_channel_id = dm_channel["id"]

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Cannot create DM channel with {display_name}. User may have DMs disabled."
                else:
                    return f"❌ Error: Failed to create DM channel: {str(e)}"

            # Get messages from the DM channel
            try:
                messages = await self._discord_client.get_channel_messages(
                    dm_channel_id, limit=limit
                )

                if not messages:
                    return f"📭 No direct messages found with {display_name}."

                # Format the messages
                result = f"📬 **Direct Messages with {display_name}** (User ID: `{user_id}`)\n"
                result += f"DM Channel ID: `{dm_channel_id}`\n"
                result += f"Retrieved {len(messages)} message(s)\n\n"
                result += "=" * 60 + "\n\n"

                # Get bot user ID to identify bot messages
                try:
                    bot_user = await self._discord_client.get_current_user()
                    bot_user_id = bot_user["id"]
                    bot_username = bot_user.get("username", "Bot")
                except:
                    bot_user_id = None
                    bot_username = "Bot"

                for i, message in enumerate(messages, 1):
                    author = message.get("author", {})
                    author_id = author.get("id", "Unknown")
                    author_name = author.get("username", "Unknown")
                    content = message.get("content", "(no text content)")
                    timestamp = message.get("timestamp", "")[:19].replace("T", " ")
                    message_id = message.get("id", "Unknown")

                    # Determine if it's from bot or user
                    if author_id == bot_user_id:
                        sender_label = f"🤖 {bot_username} (You)"
                    elif author_id == user_id:
                        sender_label = f"👤 {display_name}"
                    else:
                        sender_label = f"❓ {author_name}"

                    result += f"**{i:2d}.** [{timestamp}] {sender_label}\n"
                    result += f"     Message ID: `{message_id}`\n"

                    # Handle different content types
                    if content and content.strip():
                        # Truncate very long messages
                        if len(content) > 500:
                            content = content[:500] + "... (truncated)"
                        result += f"     💬 {content}\n"
                    else:
                        result += f"     💬 (no text content)\n"

                    # Check for embeds
                    embeds = message.get("embeds", [])
                    if embeds:
                        result += f"     📎 {len(embeds)} embed(s)\n"

                    # Check for attachments
                    attachments = message.get("attachments", [])
                    if attachments:
                        result += f"     📁 {len(attachments)} attachment(s): "
                        filenames = [
                            att.get("filename", "unknown") for att in attachments[:3]
                        ]
                        result += ", ".join(filenames)
                        if len(attachments) > 3:
                            result += f" and {len(attachments) - 3} more"
                        result += "\n"

                    # Check for reactions
                    reactions = message.get("reactions", [])
                    if reactions:
                        result += f"     ⭐ {len(reactions)} reaction(s)\n"

                    result += "\n"

                self._logger.info(
                    "Direct messages retrieved successfully",
                    user_id=user_id,
                    username=display_name,
                    message_count=len(messages),
                )

                return result

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to read DMs with {display_name}."
                else:
                    return f"❌ Error: Failed to read DM messages: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while reading direct messages: {str(e)}"
            self._logger.error(
                "Unexpected error in read_direct_messages",
                user_id=user_id,
                error=str(e),
            )
            return error_msg

    async def delete_message(self, channel_id: str, message_id: str) -> str:
        """
        Delete a message from a Discord channel.

        Args:
            channel_id: The Discord channel ID containing the message
            message_id: The Discord message ID to delete

        Returns:
            str: Success message or error message
        """
        try:
            self._logger.info(
                "Deleting message", channel_id=channel_id, message_id=message_id
            )

            # Check if channel is allowed
            if not self._validate_channel_permission(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access
            try:
                channel = await self._discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not self._validate_guild_permission(guild_id):
                    return f"❌ Error: Access to guild containing channel `{channel_id}` is not permitted."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Channel `{channel_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access channel `{channel_id}`."
                else:
                    return f"❌ Error: Failed to access channel: {str(e)}"

            # Get message information before deleting (for confirmation)
            try:
                message = await self._discord_client.get_channel_message(
                    channel_id, message_id
                )
                message_author = message.get("author", {}).get("username", "Unknown")
                message_content = message.get("content", "")[:50]
                if len(message.get("content", "")) > 50:
                    message_content += "..."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Message `{message_id}` not found in channel #{channel_name}."
                else:
                    # Continue with deletion attempt even if we can't get message details
                    message_author = "Unknown"
                    message_content = "Unknown content"

            # Delete the message
            try:
                await self._discord_client.delete_message(channel_id, message_id)

                success_msg = f"✅ Message deleted successfully from #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Author**: {message_author}"
                success_msg += f"\n- **Content**: {message_content}"

                self._logger.info(
                    "Message deleted successfully",
                    channel_id=channel_id,
                    message_id=message_id,
                    author=message_author,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to delete messages in #{channel_name}."
                elif e.status_code == 404:
                    return f"❌ Error: Message `{message_id}` not found in channel #{channel_name}."
                else:
                    return f"❌ Error: Failed to delete message: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while deleting message: {str(e)}"
            self._logger.error(
                "Unexpected error in delete_message",
                channel_id=channel_id,
                message_id=message_id,
                error=str(e),
            )
            return error_msg

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
        try:
            self._logger.info(
                "Editing message",
                channel_id=channel_id,
                message_id=message_id,
                new_content_length=len(new_content),
            )

            # Validate inputs
            if not new_content or not new_content.strip():
                return "❌ Error: New message content cannot be empty."

            if len(new_content) > 2000:
                return f"❌ Error: Message content too long ({len(new_content)} characters). Discord limit is 2000 characters."

            # Check if channel is allowed
            if not self._validate_channel_permission(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access
            try:
                channel = await self._discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not self._validate_guild_permission(guild_id):
                    return f"❌ Error: Access to guild containing channel `{channel_id}` is not permitted."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Channel `{channel_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access channel `{channel_id}`."
                else:
                    return f"❌ Error: Failed to access channel: {str(e)}"

            # Get current bot user ID to verify ownership
            try:
                bot_user = await self._discord_client.get_current_user()
                bot_user_id = bot_user["id"]
            except DiscordAPIError as e:
                return f"❌ Error: Failed to get bot user information: {str(e)}"

            # Get message information to verify ownership
            try:
                message = await self._discord_client.get_channel_message(
                    channel_id, message_id
                )
                message_author_id = message.get("author", {}).get("id")
                old_content = message.get("content", "")

                if message_author_id != bot_user_id:
                    return f"❌ Error: Can only edit bot's own messages. This message was sent by another user."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Message `{message_id}` not found in channel #{channel_name}."
                else:
                    return f"❌ Error: Failed to get message information: {str(e)}"

            # Edit the message using PATCH request
            try:
                result = await self._discord_client.patch(
                    f"/channels/{channel_id}/messages/{message_id}",
                    data={"content": new_content},
                )

                success_msg = f"✅ Message edited successfully in #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Old Content**: {old_content[:50]}{'...' if len(old_content) > 50 else ''}"
                success_msg += f"\n- **New Content**: {new_content[:50]}{'...' if len(new_content) > 50 else ''}"

                self._logger.info(
                    "Message edited successfully",
                    channel_id=channel_id,
                    message_id=message_id,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to edit messages in #{channel_name}."
                elif e.status_code == 404:
                    return f"❌ Error: Message `{message_id}` not found in channel #{channel_name}."
                else:
                    return f"❌ Error: Failed to edit message: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while editing message: {str(e)}"
            self._logger.error(
                "Unexpected error in edit_message",
                channel_id=channel_id,
                message_id=message_id,
                error=str(e),
            )
            return error_msg

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

    async def timeout_user(
        self, guild_id: str, user_id: str, duration_minutes: int, reason: Optional[str] = None
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
        try:
            self._logger.info(
                "Timing out user",
                guild_id=guild_id,
                user_id=user_id,
                duration_minutes=duration_minutes,
                reason=reason,
            )

            # Input validation for duration (1 minute to 28 days maximum)
            if duration_minutes < 1:
                return "❌ Error: Timeout duration must be at least 1 minute."
            
            max_duration_minutes = 28 * 24 * 60  # 28 days in minutes (40320)
            if duration_minutes > max_duration_minutes:
                return f"❌ Error: Timeout duration cannot exceed 28 days ({max_duration_minutes} minutes). Provided: {duration_minutes} minutes."

            # Check if guild is allowed
            if not self._validate_guild_permission(guild_id):
                return self._get_guild_permission_denied_message(guild_id)

            # Get guild information to validate access and get guild name
            try:
                guild = await self._discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Guild `{guild_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access guild `{guild_id}`."
                else:
                    return f"❌ Error: Failed to access guild: {str(e)}"

            # Get user information to validate and get username
            try:
                user = await self._discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")
                display_name = user.get("global_name") or username
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Validate role hierarchy before attempting moderation action
            hierarchy_error = await self._validate_role_hierarchy(
                guild_id, user_id, guild_name, display_name
            )
            if hierarchy_error:
                return hierarchy_error

            # Calculate timeout end time using datetime and timedelta
            timeout_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
            timeout_until_iso = timeout_until.isoformat() + "Z"

            # Call Discord API to set communication_disabled_until field
            try:
                await self._discord_client.edit_guild_member(
                    guild_id=guild_id,
                    user_id=user_id,
                    communication_disabled_until=timeout_until_iso,
                    reason=reason
                )

                # Format success response
                success_msg = f"✅ User timed out successfully!"
                success_msg += f"\n- **User**: {display_name} (`{user_id}`)"
                success_msg += f"\n- **Guild**: {guild_name} (`{guild_id}`)"
                success_msg += f"\n- **Duration**: {duration_minutes} minutes"
                if reason:
                    success_msg += f"\n- **Reason**: {reason}"
                success_msg += f"\n- **Expires**: {timeout_until.strftime('%Y-%m-%d %H:%M:%S')} UTC"

                # Add structured logging
                self._logger.info(
                    "User timeout completed successfully",
                    action="timeout",
                    guild_id=guild_id,
                    guild_name=guild_name,
                    target_user_id=user_id,
                    target_username=username,
                    moderator_context="mcp_tool",
                    duration_minutes=duration_minutes,
                    reason=reason,
                    expires_at=timeout_until_iso,
                    success=True,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    # Check specific permission error scenarios
                    if "Missing Permissions" in str(e) or "moderate_members" in str(e).lower():
                        return f"❌ Error: Bot does not have 'moderate_members' permission in {guild_name}."
                    else:
                        return f"❌ Error: Bot does not have permission to timeout users in {guild_name}. Role hierarchy may prevent this action."
                elif e.status_code == 404:
                    return f"❌ Error: User `{user_id}` is not a member of {guild_name}."
                elif e.status_code == 400:
                    return f"❌ Error: Invalid timeout request. User may already be timed out or parameters are invalid."
                else:
                    return f"❌ Error: Failed to timeout user: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while timing out user: {str(e)}"
            self._logger.error(
                "Unexpected error in timeout_user",
                guild_id=guild_id,
                user_id=user_id,
                duration_minutes=duration_minutes,
                error=str(e),
            )
            return error_msg

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
        try:
            self._logger.info(
                "Removing timeout from user",
                guild_id=guild_id,
                user_id=user_id,
                reason=reason,
            )

            # Check if guild is allowed
            if not self._validate_guild_permission(guild_id):
                return self._get_guild_permission_denied_message(guild_id)

            # Get guild information to validate access and get guild name
            try:
                guild = await self._discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Guild `{guild_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access guild `{guild_id}`."
                else:
                    return f"❌ Error: Failed to access guild: {str(e)}"

            # Get user information to validate and get username
            try:
                user = await self._discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")
                display_name = user.get("global_name") or username
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Validate role hierarchy before attempting moderation action
            hierarchy_error = await self._validate_role_hierarchy(
                guild_id, user_id, guild_name, display_name
            )
            if hierarchy_error:
                return hierarchy_error

            # Check if user is currently timed out before attempting removal
            try:
                member = await self._discord_client.get_guild_member(guild_id, user_id)
                communication_disabled_until = member.get("communication_disabled_until")
                
                if not communication_disabled_until:
                    return f"ℹ️ User {display_name} is not currently timed out in {guild_name}."
                
                # Parse the timeout end time to show when it would have expired
                try:
                    from datetime import datetime
                    timeout_end = datetime.fromisoformat(communication_disabled_until.replace("Z", "+00:00"))
                    timeout_end_str = timeout_end.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    timeout_end_str = "unknown time"
                    
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` is not a member of {guild_name}."
                else:
                    return f"❌ Error: Failed to get member information: {str(e)}"

            # Call Discord API to clear communication_disabled_until field
            try:
                await self._discord_client.edit_guild_member(
                    guild_id=guild_id,
                    user_id=user_id,
                    communication_disabled_until=None,
                    reason=reason
                )

                # Format success response
                success_msg = f"✅ User timeout removed successfully!"
                success_msg += f"\n- **User**: {display_name} (`{user_id}`)"
                success_msg += f"\n- **Guild**: {guild_name} (`{guild_id}`)"
                success_msg += f"\n- **Previous timeout expiry**: {timeout_end_str}"
                if reason:
                    success_msg += f"\n- **Reason**: {reason}"

                # Add structured logging
                self._logger.info(
                    "User timeout removal completed successfully",
                    action="untimeout",
                    guild_id=guild_id,
                    guild_name=guild_name,
                    target_user_id=user_id,
                    target_username=username,
                    moderator_context="mcp_tool",
                    reason=reason,
                    previous_timeout_expiry=timeout_end_str,
                    success=True,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    # Check specific permission error scenarios
                    if "Missing Permissions" in str(e) or "moderate_members" in str(e).lower():
                        return f"❌ Error: Bot does not have 'moderate_members' permission in {guild_name}."
                    else:
                        return f"❌ Error: Bot does not have permission to remove timeouts in {guild_name}. Role hierarchy may prevent this action."
                elif e.status_code == 404:
                    return f"❌ Error: User `{user_id}` is not a member of {guild_name}."
                elif e.status_code == 400:
                    return f"❌ Error: Invalid untimeout request. Parameters may be invalid."
                else:
                    return f"❌ Error: Failed to remove timeout: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while removing timeout: {str(e)}"
            self._logger.error(
                "Unexpected error in untimeout_user",
                guild_id=guild_id,
                user_id=user_id,
                error=str(e),
            )
            return error_msg

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
        try:
            self._logger.info(
                "Kicking user from guild",
                guild_id=guild_id,
                user_id=user_id,
                reason=reason,
            )

            # Check if guild is allowed
            if not self._validate_guild_permission(guild_id):
                return self._get_guild_permission_denied_message(guild_id)

            # Get guild information to validate access and get guild name
            try:
                guild = await self._discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Guild `{guild_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access guild `{guild_id}`."
                else:
                    return f"❌ Error: Failed to access guild: {str(e)}"

            # Get user information to validate and get username
            try:
                user = await self._discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")
                display_name = user.get("global_name") or username
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Verify target user exists in guild before attempting kick
            try:
                member = await self._discord_client.get_guild_member(guild_id, user_id)
                # If we get here, the user is a member of the guild
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` is not a member of {guild_name}."
                else:
                    return f"❌ Error: Failed to get member information: {str(e)}"

            # Validate role hierarchy before attempting moderation action
            hierarchy_error = await self._validate_role_hierarchy(
                guild_id, user_id, guild_name, display_name
            )
            if hierarchy_error:
                return hierarchy_error

            # Call Discord API kick endpoint with proper reason parameter
            try:
                await self._discord_client.kick_guild_member(
                    guild_id=guild_id,
                    user_id=user_id,
                    reason=reason
                )

                # Format success response
                success_msg = f"✅ User kicked successfully!"
                success_msg += f"\n- **User**: {display_name} (`{user_id}`)"
                success_msg += f"\n- **Guild**: {guild_name} (`{guild_id}`)"
                if reason:
                    success_msg += f"\n- **Reason**: {reason}"

                # Add structured logging and audit log integration
                self._logger.info(
                    "User kick completed successfully",
                    action="kick",
                    guild_id=guild_id,
                    guild_name=guild_name,
                    target_user_id=user_id,
                    target_username=username,
                    moderator_context="mcp_tool",
                    reason=reason,
                    success=True,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    # Check specific permission error scenarios
                    if "Missing Permissions" in str(e) or "kick_members" in str(e).lower():
                        return f"❌ Error: Bot does not have 'kick_members' permission in {guild_name}."
                    else:
                        return f"❌ Error: Bot does not have permission to kick users in {guild_name}. Role hierarchy may prevent this action."
                elif e.status_code == 404:
                    return f"❌ Error: User `{user_id}` is not a member of {guild_name}."
                elif e.status_code == 400:
                    return f"❌ Error: Invalid kick request. Parameters may be invalid."
                else:
                    return f"❌ Error: Failed to kick user: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while kicking user: {str(e)}"
            self._logger.error(
                "Unexpected error in kick_user",
                guild_id=guild_id,
                user_id=user_id,
                error=str(e),
            )
            return error_msg

    async def ban_user(
        self, guild_id: str, user_id: str, reason: Optional[str] = None, delete_message_days: int = 0
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
        try:
            self._logger.info(
                "Banning user from guild",
                guild_id=guild_id,
                user_id=user_id,
                reason=reason,
                delete_message_days=delete_message_days,
            )

            # Validate delete_message_days parameter (0-7 range)
            if delete_message_days < 0 or delete_message_days > 7:
                return f"❌ Error: delete_message_days must be between 0 and 7 (got {delete_message_days})."

            # Check if guild is allowed
            if not self._validate_guild_permission(guild_id):
                return self._get_guild_permission_denied_message(guild_id)

            # Get guild information to validate access and get guild name
            try:
                guild = await self._discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: Guild `{guild_id}` not found or bot has no access."
                elif e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to access guild `{guild_id}`."
                else:
                    return f"❌ Error: Failed to access guild: {str(e)}"

            # Get user information to validate and get username
            try:
                user = await self._discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")
                display_name = user.get("global_name") or username
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{user_id}` not found."
                else:
                    return f"❌ Error: Failed to get user information: {str(e)}"

            # Check if user is already banned (handle already-banned user scenarios)
            try:
                ban_info = await self._discord_client.get(f"/guilds/{guild_id}/bans/{user_id}")
                if ban_info:
                    return f"❌ Error: User `{display_name}` (`{user_id}`) is already banned from {guild_name}."
            except DiscordAPIError as e:
                # 404 means user is not banned, which is what we want
                if e.status_code != 404:
                    # Other errors might indicate permission issues, but we'll continue and let the ban attempt handle it
                    self._logger.warning(
                        "Could not check ban status",
                        guild_id=guild_id,
                        user_id=user_id,
                        error=str(e),
                    )

            # Validate role hierarchy before attempting moderation action
            # Note: For bans, we can ban users who are not currently in the guild,
            # so we only validate hierarchy if the user is a current member
            try:
                await self._discord_client.get_guild_member(guild_id, user_id)
                # User is a member, validate hierarchy
                hierarchy_error = await self._validate_role_hierarchy(
                    guild_id, user_id, guild_name, display_name
                )
                if hierarchy_error:
                    return hierarchy_error
            except DiscordAPIError as e:
                if e.status_code == 404:
                    # User is not a member, skip hierarchy validation for bans
                    self._logger.debug(
                        "Skipping hierarchy validation for ban - user not in guild",
                        guild_id=guild_id,
                        user_id=user_id,
                    )
                else:
                    # Other error getting member info, log but continue
                    self._logger.warning(
                        "Could not get member info for hierarchy validation",
                        guild_id=guild_id,
                        user_id=user_id,
                        error=str(e),
                    )

            # Call Discord API ban endpoint with reason and message deletion parameters
            try:
                await self._discord_client.ban_guild_member(
                    guild_id=guild_id,
                    user_id=user_id,
                    reason=reason,
                    delete_message_days=delete_message_days
                )

                # Format success response
                success_msg = f"✅ User banned successfully!"
                success_msg += f"\n- **User**: {display_name} (`{user_id}`)"
                success_msg += f"\n- **Guild**: {guild_name} (`{guild_id}`)"
                if reason:
                    success_msg += f"\n- **Reason**: {reason}"
                if delete_message_days > 0:
                    success_msg += f"\n- **Message Deletion**: {delete_message_days} day(s) of messages deleted"
                else:
                    success_msg += f"\n- **Message Deletion**: No messages deleted"

                # Add structured logging and audit log integration
                self._logger.info(
                    "User ban completed successfully",
                    action="ban",
                    guild_id=guild_id,
                    guild_name=guild_name,
                    target_user_id=user_id,
                    target_username=username,
                    moderator_context="mcp_tool",
                    reason=reason,
                    delete_message_days=delete_message_days,
                    success=True,
                )

                return success_msg

            except DiscordAPIError as e:
                if e.status_code == 403:
                    # Check specific permission error scenarios
                    if "Missing Permissions" in str(e) or "ban_members" in str(e).lower():
                        return f"❌ Error: Bot does not have 'ban_members' permission in {guild_name}."
                    else:
                        return f"❌ Error: Bot does not have permission to ban users in {guild_name}. Role hierarchy may prevent this action."
                elif e.status_code == 404:
                    return f"❌ Error: Guild `{guild_id}` or user `{user_id}` not found."
                elif e.status_code == 400:
                    return f"❌ Error: Invalid ban request. Parameters may be invalid."
                else:
                    return f"❌ Error: Failed to ban user: {str(e)}"

        except Exception as e:
            error_msg = f"❌ Unexpected error while banning user: {str(e)}"
            self._logger.error(
                "Unexpected error in ban_user",
                guild_id=guild_id,
                user_id=user_id,
                error=str(e),
            )
            return error_msg

    async def _validate_role_hierarchy(
        self, guild_id: str, target_user_id: str, guild_name: str, target_username: str
    ) -> Optional[str]:
        """
        Validate role hierarchy for moderation actions.
        
        Checks that the bot's highest role is higher than the target user's highest role,
        following Discord's hierarchy rules where lower position numbers indicate higher roles.
        
        Args:
            guild_id: The Discord guild ID
            target_user_id: The target user ID to check hierarchy against
            guild_name: The guild name for error messages
            target_username: The target username for error messages
            
        Returns:
            Optional[str]: Error message if hierarchy validation fails, None if validation passes
        """
        try:
            # Get bot's member information in the guild
            try:
                bot_user = await self._discord_client.get_current_user()
                bot_user_id = bot_user["id"]
                bot_member = await self._discord_client.get_guild_member(guild_id, bot_user_id)
            except DiscordAPIError as e:
                self._logger.error(
                    "Failed to get bot member information for hierarchy validation",
                    guild_id=guild_id,
                    bot_user_id=bot_user_id,
                    error=str(e),
                )
                return f"❌ Error: Could not validate bot permissions in {guild_name}."

            # Get target user's member information in the guild
            try:
                target_member = await self._discord_client.get_guild_member(guild_id, target_user_id)
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"❌ Error: User `{target_username}` (`{target_user_id}`) is not a member of {guild_name}."
                else:
                    self._logger.error(
                        "Failed to get target member information for hierarchy validation",
                        guild_id=guild_id,
                        target_user_id=target_user_id,
                        error=str(e),
                    )
                    return f"❌ Error: Could not validate target user permissions in {guild_name}."

            # Get guild information to access roles
            try:
                guild_info = await self._discord_client.get_guild(guild_id)
                guild_roles = guild_info.get("roles", [])
            except DiscordAPIError as e:
                self._logger.error(
                    "Failed to get guild roles for hierarchy validation",
                    guild_id=guild_id,
                    error=str(e),
                )
                return f"❌ Error: Could not validate role hierarchy in {guild_name}."

            # Create a mapping of role ID to role data for quick lookup
            role_map = {role["id"]: role for role in guild_roles}

            # Get bot's highest role position
            bot_role_ids = bot_member.get("roles", [])
            bot_highest_position = -1  # Default position for @everyone role
            
            for role_id in bot_role_ids:
                role = role_map.get(role_id)
                if role:
                    # Lower position numbers indicate higher roles in Discord
                    if bot_highest_position == -1 or role["position"] > bot_highest_position:
                        bot_highest_position = role["position"]

            # Get target user's highest role position
            target_role_ids = target_member.get("roles", [])
            target_highest_position = -1  # Default position for @everyone role
            
            for role_id in target_role_ids:
                role = role_map.get(role_id)
                if role:
                    # Lower position numbers indicate higher roles in Discord
                    if target_highest_position == -1 or role["position"] > target_highest_position:
                        target_highest_position = role["position"]

            # Check if bot can moderate the target user
            # Bot must have a higher role position than the target user
            if bot_highest_position <= target_highest_position:
                # Find the names of the highest roles for better error messaging
                bot_highest_role_name = "@everyone"
                target_highest_role_name = "@everyone"
                
                for role_id in bot_role_ids:
                    role = role_map.get(role_id)
                    if role and role["position"] == bot_highest_position:
                        bot_highest_role_name = role["name"]
                        break
                        
                for role_id in target_role_ids:
                    role = role_map.get(role_id)
                    if role and role["position"] == target_highest_position:
                        target_highest_role_name = role["name"]
                        break

                return (
                    f"❌ Error: Cannot moderate `{target_username}` due to role hierarchy restrictions.\n"
                    f"- **Bot's highest role**: {bot_highest_role_name} (position {bot_highest_position})\n"
                    f"- **Target user's highest role**: {target_highest_role_name} (position {target_highest_position})\n"
                    f"- **Requirement**: Bot's role must be higher than target user's role"
                )

            # Hierarchy validation passed
            self._logger.debug(
                "Role hierarchy validation passed",
                guild_id=guild_id,
                target_user_id=target_user_id,
                bot_highest_position=bot_highest_position,
                target_highest_position=target_highest_position,
            )
            return None

        except Exception as e:
            self._logger.error(
                "Unexpected error during role hierarchy validation",
                guild_id=guild_id,
                target_user_id=target_user_id,
                error=str(e),
            )
            return f"❌ Error: Could not validate role hierarchy: {str(e)}"
