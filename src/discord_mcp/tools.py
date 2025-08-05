"""
MCP Tools for Discord integration.

This module implements all the write operations (tools) that allow AI assistants
to perform actions on Discord through the Model Context Protocol.
"""

from typing import Dict, Any, List, Optional
import structlog
from mcp.server.fastmcp import FastMCP

from .discord_client import DiscordClient, DiscordAPIError
from .config import Settings

logger = structlog.get_logger(__name__)


def register_tools(server: FastMCP) -> None:
    """Register all Discord MCP tools with the server."""
    
    @server.tool()
    async def send_message(
        channel_id: str,
        content: str,
        reply_to_message_id: Optional[str] = None
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
            
            logger.info("Sending message to channel", 
                       channel_id=channel_id, 
                       content_length=len(content),
                       reply_to=reply_to_message_id)
            
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
                    "channel_id": channel_id
                }
            
            # Send the message
            try:
                result = await discord_client.send_message(
                    channel_id=channel_id,
                    content=content,
                    message_reference=message_data.get("message_reference")
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
                
                logger.info("Message sent successfully", 
                           channel_id=channel_id,
                           message_id=message_id,
                           reply_to=reply_to_message_id)
                
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
            logger.error("Unexpected error in send_message", 
                        channel_id=channel_id, 
                        error=str(e))
            return error_msg
    
    @server.tool()
    async def send_dm(
        user_id: str,
        content: str
    ) -> str:
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
            
            logger.info("Sending DM to user", 
                       user_id=user_id, 
                       content_length=len(content))
            
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
                if user.get("bot") and user.get("id") != discord_client.settings.discord_application_id:
                    logger.warning("Attempting to DM another bot", user_id=user_id, username=username)
                
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
                
                logger.info("DM sent successfully", 
                           user_id=user_id,
                           username=username,
                           message_id=message_id)
                
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
            logger.error("Unexpected error in send_dm", 
                        user_id=user_id, 
                        error=str(e))
            return error_msg
    
    @server.tool()
    async def delete_message(
        channel_id: str,
        message_id: str
    ) -> str:
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
            
            logger.info("Deleting message", 
                       channel_id=channel_id, 
                       message_id=message_id)
            
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
                message = await discord_client.get_channel_message(channel_id, message_id)
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
                
                logger.info("Message deleted successfully", 
                           channel_id=channel_id,
                           message_id=message_id,
                           author=message_author)
                
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
            logger.error("Unexpected error in delete_message", 
                        channel_id=channel_id,
                        message_id=message_id,
                        error=str(e))
            return error_msg
    
    @server.tool()
    async def edit_message(
        channel_id: str,
        message_id: str,
        new_content: str
    ) -> str:
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
            
            logger.info("Editing message", 
                       channel_id=channel_id, 
                       message_id=message_id,
                       new_content_length=len(new_content))
            
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
                message = await discord_client.get_channel_message(channel_id, message_id)
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
                    data={"content": new_content}
                )
                
                success_msg = f"✅ Message edited successfully in #{channel_name}!"
                success_msg += f"\n- **Message ID**: `{message_id}`"
                success_msg += f"\n- **Channel**: #{channel_name} (`{channel_id}`)"
                success_msg += f"\n- **Old Content**: {old_content[:50]}{'...' if len(old_content) > 50 else ''}"
                success_msg += f"\n- **New Content**: {new_content[:50]}{'...' if len(new_content) > 50 else ''}"
                
                logger.info("Message edited successfully", 
                           channel_id=channel_id,
                           message_id=message_id)
                
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
            logger.error("Unexpected error in edit_message", 
                        channel_id=channel_id,
                        message_id=message_id,
                        error=str(e))
            return error_msg
    
    @server.tool()
    async def read_direct_messages(
        user_id: str,
        limit: int = 10
    ) -> str:
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
            
            logger.info("Reading direct messages", 
                       user_id=user_id, 
                       limit=limit)
            
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
                messages = await discord_client.get_channel_messages(dm_channel_id, limit=limit)
                
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
                        filenames = [att.get("filename", "unknown") for att in attachments[:3]]
                        result += ", ".join(filenames)
                        if len(attachments) > 3:
                            result += f" and {len(attachments) - 3} more"
                        result += "\n"
                    
                    # Check for reactions
                    reactions = message.get("reactions", [])
                    if reactions:
                        result += f"     ⭐ {len(reactions)} reaction(s)\n"
                    
                    result += "\n"
                
                logger.info("Direct messages retrieved successfully", 
                           user_id=user_id,
                           username=display_name,
                           message_count=len(messages))
                
                return result
                
            except DiscordAPIError as e:
                if e.status_code == 403:
                    return f"❌ Error: Bot does not have permission to read DMs with {display_name}."
                else:
                    return f"❌ Error: Failed to read DM messages: {str(e)}"
            
        except Exception as e:
            error_msg = f"❌ Unexpected error while reading direct messages: {str(e)}"
            logger.error("Unexpected error in read_direct_messages", 
                        user_id=user_id,
                        error=str(e))
            return error_msg
    
    logger.info("Discord MCP tools registered successfully")
