"""
Tests for the read_direct_messages tool.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.server.fastmcp import FastMCP

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError, DiscordClient
from discord_mcp.tools import register_tools


@pytest.fixture
def mock_server():
    """Create a mock FastMCP server."""
    server = MagicMock(spec=FastMCP)
    server._tools = {}

    # Mock the tool decorator
    def tool_decorator():
        def decorator(func):
            server._tools[func.__name__] = func
            return func

        return decorator

    server.tool = tool_decorator
    return server


@pytest.fixture
def mock_context():
    """Create a mock server context."""
    mock_discord_client = AsyncMock(spec=DiscordClient)
    mock_settings = MagicMock(spec=Settings)

    context = MagicMock()
    context.request_context.lifespan_context = {
        "discord_client": mock_discord_client,
        "settings": mock_settings,
    }

    return context, mock_discord_client, mock_settings


@pytest.mark.asyncio
async def test_read_direct_messages_success(mock_server, mock_context):
    """Test successful direct message reading."""
    context, mock_discord_client, mock_settings = mock_context

    # Register tools
    register_tools(mock_server)

    # Mock server.get_context
    mock_server.get_context.return_value = context

    # Mock Discord API responses
    mock_discord_client.get_user.return_value = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "1234",
    }

    mock_discord_client.create_dm_channel.return_value = {"id": "987654321"}

    mock_discord_client.get_current_user.return_value = {
        "id": "bot123",
        "username": "TestBot",
    }

    mock_discord_client.get_channel_messages.return_value = [
        {
            "id": "msg1",
            "content": "Hello from user",
            "author": {"id": "123456789", "username": "testuser"},
            "timestamp": "2025-08-05T10:00:00Z",
            "embeds": [],
            "attachments": [],
            "reactions": [],
        },
        {
            "id": "msg2",
            "content": "Hello from bot",
            "author": {"id": "bot123", "username": "TestBot"},
            "timestamp": "2025-08-05T10:01:00Z",
            "embeds": [],
            "attachments": [],
            "reactions": [],
        },
    ]

    # Get the tool function
    read_dm_tool = mock_server._tools["read_direct_messages"]

    # Call the tool
    result = await read_dm_tool(user_id="123456789", limit=10)

    # Verify the result
    assert "📬 **Direct Messages with testuser#1234**" in result
    assert "User ID: `123456789`" in result
    assert "DM Channel ID: `987654321`" in result
    assert "Retrieved 2 message(s)" in result
    assert "Hello from user" in result
    assert "Hello from bot" in result
    assert "👤 testuser#1234" in result
    assert "🤖 TestBot (You)" in result

    # Verify API calls
    mock_discord_client.get_user.assert_called_once_with("123456789")
    mock_discord_client.create_dm_channel.assert_called_once_with("123456789")
    mock_discord_client.get_channel_messages.assert_called_once_with(
        "987654321", limit=10
    )


@pytest.mark.asyncio
async def test_read_direct_messages_user_not_found(mock_server, mock_context):
    """Test handling when user is not found."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock user not found error
    mock_discord_client.get_user.side_effect = DiscordAPIError("User not found", 404)

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="invalid_user", limit=10)

    assert "❌ Error: User `invalid_user` not found." in result


@pytest.mark.asyncio
async def test_read_direct_messages_dm_disabled(mock_server, mock_context):
    """Test handling when user has DMs disabled."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock successful user lookup
    mock_discord_client.get_user.return_value = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "1234",
    }

    # Mock DM creation failure
    mock_discord_client.create_dm_channel.side_effect = DiscordAPIError(
        "Cannot send messages to this user", 403
    )

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="123456789", limit=10)

    assert (
        "❌ Error: Cannot create DM channel with testuser#1234. User may have DMs disabled."
        in result
    )


@pytest.mark.asyncio
async def test_read_direct_messages_no_messages(mock_server, mock_context):
    """Test handling when no messages exist."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock successful setup but no messages
    mock_discord_client.get_user.return_value = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "0000",  # New username format
    }

    mock_discord_client.create_dm_channel.return_value = {"id": "987654321"}

    mock_discord_client.get_channel_messages.return_value = []

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="123456789", limit=10)

    assert "📭 No direct messages found with testuser." in result


@pytest.mark.asyncio
async def test_read_direct_messages_with_attachments_and_embeds(
    mock_server, mock_context
):
    """Test handling messages with attachments and embeds."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock setup
    mock_discord_client.get_user.return_value = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "1234",
    }

    mock_discord_client.create_dm_channel.return_value = {"id": "987654321"}

    mock_discord_client.get_current_user.return_value = {
        "id": "bot123",
        "username": "TestBot",
    }

    # Mock message with attachments and embeds
    mock_discord_client.get_channel_messages.return_value = [
        {
            "id": "msg1",
            "content": "Check this out!",
            "author": {"id": "123456789", "username": "testuser"},
            "timestamp": "2025-08-05T10:00:00Z",
            "embeds": [{"title": "Cool Embed", "description": "This is an embed"}],
            "attachments": [
                {"filename": "image.png", "size": 1024},
                {"filename": "document.pdf", "size": 2048},
            ],
            "reactions": [{"emoji": {"name": "👍"}, "count": 1}],
        }
    ]

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="123456789", limit=10)

    assert "Check this out!" in result
    assert "📎 1 embed(s)" in result
    assert "📁 2 attachment(s): image.png, document.pdf" in result
    assert "⭐ 1 reaction(s)" in result


@pytest.mark.asyncio
async def test_read_direct_messages_invalid_limit(mock_server, mock_context):
    """Test handling invalid limit parameters."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    read_dm_tool = mock_server._tools["read_direct_messages"]

    # Test limit too low
    result = await read_dm_tool(user_id="123456789", limit=0)
    assert "❌ Error: Limit must be between 1 and 100." in result

    # Test limit too high
    result = await read_dm_tool(user_id="123456789", limit=101)
    assert "❌ Error: Limit must be between 1 and 100." in result


@pytest.mark.asyncio
async def test_read_direct_messages_long_content_truncation(mock_server, mock_context):
    """Test handling of very long message content."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock setup
    mock_discord_client.get_user.return_value = {
        "id": "123456789",
        "username": "testuser",
        "discriminator": "1234",
    }

    mock_discord_client.create_dm_channel.return_value = {"id": "987654321"}

    mock_discord_client.get_current_user.return_value = {
        "id": "bot123",
        "username": "TestBot",
    }

    # Mock message with very long content
    long_content = "A" * 600  # Longer than 500 char limit
    mock_discord_client.get_channel_messages.return_value = [
        {
            "id": "msg1",
            "content": long_content,
            "author": {"id": "123456789", "username": "testuser"},
            "timestamp": "2025-08-05T10:00:00Z",
            "embeds": [],
            "attachments": [],
            "reactions": [],
        }
    ]

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="123456789", limit=10)

    # Should be truncated
    assert "... (truncated)" in result
    assert len([line for line in result.split("\n") if "AAAA" in line][0]) < len(
        long_content
    )


@pytest.mark.asyncio
async def test_read_direct_messages_unexpected_error(mock_server, mock_context):
    """Test handling of unexpected errors."""
    context, mock_discord_client, mock_settings = mock_context

    register_tools(mock_server)
    mock_server.get_context.return_value = context

    # Mock unexpected error
    mock_discord_client.get_user.side_effect = Exception("Unexpected error")

    read_dm_tool = mock_server._tools["read_direct_messages"]
    result = await read_dm_tool(user_id="123456789", limit=10)

    assert (
        "❌ Unexpected error while reading direct messages: Unexpected error" in result
    )
