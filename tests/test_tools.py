"""
Tests for Discord MCP tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from discord_mcp.tools import register_tools
from discord_mcp.discord_client import DiscordAPIError
from discord_mcp.config import Settings
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678"
    )


@pytest.fixture
def mock_discord_client():
    """Create mock Discord client."""
    return AsyncMock()


@pytest.fixture
def mock_context(settings, mock_discord_client):
    """Create mock MCP context."""
    context = MagicMock()
    context.request_context.lifespan_context = {
        "discord_client": mock_discord_client,
        "settings": settings
    }
    return context


@pytest.fixture
def server_with_tools():
    """Create FastMCP server with tools registered."""
    server = FastMCP("Test Server")
    
    # Mock get_context method
    def mock_get_context():
        context = MagicMock()
        context.request_context.lifespan_context = {
            "discord_client": AsyncMock(),
            "settings": Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                discord_application_id="123456789012345678"
            )
        }
        return context
    
    server.get_context = mock_get_context
    register_tools(server)
    return server


class TestSendMessageTool:
    """Test send message tool."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, server_with_tools):
        """Test successful message sending."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_message":
                tool_func = tool.handler
                break
        
        assert tool_func is not None
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.send_message.return_value = {
            "id": "msg123",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            channel_id="ch123",
            content="Hello world!"
        )
        
        # Verify the result
        assert "✅ Message sent successfully" in result
        assert "msg123" in result
        assert "general" in result
        assert "Hello world!" in result
        
        # Verify API calls
        mock_discord_client.get_channel.assert_called_once_with("ch123")
        mock_discord_client.send_message.assert_called_once_with(
            channel_id="ch123",
            content="Hello world!",
            message_reference=None
        )
    
    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, server_with_tools):
        """Test sending message as a reply."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_message":
                tool_func = tool.handler
                break
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.send_message.return_value = {
            "id": "msg123",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool with reply
        result = await tool_func(
            channel_id="ch123",
            content="This is a reply!",
            reply_to_message_id="original_msg"
        )
        
        # Verify the result
        assert "✅ Message sent successfully" in result
        assert "Reply to" in result
        assert "original_msg" in result
        
        # Verify API calls
        mock_discord_client.send_message.assert_called_once_with(
            channel_id="ch123",
            content="This is a reply!",
            message_reference={
                "message_id": "original_msg",
                "channel_id": "ch123"
            }
        )
    
    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, server_with_tools):
        """Test sending message with empty content."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_message":
                tool_func = tool.handler
                break
        
        # Call the tool with empty content
        result = await tool_func(
            channel_id="ch123",
            content=""
        )
        
        # Verify error message
        assert "❌ Error: Message content cannot be empty" in result
    
    @pytest.mark.asyncio
    async def test_send_message_too_long(self, server_with_tools):
        """Test sending message that's too long."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_message":
                tool_func = tool.handler
                break
        
        # Call the tool with content that's too long
        long_content = "x" * 2001  # Discord limit is 2000
        result = await tool_func(
            channel_id="ch123",
            content=long_content
        )
        
        # Verify error message
        assert "❌ Error: Message content too long" in result
        assert "2001 characters" in result
    
    @pytest.mark.asyncio
    async def test_send_message_channel_not_allowed(self, server_with_tools):
        """Test sending message to restricted channel."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_message":
                tool_func = tool.handler
                break
        
        # Mock the server's get_context method with restricted settings
        def mock_get_context():
            context = MagicMock()
            settings = Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                discord_application_id="123456789012345678",
                allowed_channels="ch456"  # Only allow ch456
            )
            context.request_context.lifespan_context = {
                "discord_client": AsyncMock(),
                "settings": settings
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool with restricted channel
        result = await tool_func(
            channel_id="ch123",  # Not in allowed list
            content="Hello world!"
        )
        
        # Verify error message
        assert "❌ Error: Access to channel" in result
        assert "not permitted" in result


class TestSendDMTool:
    """Test send DM tool."""
    
    @pytest.mark.asyncio
    async def test_send_dm_success(self, server_with_tools):
        """Test successful DM sending."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_dm":
                tool_func = tool.handler
                break
        
        assert tool_func is not None
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "id": "user123",
            "bot": False
        }
        mock_discord_client.send_dm.return_value = {
            "id": "dm_msg123",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            user_id="user123",
            content="Hello via DM!"
        )
        
        # Verify the result
        assert "✅ Direct message sent successfully" in result
        assert "testuser" in result
        assert "dm_msg123" in result
        assert "Hello via DM!" in result
        
        # Verify API calls
        mock_discord_client.get_user.assert_called_once_with("user123")
        mock_discord_client.send_dm.assert_called_once_with("user123", "Hello via DM!")
    
    @pytest.mark.asyncio
    async def test_send_dm_user_not_found(self, server_with_tools):
        """Test sending DM to non-existent user."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_dm":
                tool_func = tool.handler
                break
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            user_id="user999",
            content="Hello!"
        )
        
        # Verify error message
        assert "❌ Error: User" in result
        assert "not found" in result
    
    @pytest.mark.asyncio
    async def test_send_dm_blocked(self, server_with_tools):
        """Test sending DM when user has blocked DMs."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "send_dm":
                tool_func = tool.handler
                break
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "id": "user123",
            "bot": False
        }
        mock_discord_client.send_dm.side_effect = DiscordAPIError("Forbidden", 403)
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            user_id="user123",
            content="Hello!"
        )
        
        # Verify error message
        assert "❌ Error: Cannot send DM" in result
        assert "DMs disabled or blocked" in result


class TestDeleteMessageTool:
    """Test delete message tool."""
    
    @pytest.mark.asyncio
    async def test_delete_message_success(self, server_with_tools):
        """Test successful message deletion."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "delete_message":
                tool_func = tool.handler
                break
        
        assert tool_func is not None
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.get_channel_message.return_value = {
            "author": {"username": "testuser"},
            "content": "This message will be deleted"
        }
        mock_discord_client.delete_message.return_value = {}
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            channel_id="ch123",
            message_id="msg123"
        )
        
        # Verify the result
        assert "✅ Message deleted successfully" in result
        assert "general" in result
        assert "testuser" in result
        assert "This message will be deleted" in result
        
        # Verify API calls
        mock_discord_client.get_channel.assert_called_once_with("ch123")
        mock_discord_client.get_channel_message.assert_called_once_with("ch123", "msg123")
        mock_discord_client.delete_message.assert_called_once_with("ch123", "msg123")
    
    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, server_with_tools):
        """Test deleting non-existent message."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "delete_message":
                tool_func = tool.handler
                break
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.get_channel_message.side_effect = DiscordAPIError("Not Found", 404)
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            channel_id="ch123",
            message_id="msg999"
        )
        
        # Verify error message
        assert "❌ Error: Message" in result
        assert "not found" in result


class TestEditMessageTool:
    """Test edit message tool."""
    
    @pytest.mark.asyncio
    async def test_edit_message_success(self, server_with_tools):
        """Test successful message editing."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "edit_message":
                tool_func = tool.handler
                break
        
        assert tool_func is not None
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.get_current_user.return_value = {
            "id": "bot123"
        }
        mock_discord_client.get_channel_message.return_value = {
            "author": {"id": "bot123"},  # Same as bot user ID
            "content": "Original message"
        }
        mock_discord_client.patch.return_value = {
            "id": "msg123",
            "content": "Edited message"
        }
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            channel_id="ch123",
            message_id="msg123",
            new_content="Edited message"
        )
        
        # Verify the result
        assert "✅ Message edited successfully" in result
        assert "Original message" in result
        assert "Edited message" in result
        
        # Verify API calls
        mock_discord_client.patch.assert_called_once_with(
            "/channels/ch123/messages/msg123",
            data={"content": "Edited message"}
        )
    
    @pytest.mark.asyncio
    async def test_edit_message_not_own_message(self, server_with_tools):
        """Test editing message not sent by bot."""
        # Get the tool function
        tool_func = None
        for tool in server_with_tools._tools:
            if tool.name == "edit_message":
                tool_func = tool.handler
                break
        
        # Mock the context and Discord client
        mock_discord_client = AsyncMock()
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123"
        }
        mock_discord_client.get_current_user.return_value = {
            "id": "bot123"
        }
        mock_discord_client.get_channel_message.return_value = {
            "author": {"id": "user456"},  # Different from bot user ID
            "content": "User's message"
        }
        
        # Mock the server's get_context method
        def mock_get_context():
            context = MagicMock()
            context.request_context.lifespan_context = {
                "discord_client": mock_discord_client,
                "settings": Settings(
                    discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    discord_application_id="123456789012345678"
                )
            }
            return context
        
        server_with_tools.get_context = mock_get_context
        
        # Call the tool
        result = await tool_func(
            channel_id="ch123",
            message_id="msg123",
            new_content="Edited message"
        )
        
        # Verify error message
        assert "❌ Error: Can only edit bot's own messages" in result
