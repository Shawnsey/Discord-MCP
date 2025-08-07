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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info("Fetching guild list")

            # Get guilds from Discord API
            guilds = await discord_client.get_user_guilds()

            # Filter guilds based on settings
            if settings.get_allowed_guilds_set():
                allowed_guilds = settings.get_allowed_guilds_set()
                guilds = [g for g in guilds if g["id"] in allowed_guilds]
                logger.info(
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
                    guild_details = await discord_client.get_guild(guild["id"])
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
                    logger.warning(
                        "Failed to get guild details",
                        guild_id=guild["id"],
                        error=str(e),
                    )
                    guild_info.append(
                        "- **Details**: Unable to fetch additional details"
                    )

                guild_info.append("")  # Empty line between guilds

            result = "\n".join(guild_info)
            logger.info("Guild list retrieved successfully", guild_count=len(guilds))
            return result

        except DiscordAPIError as e:
            error_msg = f"Discord API error while fetching guilds: {str(e)}"
            logger.error("Discord API error in list_guilds", error=str(e))
            return f"# Error\n\n{error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error while fetching guilds: {str(e)}"
            logger.error("Unexpected error in list_guilds", error=str(e))
            return f"# Error\n\n{error_msg}"

    @server.resource("channels://{guild_id}")
    async def list_channels(guild_id: str) -> str:
        """
        List all channels in a specific Discord guild.

        Args:
            guild_id: The Discord guild (server) ID

        Returns a formatted list of channels with their information
        including ID, name, type, topic, and permissions.
        """
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info("Fetching channel list", guild_id=guild_id)

            # Check if guild is allowed
            if not settings.is_guild_allowed(guild_id):
                return (
                    f"# Access Denied\n\nAccess to guild `{guild_id}` is not permitted."
                )

            # Get guild information first
            try:
                guild = await discord_client.get_guild(guild_id)
                guild_name = guild["name"]
            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"# Guild Not Found\n\nGuild with ID `{guild_id}` was not found or bot has no access."
                raise

            # Get channels from Discord API
            channels = await discord_client.get_guild_channels(guild_id)

            # Filter channels based on settings
            if settings.get_allowed_channels_set():
                allowed_channels = settings.get_allowed_channels_set()
                channels = [c for c in channels if c["id"] in allowed_channels]
                logger.info(
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
            logger.info(
                "Channel list retrieved successfully",
                guild_id=guild_id,
                channel_count=len(channels),
            )
            return result

        except DiscordAPIError as e:
            error_msg = f"Discord API error while fetching channels: {str(e)}"
            logger.error(
                "Discord API error in list_channels", guild_id=guild_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error while fetching channels: {str(e)}"
            logger.error(
                "Unexpected error in list_channels", guild_id=guild_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"

    @server.resource("messages://{channel_id}")
    async def get_messages(channel_id: str) -> str:
        """
        Get recent messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID

        Returns a formatted list of recent messages with author information,
        timestamps, and content.
        """
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info("Fetching messages", channel_id=channel_id)

            # Check if channel is allowed
            if not settings.is_channel_allowed(channel_id):
                return f"# Access Denied\n\nAccess to channel `{channel_id}` is not permitted."

            # Get channel information first
            try:
                channel = await discord_client.get_channel(channel_id)
                channel_name = channel["name"]
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not settings.is_guild_allowed(guild_id):
                    return f"# Access Denied\n\nAccess to guild containing channel `{channel_id}` is not permitted."

            except DiscordAPIError as e:
                if e.status_code == 404:
                    return f"# Channel Not Found\n\nChannel with ID `{channel_id}` was not found or bot has no access."
                raise

            # Get messages from Discord API (limit to 50 recent messages)
            messages = await discord_client.get_channel_messages(channel_id, limit=50)

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
            logger.info(
                "Messages retrieved successfully",
                channel_id=channel_id,
                message_count=len(messages),
            )
            return result

        except DiscordAPIError as e:
            error_msg = f"Discord API error while fetching messages: {str(e)}"
            logger.error(
                "Discord API error in get_messages", channel_id=channel_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error while fetching messages: {str(e)}"
            logger.error(
                "Unexpected error in get_messages", channel_id=channel_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"

    @server.resource("user://{user_id}")
    async def get_user_info(user_id: str) -> str:
        """
        Get information about a Discord user.

        Args:
            user_id: The Discord user ID

        Returns formatted user information including username, avatar,
        and other available details.
        """
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]

            logger.info("Fetching user info", user_id=user_id)

            # Get user information from Discord API
            try:
                user = await discord_client.get_user(user_id)
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
            logger.info("User info retrieved successfully", user_id=user_id)
            return result

        except DiscordAPIError as e:
            error_msg = f"Discord API error while fetching user info: {str(e)}"
            logger.error(
                "Discord API error in get_user_info", user_id=user_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error while fetching user info: {str(e)}"
            logger.error(
                "Unexpected error in get_user_info", user_id=user_id, error=str(e)
            )
            return f"# Error\n\n{error_msg}"

    logger.info("Discord MCP resources registered successfully")
