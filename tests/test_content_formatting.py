"""
Unit tests for content formatting methods in DiscordService.

This module tests the centralized content formatting methods that extract
formatting logic from the main service methods.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import structlog

from src.discord_mcp.config import Settings
from src.discord_mcp.discord_client import DiscordAPIError, DiscordClient
from src.discord_mcp.services.discord_service import DiscordService


class TestContentFormattingMethods:
    """Test suite for content formatting methods."""

    @pytest.fixture
    def discord_service(self):
        """Create a DiscordService instance for testing."""
        mock_client = AsyncMock(spec=DiscordClient)
        mock_settings = Mock(spec=Settings)
        mock_logger = Mock(spec=structlog.stdlib.BoundLogger)
        return DiscordService(mock_client, mock_settings, mock_logger)

    @pytest.fixture
    def sample_guilds(self):
        """Sample guild data for testing."""
        return [
            {
                "id": "123456789012345678",
                "name": "Test Guild 1",
                "owner": True,
            },
            {
                "id": "987654321098765432", 
                "name": "Test Guild 2",
                "owner": False,
            },
        ]

    @pytest.fixture
    def sample_channels(self):
        """Sample channel data for testing."""
        return [
            {
                "id": "111111111111111111",
                "name": "general",
                "type": 0,
                "topic": "General discussion",
                "position": 0,
                "parent_id": None,
                "nsfw": False,
            },
            {
                "id": "222222222222222222",
                "name": "voice-chat",
                "type": 2,
                "position": 1,
                "parent_id": None,
            },
            {
                "id": "333333333333333333",
                "name": "announcements",
                "type": 5,
                "topic": "Important updates",
                "position": 2,
                "parent_id": "444444444444444444",
                "nsfw": False,
            },
        ]

    @pytest.fixture
    def sample_messages(self):
        """Sample message data for testing."""
        return [
            {
                "id": "msg1",
                "content": "Hello, world!",
                "author": {"id": "user1", "username": "testuser1"},
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [],
                "embeds": [],
            },
            {
                "id": "msg2",
                "content": "How are you doing?",
                "author": {"id": "user2", "username": "testuser2"},
                "timestamp": "2023-01-01T12:01:00Z",
                "attachments": [
                    {"filename": "image.png", "url": "https://example.com/image.png"}
                ],
                "embeds": [{"title": "Test Embed"}],
            },
        ]

    @pytest.fixture
    def sample_user(self):
        """Sample user data for testing."""
        return {
            "id": "123456789012345678",
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User",
            "bot": False,
            "avatar": "avatar_hash_123",
            "banner": "banner_hash_456",
            "accent_color": 16711680,
            "public_flags": 64,
        }

    @pytest.mark.asyncio
    async def test_format_guild_info_with_guilds(self, discord_service, sample_guilds):
        """Test _format_guild_info with valid guild data."""
        # Mock the Discord client to return guild details
        discord_service._discord_client.get_guild.side_effect = [
            {
                "id": "123456789012345678",
                "name": "Test Guild 1",
                "approximate_member_count": 150,
                "description": "A test Discord guild",
                "features": ["COMMUNITY", "NEWS"],
            },
            {
                "id": "987654321098765432",
                "name": "Test Guild 2", 
                "approximate_member_count": 75,
                "description": None,
                "features": [],
            },
        ]

        result = await discord_service._format_guild_info(sample_guilds)

        assert "# Discord Guilds" in result
        assert "Found 2 accessible guild(s)" in result
        assert "## Test Guild 1" in result
        assert "## Test Guild 2" in result
        assert "**ID**: `123456789012345678`" in result
        assert "**Owner**: Yes" in result
        assert "**Owner**: No" in result
        assert "**Member Count**: 150" in result
        assert "**Description**: A test Discord guild" in result
        assert "**Features**: COMMUNITY, NEWS" in result

    @pytest.mark.asyncio
    async def test_format_guild_info_empty_list(self, discord_service):
        """Test _format_guild_info with empty guild list."""
        result = await discord_service._format_guild_info([])

        assert "# Discord Guilds" in result
        assert "No guilds found or bot has no access to any guilds." in result

    @pytest.mark.asyncio
    async def test_format_guild_info_custom_title(self, discord_service, sample_guilds):
        """Test _format_guild_info with custom title."""
        discord_service._discord_client.get_guild.return_value = {
            "id": "123456789012345678",
            "name": "Test Guild 1",
            "approximate_member_count": 150,
            "description": "A test Discord guild",
            "features": [],
        }

        result = await discord_service._format_guild_info(sample_guilds, "My Custom Guilds")

        assert "# My Custom Guilds" in result
        assert "Found 2 accessible guild(s)" in result

    @pytest.mark.asyncio
    async def test_format_guild_info_api_error(self, discord_service, sample_guilds):
        """Test _format_guild_info when guild details API call fails."""
        discord_service._discord_client.get_guild.side_effect = DiscordAPIError(
            "Guild not found", 404
        )

        result = await discord_service._format_guild_info(sample_guilds)

        assert "# Discord Guilds" in result
        assert "**Details**: Unable to fetch additional details" in result

    def test_format_channel_info_with_channels(self, discord_service, sample_channels):
        """Test _format_channel_info with valid channel data."""
        result = discord_service._format_channel_info(sample_channels, "Test Guild")

        assert "# Channels in Test Guild" in result
        assert "Found 3 accessible channel(s)" in result
        assert "## Text Channels" in result
        assert "## Voice Channels" in result
        assert "## Announcement Channels" in result
        assert "### general" in result
        assert "### voice-chat" in result
        assert "### announcements" in result
        assert "**Topic**: General discussion" in result
        assert "**Topic**: Important updates" in result
        assert "**Category**: 444444444444444444" in result
        assert "**Position**: 0" in result

    def test_format_channel_info_empty_list(self, discord_service):
        """Test _format_channel_info with empty channel list."""
        result = discord_service._format_channel_info([], "Test Guild")

        assert "# Channels in Test Guild" in result
        assert "No accessible channels found in this guild." in result

    def test_format_channel_info_unknown_type(self, discord_service):
        """Test _format_channel_info with unknown channel type."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "unknown-channel",
                "type": 99,  # Unknown type
                "position": 0,
            }
        ]

        result = discord_service._format_channel_info(channels, "Test Guild")

        assert "## Type 99" in result
        assert "### unknown-channel" in result

    def test_format_message_info_with_messages(self, discord_service, sample_messages):
        """Test _format_message_info with valid message data."""
        result = discord_service._format_message_info(sample_messages, "general")

        assert "# Messages in #general" in result
        assert "Showing 2 recent message(s)" in result
        assert "## Message from testuser1" in result
        assert "## Message from testuser2" in result
        assert "**Author**: testuser1 (`user1`)" in result
        assert "**Author**: testuser2 (`user2`)" in result
        assert "**Message ID**: `msg1`" in result
        assert "**Message ID**: `msg2`" in result
        assert "Hello, world!" in result
        assert "How are you doing?" in result
        assert "**Attachments**: 1 file(s)" in result
        assert "image.png" in result
        assert "**Embeds**: 1 embed(s)" in result

    def test_format_message_info_empty_list(self, discord_service):
        """Test _format_message_info with empty message list."""
        result = discord_service._format_message_info([], "general")

        assert "# Messages in #general" in result
        assert "No messages found in this channel." in result

    def test_format_message_info_no_content(self, discord_service):
        """Test _format_message_info with message having no content."""
        messages = [
            {
                "id": "msg1",
                "content": "",
                "author": {"id": "user1", "username": "testuser1"},
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [],
                "embeds": [],
            }
        ]

        result = discord_service._format_message_info(messages, "general")

        assert "**Content**: *(No text content)*" in result

    def test_format_message_info_missing_author(self, discord_service):
        """Test _format_message_info with missing author information."""
        messages = [
            {
                "id": "msg1",
                "content": "Test message",
                "author": {},
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [],
                "embeds": [],
            }
        ]

        result = discord_service._format_message_info(messages, "general")

        assert "## Message from Unknown User" in result
        assert "**Author**: Unknown (`Unknown`)" in result

    def test_format_user_info_complete_user(self, discord_service, sample_user):
        """Test _format_user_info with complete user data."""
        result = discord_service._format_user_info(sample_user)

        assert "# User: testuser" in result
        assert "**Username**: testuser" in result
        assert "**User ID**: `123456789012345678`" in result
        assert "**Discriminator**: #1234" in result
        assert "**Display Name**: Test User" in result
        assert "**Type**: User" in result
        assert "**Avatar**: [View Avatar](https://cdn.discordapp.com/avatars/123456789012345678/avatar_hash_123.png)" in result
        assert "**Banner**: [View Banner](https://cdn.discordapp.com/banners/123456789012345678/banner_hash_456.png)" in result
        assert "**Accent Color**: #ff0000" in result
        assert "**Public Flags**: 64" in result

    def test_format_user_info_bot_user(self, discord_service):
        """Test _format_user_info with bot user data."""
        bot_user = {
            "id": "bot123456789012345678",
            "username": "testbot",
            "discriminator": "0000",
            "bot": True,
            "system": True,
            "avatar": None,
        }

        result = discord_service._format_user_info(bot_user)

        assert "# User: testbot" in result
        assert "**Type**: Bot" in result
        assert "**System User**: Yes" in result
        assert "**Avatar**: Default avatar" in result

    def test_format_user_info_minimal_data(self, discord_service):
        """Test _format_user_info with minimal user data."""
        minimal_user = {
            "id": "123456789012345678",
            "username": "minimaluser",
        }

        result = discord_service._format_user_info(minimal_user)

        assert "# User: minimaluser" in result
        assert "**Username**: minimaluser" in result
        assert "**User ID**: `123456789012345678`" in result
        assert "**Type**: User" in result
        assert "**Avatar**: Default avatar" in result

    def test_format_user_info_with_fallback_id(self, discord_service):
        """Test _format_user_info with fallback user ID."""
        user_without_id = {
            "username": "testuser",
        }

        result = discord_service._format_user_info(user_without_id, "fallback_id_123")

        assert "**User ID**: `fallback_id_123`" in result

    def test_format_user_info_new_username_format(self, discord_service):
        """Test _format_user_info with new Discord username format (no discriminator)."""
        new_format_user = {
            "id": "123456789012345678",
            "username": "newformatuser",
            "discriminator": "0",
            "global_name": "New Format User",
        }

        result = discord_service._format_user_info(new_format_user)

        assert "# User: newformatuser" in result
        assert "**Display Name**: New Format User" in result
        # Should not include discriminator section for "0"
        assert "**Discriminator**" not in result