"""
Consolidated tests for Discord MCP tools.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.server.fastmcp import FastMCP

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError
from discord_mcp.tools import register_tools


@pytest.fixture
def server_with_tools():
    """Create FastMCP server with tools registered."""
    server = FastMCP("Test Server")
    register_tools(server)
    return server


def create_mock_context(mock_discord_client, settings=None):
    """Helper function to create mock context."""
    if settings is None:
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
        )

    context = MagicMock()
    context.request_context.lifespan_context = {
        "discord_client": mock_discord_client,
        "settings": settings,
    }
    return context


class TestListGuildsTool:
    """Test list guilds tool."""

    @pytest.mark.asyncio
    async def test_list_guilds_success(self, server_with_tools):
        """Test successful guild listing."""
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user_guilds.return_value = [
            {"id": "guild123", "name": "Test Guild", "owner": True},
            {"id": "guild456", "name": "Another Guild", "owner": False},
        ]
        mock_discord_client.get_guild.return_value = {
            "approximate_member_count": 100,
            "description": "A test guild",
            "features": ["COMMUNITY", "NEWS"],
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        # Call the tool
        result_tuple = await server_with_tools.call_tool("list_guilds", {})
        result = result_tuple[1]["result"]

        # Verify the result
        assert "# Discord Guilds" in result
        assert "Found 2 accessible guild(s)" in result
        assert "Test Guild" in result
        assert "Another Guild" in result
        assert "guild123" in result
        assert "guild456" in result
        assert "Owner**: Yes" in result
        assert "Owner**: No" in result
        assert "Member Count**: 100" in result
        assert "COMMUNITY, NEWS" in result

        # Verify API calls
        mock_discord_client.get_user_guilds.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_guilds_no_guilds(self, server_with_tools):
        """Test when no guilds are accessible."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user_guilds.return_value = []

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool("list_guilds", {})
        result = result_tuple[1]["result"]

        assert "No guilds found or bot has no access to any guilds" in result

    @pytest.mark.asyncio
    async def test_list_guilds_api_error(self, server_with_tools):
        """Test handling Discord API errors."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user_guilds.side_effect = DiscordAPIError(
            "API Error", 500
        )

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool("list_guilds", {})
        result = result_tuple[1]["result"]

        assert "# Error" in result
        assert "Discord API error while fetching guilds" in result


class TestListChannelsTool:
    """Test list channels tool."""

    @pytest.mark.asyncio
    async def test_list_channels_success(self, server_with_tools):
        """Test successful channel listing."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_guild_channels.return_value = [
            {
                "id": "ch123",
                "name": "general",
                "type": 0,
                "topic": "General discussion",
                "position": 0,
            },
            {"id": "ch456", "name": "voice-chat", "type": 2, "position": 1},
        ]

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "list_channels", {"guild_id": "guild123"}
        )
        result = result_tuple[1]["result"]

        assert "# Channels in Test Guild" in result
        assert "Found 2 accessible channel(s)" in result
        assert "## Text Channels" in result
        assert "## Voice Channels" in result
        assert "general" in result
        assert "voice-chat" in result
        assert "General discussion" in result

        mock_discord_client.get_guild.assert_called_once_with("guild123")
        mock_discord_client.get_guild_channels.assert_called_once_with("guild123")

    @pytest.mark.asyncio
    async def test_list_channels_guild_not_allowed(self, server_with_tools):
        """Test listing channels for restricted guild."""
        mock_discord_client = AsyncMock()
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_guilds="guild456",  # Only allow guild456
        )

        server_with_tools.get_context = lambda: create_mock_context(
            mock_discord_client, settings
        )

        result_tuple = await server_with_tools.call_tool(
            "list_channels", {"guild_id": "guild123"}
        )
        result = result_tuple[1]["result"]

        assert "# Access Denied" in result
        assert "not permitted" in result

    @pytest.mark.asyncio
    async def test_list_channels_guild_not_found(self, server_with_tools):
        """Test listing channels for non-existent guild."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not Found", 404)

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "list_channels", {"guild_id": "guild999"}
        )
        result = result_tuple[1]["result"]

        assert "# Guild Not Found" in result
        assert "was not found or bot has no access" in result


class TestGetMessagesTool:
    """Test get messages tool."""

    @pytest.mark.asyncio
    async def test_get_messages_success(self, server_with_tools):
        """Test successful message retrieval."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.get_channel_messages.return_value = [
            {
                "id": "msg1",
                "content": "Hello world!",
                "author": {"username": "testuser", "id": "user123"},
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [],
                "embeds": [],
            },
            {
                "id": "msg2",
                "content": "How are you?",
                "author": {"username": "anotheruser", "id": "user456"},
                "timestamp": "2023-01-01T12:01:00Z",
                "attachments": [{"filename": "image.png"}],
                "embeds": [{"title": "Test Embed"}],
            },
        ]

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "get_messages", {"channel_id": "ch123"}
        )
        result = result_tuple[1]["result"]

        assert "# Messages in #general" in result
        assert "Showing 2 recent message(s)" in result
        assert "Hello world!" in result
        assert "How are you?" in result
        assert "testuser" in result
        assert "anotheruser" in result
        assert "2023-01-01 12:00:00 UTC" in result
        assert "1 file(s)" in result
        assert "1 embed(s)" in result

        mock_discord_client.get_channel.assert_called_once_with("ch123")
        mock_discord_client.get_channel_messages.assert_called_once_with(
            "ch123", limit=50
        )

    @pytest.mark.asyncio
    async def test_get_messages_channel_not_allowed(self, server_with_tools):
        """Test getting messages from restricted channel."""
        mock_discord_client = AsyncMock()
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_channels="ch456",  # Only allow ch456
        )

        server_with_tools.get_context = lambda: create_mock_context(
            mock_discord_client, settings
        )

        result_tuple = await server_with_tools.call_tool(
            "get_messages", {"channel_id": "ch123"}
        )
        result = result_tuple[1]["result"]

        assert "# Access Denied" in result
        assert "not permitted" in result

    @pytest.mark.asyncio
    async def test_get_messages_no_messages(self, server_with_tools):
        """Test getting messages from empty channel."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "empty-channel",
            "guild_id": "guild123",
        }
        mock_discord_client.get_channel_messages.return_value = []

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "get_messages", {"channel_id": "ch123"}
        )
        result = result_tuple[1]["result"]

        assert "No messages found in this channel" in result


class TestGetUserInfoTool:
    """Test get user info tool."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, server_with_tools):
        """Test successful user info retrieval."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "id": "user123",
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User",
            "bot": False,
            "avatar": "avatar_hash",
            "banner": "banner_hash",
            "accent_color": 0xFF5733,
            "public_flags": 64,
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "get_user_info", {"user_id": "user123"}
        )
        result = result_tuple[1]["result"]

        assert "# User: testuser" in result
        assert "Username**: testuser" in result
        assert "User ID**: `user123`" in result
        assert "Discriminator**: #1234" in result
        assert "Display Name**: Test User" in result
        assert "Type**: User" in result
        assert "View Avatar" in result
        assert "View Banner" in result
        assert "Accent Color**: #ff5733" in result
        assert "Public Flags**: 64" in result

        mock_discord_client.get_user.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_user_info_bot_user(self, server_with_tools):
        """Test getting info for a bot user."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "id": "bot123",
            "username": "testbot",
            "discriminator": "0000",
            "bot": True,
            "system": False,
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "get_user_info", {"user_id": "bot123"}
        )
        result = result_tuple[1]["result"]

        assert "# User: testbot" in result
        assert "Type**: Bot" in result
        assert "Default avatar" in result

    @pytest.mark.asyncio
    async def test_get_user_info_user_not_found(self, server_with_tools):
        """Test getting info for non-existent user."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "get_user_info", {"user_id": "user999"}
        )
        result = result_tuple[1]["result"]

        assert "# User Not Found" in result
        assert "was not found" in result


class TestSendMessageTool:
    """Test send message tool."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, server_with_tools):
        """Test successful message sending."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.send_message.return_value = {
            "id": "msg123",
            "timestamp": "2023-01-01T12:00:00Z",
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_message", {"channel_id": "ch123", "content": "Hello world!"}
        )
        result = result_tuple[1]["result"]

        assert "✅ Message sent successfully" in result
        assert "msg123" in result
        assert "general" in result
        assert "Hello world!" in result

        mock_discord_client.get_channel.assert_called_once_with("ch123")
        mock_discord_client.send_message.assert_called_once_with(
            channel_id="ch123", content="Hello world!", message_reference=None
        )

    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, server_with_tools):
        """Test sending message as a reply."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.send_message.return_value = {
            "id": "msg123",
            "timestamp": "2023-01-01T12:00:00Z",
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_message",
            {
                "channel_id": "ch123",
                "content": "This is a reply!",
                "reply_to_message_id": "original_msg",
            },
        )
        result = result_tuple[1]["result"]

        assert "✅ Message sent successfully" in result
        assert "Reply to" in result
        assert "original_msg" in result

        mock_discord_client.send_message.assert_called_once_with(
            channel_id="ch123",
            content="This is a reply!",
            message_reference={"message_id": "original_msg", "channel_id": "ch123"},
        )

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, server_with_tools):
        """Test sending message with empty content."""
        mock_discord_client = AsyncMock()
        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_message", {"channel_id": "ch123", "content": ""}
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Message content cannot be empty" in result

    @pytest.mark.asyncio
    async def test_send_message_too_long(self, server_with_tools):
        """Test sending message that's too long."""
        mock_discord_client = AsyncMock()
        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        long_content = "x" * 2001  # Discord limit is 2000
        result_tuple = await server_with_tools.call_tool(
            "send_message", {"channel_id": "ch123", "content": long_content}
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Message content too long" in result
        assert "2001 characters" in result

    @pytest.mark.asyncio
    async def test_send_message_channel_not_allowed(self, server_with_tools):
        """Test sending message to restricted channel."""
        mock_discord_client = AsyncMock()
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_channels="ch456",  # Only allow ch456
        )

        server_with_tools.get_context = lambda: create_mock_context(
            mock_discord_client, settings
        )

        result_tuple = await server_with_tools.call_tool(
            "send_message",
            {"channel_id": "ch123", "content": "Hello world!"},  # Not in allowed list
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Access to channel" in result
        assert "not permitted" in result


class TestSendDMTool:
    """Test send DM tool."""

    @pytest.mark.asyncio
    async def test_send_dm_success(self, server_with_tools):
        """Test successful DM sending."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "id": "user123",
            "bot": False,
        }
        mock_discord_client.send_dm.return_value = {
            "id": "dm_msg123",
            "timestamp": "2023-01-01T12:00:00Z",
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_dm", {"user_id": "user123", "content": "Hello via DM!"}
        )
        result = result_tuple[1]["result"]

        assert "✅ Direct message sent successfully" in result
        assert "testuser" in result
        assert "dm_msg123" in result
        assert "Hello via DM!" in result

        mock_discord_client.get_user.assert_called_once_with("user123")
        mock_discord_client.send_dm.assert_called_once_with("user123", "Hello via DM!")

    @pytest.mark.asyncio
    async def test_send_dm_user_not_found(self, server_with_tools):
        """Test sending DM to non-existent user."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_dm", {"user_id": "user999", "content": "Hello!"}
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: User" in result
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_send_dm_blocked(self, server_with_tools):
        """Test sending DM when user has blocked DMs."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "id": "user123",
            "bot": False,
        }
        mock_discord_client.send_dm.side_effect = DiscordAPIError("Forbidden", 403)

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "send_dm", {"user_id": "user123", "content": "Hello!"}
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Cannot send DM" in result
        assert "DMs disabled or blocked" in result


class TestDeleteMessageTool:
    """Test delete message tool."""

    @pytest.mark.asyncio
    async def test_delete_message_success(self, server_with_tools):
        """Test successful message deletion."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.get_channel_message.return_value = {
            "author": {"username": "testuser"},
            "content": "This message will be deleted",
        }
        mock_discord_client.delete_message.return_value = {}

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "delete_message", {"channel_id": "ch123", "message_id": "msg123"}
        )
        result = result_tuple[1]["result"]

        assert "✅ Message deleted successfully" in result
        assert "general" in result
        assert "testuser" in result
        assert "This message will be deleted" in result

        mock_discord_client.get_channel.assert_called_once_with("ch123")
        mock_discord_client.get_channel_message.assert_called_once_with(
            "ch123", "msg123"
        )
        mock_discord_client.delete_message.assert_called_once_with("ch123", "msg123")

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, server_with_tools):
        """Test deleting non-existent message."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.get_channel_message.side_effect = DiscordAPIError(
            "Not Found", 404
        )

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "delete_message", {"channel_id": "ch123", "message_id": "msg999"}
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Message" in result
        assert "not found" in result


class TestEditMessageTool:
    """Test edit message tool."""

    @pytest.mark.asyncio
    async def test_edit_message_success(self, server_with_tools):
        """Test successful message editing."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot123"}
        mock_discord_client.get_channel_message.return_value = {
            "author": {"id": "bot123"},  # Same as bot user ID
            "content": "Original message",
        }
        mock_discord_client.patch.return_value = {
            "id": "msg123",
            "content": "Edited message",
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "edit_message",
            {
                "channel_id": "ch123",
                "message_id": "msg123",
                "new_content": "Edited message",
            },
        )
        result = result_tuple[1]["result"]

        assert "✅ Message edited successfully" in result
        assert "Original message" in result
        assert "Edited message" in result

        mock_discord_client.patch.assert_called_once_with(
            "/channels/ch123/messages/msg123", data={"content": "Edited message"}
        )

    @pytest.mark.asyncio
    async def test_edit_message_not_own_message(self, server_with_tools):
        """Test editing message not sent by bot."""
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot123"}
        mock_discord_client.get_channel_message.return_value = {
            "author": {"id": "user456"},  # Different from bot user ID
            "content": "User's message",
        }

        server_with_tools.get_context = lambda: create_mock_context(mock_discord_client)

        result_tuple = await server_with_tools.call_tool(
            "edit_message",
            {
                "channel_id": "ch123",
                "message_id": "msg123",
                "new_content": "Edited message",
            },
        )
        result = result_tuple[1]["result"]

        assert "❌ Error: Can only edit bot's own messages" in result
