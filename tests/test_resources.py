"""
Tests for Discord MCP resources.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context, FastMCP

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError
from discord_mcp.resources import register_resources


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678",
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
        "settings": settings,
    }
    return context


@pytest.fixture
def server_with_resources():
    """Create FastMCP server with resources registered."""
    server = FastMCP("Test Server")
    register_resources(server)
    return server


class TestGuildListingResource:
    """Test guild listing resource."""

    @pytest.mark.asyncio
    async def test_list_guilds_success(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test successful guild listing."""
        # Mock guild data
        mock_guilds = [
            {"id": "123", "name": "Test Guild 1", "owner": True},
            {"id": "456", "name": "Test Guild 2", "owner": False},
        ]
        mock_discord_client.get_user_guilds.return_value = mock_guilds
        mock_discord_client.get_guild.side_effect = [
            {"approximate_member_count": 100, "description": "Test guild 1"},
            {"approximate_member_count": 50, "description": None},
        ]

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "guilds://":
                resource_func = resource.handler
                break

        assert resource_func is not None

        # Call the resource
        result = await resource_func(mock_context)

        # Verify the result
        assert "# Discord Guilds" in result
        assert "Test Guild 1" in result
        assert "Test Guild 2" in result
        assert "123" in result
        assert "456" in result
        assert "100" in result  # Member count

        # Verify API calls
        mock_discord_client.get_user_guilds.assert_called_once()
        assert mock_discord_client.get_guild.call_count == 2

    @pytest.mark.asyncio
    async def test_list_guilds_with_filter(
        self, server_with_resources, mock_context, mock_discord_client, settings
    ):
        """Test guild listing with allowed guilds filter."""
        # Set allowed guilds
        settings.allowed_guilds = "123"

        # Mock guild data
        mock_guilds = [
            {"id": "123", "name": "Allowed Guild", "owner": True},
            {"id": "456", "name": "Blocked Guild", "owner": False},
        ]
        mock_discord_client.get_user_guilds.return_value = mock_guilds
        mock_discord_client.get_guild.return_value = {"approximate_member_count": 100}

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "guilds://":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(mock_context)

        # Verify only allowed guild is shown
        assert "Allowed Guild" in result
        assert "Blocked Guild" not in result
        assert "123" in result
        assert "456" not in result

    @pytest.mark.asyncio
    async def test_list_guilds_api_error(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test guild listing with API error."""
        mock_discord_client.get_user_guilds.side_effect = DiscordAPIError(
            "API Error", 500
        )

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "guilds://":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(mock_context)

        # Verify error handling
        assert "# Error" in result
        assert "Discord API error" in result
        assert "API Error" in result


class TestChannelListingResource:
    """Test channel listing resource."""

    @pytest.mark.asyncio
    async def test_list_channels_success(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test successful channel listing."""
        guild_id = "123"

        # Mock guild and channel data
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_channels = [
            {
                "id": "ch1",
                "name": "general",
                "type": 0,
                "topic": "General chat",
                "position": 0,
            },
            {"id": "ch2", "name": "voice", "type": 2, "position": 1},
            {
                "id": "ch3",
                "name": "announcements",
                "type": 5,
                "topic": "Important updates",
                "position": 2,
            },
        ]
        mock_discord_client.get_guild_channels.return_value = mock_channels

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "channels://{guild_id}":
                resource_func = resource.handler
                break

        assert resource_func is not None

        # Call the resource
        result = await resource_func(guild_id, mock_context)

        # Verify the result
        assert "# Channels in Test Guild" in result
        assert "general" in result
        assert "voice" in result
        assert "announcements" in result
        assert "Text Channels" in result
        assert "Voice Channels" in result
        assert "General chat" in result

        # Verify API calls
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_discord_client.get_guild_channels.assert_called_once_with(guild_id)

    @pytest.mark.asyncio
    async def test_list_channels_guild_not_allowed(
        self, server_with_resources, mock_context, mock_discord_client, settings
    ):
        """Test channel listing with guild not allowed."""
        guild_id = "456"
        settings.allowed_guilds = "123"  # Only allow guild 123

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "channels://{guild_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(guild_id, mock_context)

        # Verify access denied
        assert "# Access Denied" in result
        assert "not permitted" in result

        # Verify no API calls were made
        mock_discord_client.get_guild.assert_not_called()
        mock_discord_client.get_guild_channels.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_channels_guild_not_found(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test channel listing with guild not found."""
        guild_id = "999"

        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not Found", 404)

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "channels://{guild_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(guild_id, mock_context)

        # Verify not found message
        assert "# Guild Not Found" in result
        assert "not found" in result


class TestMessageResource:
    """Test message reading resource."""

    @pytest.mark.asyncio
    async def test_get_messages_success(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test successful message retrieval."""
        channel_id = "ch123"

        # Mock channel and message data
        mock_discord_client.get_channel.return_value = {
            "name": "general",
            "guild_id": "guild123",
        }
        mock_messages = [
            {
                "id": "msg1",
                "content": "Hello world!",
                "author": {"username": "user1", "id": "u1"},
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [],
                "embeds": [],
            },
            {
                "id": "msg2",
                "content": "How are you?",
                "author": {"username": "user2", "id": "u2"},
                "timestamp": "2023-01-01T12:01:00Z",
                "attachments": [{"filename": "image.png"}],
                "embeds": [],
            },
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "messages://{channel_id}":
                resource_func = resource.handler
                break

        assert resource_func is not None

        # Call the resource
        result = await resource_func(channel_id, mock_context)

        # Verify the result
        assert "# Messages in #general" in result
        assert "Hello world!" in result
        assert "How are you?" in result
        assert "user1" in result
        assert "user2" in result
        assert "2023-01-01" in result
        assert "image.png" in result

        # Verify API calls
        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_discord_client.get_channel_messages.assert_called_once_with(
            channel_id, limit=50
        )

    @pytest.mark.asyncio
    async def test_get_messages_channel_not_allowed(
        self, server_with_resources, mock_context, mock_discord_client, settings
    ):
        """Test message retrieval with channel not allowed."""
        channel_id = "ch456"
        settings.allowed_channels = "ch123"  # Only allow ch123

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "messages://{channel_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(channel_id, mock_context)

        # Verify access denied
        assert "# Access Denied" in result
        assert "not permitted" in result

        # Verify no API calls were made
        mock_discord_client.get_channel.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_messages_empty_channel(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test message retrieval from empty channel."""
        channel_id = "ch123"

        mock_discord_client.get_channel.return_value = {
            "name": "empty",
            "guild_id": "guild123",
        }
        mock_discord_client.get_channel_messages.return_value = []

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "messages://{channel_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(channel_id, mock_context)

        # Verify empty message
        assert "# Messages in #empty" in result
        assert "No messages found" in result


class TestUserInfoResource:
    """Test user information resource."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test successful user info retrieval."""
        user_id = "u123"

        # Mock user data
        mock_user = {
            "id": user_id,
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User",
            "bot": False,
            "avatar": "avatar_hash",
            "banner": "banner_hash",
            "accent_color": 0xFF0000,
            "public_flags": 64,
        }
        mock_discord_client.get_user.return_value = mock_user

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "user://{user_id}":
                resource_func = resource.handler
                break

        assert resource_func is not None

        # Call the resource
        result = await resource_func(user_id, mock_context)

        # Verify the result
        assert "# User: testuser" in result
        assert "testuser" in result
        assert "Test User" in result
        assert "#1234" in result
        assert "User" in result  # Type: User
        assert "View Avatar" in result
        assert "View Banner" in result
        assert "#ff0000" in result  # Accent color

        # Verify API call
        mock_discord_client.get_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_user_info_bot(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test user info retrieval for bot user."""
        user_id = "bot123"

        # Mock bot user data
        mock_user = {"id": user_id, "username": "testbot", "bot": True, "avatar": None}
        mock_discord_client.get_user.return_value = mock_user

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "user://{user_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(user_id, mock_context)

        # Verify bot-specific info
        assert "# User: testbot" in result
        assert "Type**: Bot" in result
        assert "Default avatar" in result

    @pytest.mark.asyncio
    async def test_get_user_info_not_found(
        self, server_with_resources, mock_context, mock_discord_client
    ):
        """Test user info retrieval for non-existent user."""
        user_id = "u999"

        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)

        # Get the resource function
        resource_func = None
        for resource in server_with_resources._resources:
            if resource.uri_template == "user://{user_id}":
                resource_func = resource.handler
                break

        # Call the resource
        result = await resource_func(user_id, mock_context)

        # Verify not found message
        assert "# User Not Found" in result
        assert "not found" in result
