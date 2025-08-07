"""
MCP Tools for Discord integration.

This module implements all the write operations (tools) that allow AI assistants
to perform actions on Discord through the Model Context Protocol.
"""

from typing import Optional

import structlog
from mcp.server.fastmcp import FastMCP

from .config import Settings
from .discord_client import DiscordAPIError, DiscordClient

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

    @server.tool()
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

    @server.tool()
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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info(
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
            if not settings.is_channel_allowed(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access and get guild info
            try:
                channel = await discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not settings.is_guild_allowed(guild_id):
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
                result = await discord_client.send_message(
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

                logger.info(
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
            logger.error(
                "Unexpected error in send_message", channel_id=channel_id, error=str(e)
            )
            return error_msg

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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]

            logger.info(
                "Sending DM to user", user_id=user_id, content_length=len(content)
            )

            # Validate inputs
            if not content or not content.strip():
                return "❌ Error: Message content cannot be empty."

            if len(content) > 2000:
                return f"❌ Error: Message content too long ({len(content)} characters). Discord limit is 2000 characters."

            # Get user information to validate and get username
            try:
                user = await discord_client.get_user(user_id)
                username = user.get("username", "Unknown User")

                # Check if user is a bot (some bots don't accept DMs)
                if (
                    user.get("bot")
                    and user.get("id") != discord_client.settings.discord_application_id
                ):
                    logger.warning(
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
                result = await discord_client.send_dm(user_id, content)

                message_id = result.get("id")
                timestamp = result.get("timestamp", "")

                success_msg = f"✅ Direct message sent successfully to {username}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Recipient**: {username} (`{user_id}`)"
                success_msg += f"\n- **Content**: {content[:100]}{'...' if len(content) > 100 else ''}"
                if timestamp:
                    success_msg += f"\n- **Sent at**: {timestamp}"

                logger.info(
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
            logger.error("Unexpected error in send_dm", user_id=user_id, error=str(e))
            return error_msg

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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info(
                "Deleting message", channel_id=channel_id, message_id=message_id
            )

            # Check if channel is allowed
            if not settings.is_channel_allowed(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access
            try:
                channel = await discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not settings.is_guild_allowed(guild_id):
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
                message = await discord_client.get_channel_message(
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
                await discord_client.delete_message(channel_id, message_id)

                success_msg = f"✅ Message deleted successfully from #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Author**: {message_author}"
                success_msg += f"\n- **Content**: {message_content}"

                logger.info(
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
            logger.error(
                "Unexpected error in delete_message",
                channel_id=channel_id,
                message_id=message_id,
                error=str(e),
            )
            return error_msg

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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info(
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
            if not settings.is_channel_allowed(channel_id):
                return f"❌ Error: Access to channel `{channel_id}` is not permitted."

            # Get channel information to validate access
            try:
                channel = await discord_client.get_channel(channel_id)
                channel_name = channel.get("name", "Unknown")
                guild_id = channel.get("guild_id")

                # Also check guild permission if it's a guild channel
                if guild_id and not settings.is_guild_allowed(guild_id):
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
                bot_user = await discord_client.get_current_user()
                bot_user_id = bot_user["id"]
            except DiscordAPIError as e:
                return f"❌ Error: Failed to get bot user information: {str(e)}"

            # Get message information to verify ownership
            try:
                message = await discord_client.get_channel_message(
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
                result = await discord_client.patch(
                    f"/channels/{channel_id}/messages/{message_id}",
                    data={"content": new_content},
                )

                success_msg = f"✅ Message edited successfully in #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Old Content**: {old_content[:50]}{'...' if len(old_content) > 50 else ''}"
                success_msg += f"\n- **New Content**: {new_content[:50]}{'...' if len(new_content) > 50 else ''}"

                logger.info(
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
            logger.error(
                "Unexpected error in edit_message",
                channel_id=channel_id,
                message_id=message_id,
                error=str(e),
            )
            return error_msg

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
        try:
            # Get context from server
            ctx = server.get_context()
            lifespan_ctx = ctx.request_context.lifespan_context
            discord_client: DiscordClient = lifespan_ctx["discord_client"]
            settings: Settings = lifespan_ctx["settings"]

            logger.info("Reading direct messages", user_id=user_id, limit=limit)

            # Validate inputs
            if limit < 1 or limit > 100:
                return "❌ Error: Limit must be between 1 and 100."

            # Get user information
            try:
                user_info = await discord_client.get_user(user_id)
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
                dm_channel = await discord_client.create_dm_channel(user_id)
                dm_channel_id = dm_channel["id"]

            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Cannot create DM channel with {display_name}. User may have DMs disabled."
                else:
                    return f"❌ Error: Failed to create DM channel: {str(e)}"

            # Get messages from the DM channel
            try:
                messages = await discord_client.get_channel_messages(
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
                    bot_user = await discord_client.get_current_user()
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

                logger.info(
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
            logger.error(
                "Unexpected error in read_direct_messages",
                user_id=user_id,
                error=str(e),
            )
            return error_msg

    logger.info("Discord MCP tools registered successfully")
