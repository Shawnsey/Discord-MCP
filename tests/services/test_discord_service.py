"""
Unit tests for DiscordService implementation.

This module contains comprehensive unit tests for the DiscordService class,
testing all methods in isolation with mocked dependencies.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import structlog

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError, DiscordClient
from discord_mcp.services.discord_service import DiscordService
from discord_mcp.services.interfaces import IDiscordService


class TestDiscordService:
    """Test suite for DiscordService implementation."""

    @pytest.fixture
    def discord_service(self, mock_discord_client, mock_settings, mock_logger):
        """Create a DiscordService instance for testing."""
        return DiscordService(mock_discord_client, mock_settings, mock_logger)

    def test_discord_service_initialization(
        self, mock_discord_client, mock_settings, mock_logger
    ):
        """Test DiscordService initialization with dependencies."""
        service = DiscordService(mock_discord_client, mock_settings, mock_logger)

        assert service._discord_client is mock_discord_client
        assert service._settings is mock_settings
        assert service._logger is mock_logger

    def test_discord_service_implements_interface(self, discord_service):
        """Test that DiscordService implements IDiscordService interface."""
        assert isinstance(discord_service, IDiscordService)

    def test_discord_service_has_all_interface_methods(self, discord_service):
        """Test that DiscordService has all required interface methods."""
        # Check that all abstract methods are implemented
        assert hasattr(discord_service, "get_guilds_formatted")
        assert hasattr(discord_service, "get_channels_formatted")
        assert hasattr(discord_service, "get_messages_formatted")
        assert hasattr(discord_service, "get_user_info_formatted")
        assert hasattr(discord_service, "send_message")
        assert hasattr(discord_service, "send_direct_message")
        assert hasattr(discord_service, "read_direct_messages")
        assert hasattr(discord_service, "delete_message")
        assert hasattr(discord_service, "edit_message")

    # Test error handling methods

    def test_handle_discord_error(self, discord_service, mock_logger):
        """Test centralized Discord API error handling."""
        error = DiscordAPIError("Test error", 500)
        operation = "testing operation"

        result = discord_service._handle_discord_error(error, operation)

        # Check error message format
        assert result.startswith("# Error\n\n")
        assert "Discord API error while testing operation: Test error" in result

        # Check logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Discord API error in testing operation" in call_args[0]

    def test_handle_unexpected_error(self, discord_service, mock_logger):
        """Test centralized unexpected error handling."""
        error = ValueError("Test unexpected error")
        operation = "testing operation"

        result = discord_service._handle_unexpected_error(error, operation)

        # Check error message format
        assert result.startswith("# Error\n\n")
        assert (
            "Unexpected error while testing operation: Test unexpected error" in result
        )

        # Check logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Unexpected error in testing operation" in call_args[0]

    # Test permission validation methods

    def test_validate_guild_permission_allowed(self, discord_service, mock_settings):
        """Test guild permission validation when allowed."""
        guild_id = "123456789012345678"
        mock_settings.is_guild_allowed.return_value = True

        result = discord_service._validate_guild_permission(guild_id)

        assert result is True
        mock_settings.is_guild_allowed.assert_called_once_with(guild_id)

    def test_validate_guild_permission_denied(self, discord_service, mock_settings):
        """Test guild permission validation when denied."""
        guild_id = "123456789012345678"
        mock_settings.is_guild_allowed.return_value = False

        result = discord_service._validate_guild_permission(guild_id)

        assert result is False
        mock_settings.is_guild_allowed.assert_called_once_with(guild_id)

    def test_validate_channel_permission_allowed(self, discord_service, mock_settings):
        """Test channel permission validation when allowed."""
        channel_id = "111111111111111111"
        mock_settings.is_channel_allowed.return_value = True

        result = discord_service._validate_channel_permission(channel_id)

        assert result is True
        mock_settings.is_channel_allowed.assert_called_once_with(channel_id)

    def test_validate_channel_permission_denied(self, discord_service, mock_settings):
        """Test channel permission validation when denied."""
        channel_id = "111111111111111111"
        mock_settings.is_channel_allowed.return_value = False

        result = discord_service._validate_channel_permission(channel_id)

        assert result is False
        mock_settings.is_channel_allowed.assert_called_once_with(channel_id)

    def test_check_allowed_guilds(self, discord_service, mock_settings):
        """Test allowed guilds checking."""
        guild_id = "123456789012345678"
        mock_settings.is_guild_allowed.return_value = True

        result = discord_service._check_allowed_guilds(guild_id)

        assert result is True
        mock_settings.is_guild_allowed.assert_called_once_with(guild_id)

    def test_check_allowed_channels(self, discord_service, mock_settings):
        """Test allowed channels checking."""
        channel_id = "111111111111111111"
        mock_settings.is_channel_allowed.return_value = True

        result = discord_service._check_allowed_channels(channel_id)

        assert result is True
        mock_settings.is_channel_allowed.assert_called_once_with(channel_id)

    # Test permission denied message methods

    def test_get_guild_permission_denied_message(self, discord_service):
        """Test guild permission denied message formatting."""
        guild_id = "123456789012345678"

        result = discord_service._get_guild_permission_denied_message(guild_id)

        expected = f"# Access Denied\n\nAccess to guild `{guild_id}` is not permitted."
        assert result == expected

    def test_get_channel_permission_denied_message(self, discord_service):
        """Test channel permission denied message formatting."""
        channel_id = "111111111111111111"

        result = discord_service._get_channel_permission_denied_message(channel_id)

        expected = (
            f"# Access Denied\n\nAccess to channel `{channel_id}` is not permitted."
        )
        assert result == expected

    def test_get_guild_containing_channel_permission_denied_message(
        self, discord_service
    ):
        """Test guild containing channel permission denied message formatting."""
        channel_id = "111111111111111111"

        result = (
            discord_service._get_guild_containing_channel_permission_denied_message(
                channel_id
            )
        )

        expected = f"# Access Denied\n\nAccess to guild containing channel `{channel_id}` is not permitted."
        assert result == expected

    # Test that service methods are not yet implemented (will be implemented in Milestone 2)

    @pytest.mark.asyncio
    async def test_get_guilds_formatted_success(
        self,
        discord_service,
        mock_discord_client,
        mock_settings,
        sample_guild_data,
        sample_guild_details,
    ):
        """Test successful guild list formatting."""
        # Setup mocks
        mock_discord_client.get_user_guilds.return_value = sample_guild_data
        mock_discord_client.get_guild.return_value = sample_guild_details
        mock_settings.get_allowed_guilds_set.return_value = None

        # Execute
        result = await discord_service.get_guilds_formatted()

        # Verify
        assert "# Discord Guilds" in result
        assert "Test Guild 1" in result
        assert "Test Guild 2" in result
        assert "123456789012345678" in result
        assert "987654321098765432" in result
        mock_discord_client.get_user_guilds.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_guilds_formatted_with_filter(
        self,
        discord_service,
        mock_discord_client,
        mock_settings,
        sample_guild_data,
        sample_guild_details,
    ):
        """Test guild list formatting with allowed guilds filter."""
        # Setup mocks
        mock_discord_client.get_user_guilds.return_value = sample_guild_data
        mock_discord_client.get_guild.return_value = sample_guild_details
        mock_settings.get_allowed_guilds_set.return_value = {"123456789012345678"}

        # Execute
        result = await discord_service.get_guilds_formatted()

        # Verify
        assert "# Discord Guilds" in result
        assert "Test Guild 1" in result
        assert "Test Guild 2" not in result  # Should be filtered out
        mock_discord_client.get_user_guilds.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_guilds_formatted_no_guilds(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test guild list formatting when no guilds are found."""
        # Setup mocks
        mock_discord_client.get_user_guilds.return_value = []
        mock_settings.get_allowed_guilds_set.return_value = None

        # Execute
        result = await discord_service.get_guilds_formatted()

        # Verify
        assert (
            result
            == "# Discord Guilds\n\nNo guilds found or bot has no access to any guilds."
        )
        mock_discord_client.get_user_guilds.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_guilds_formatted_api_error(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test guild list formatting with Discord API error."""
        # Setup mocks
        mock_discord_client.get_user_guilds.side_effect = DiscordAPIError(
            "API Error", 500
        )
        mock_settings.get_allowed_guilds_set.return_value = None

        # Execute
        result = await discord_service.get_guilds_formatted()

        # Verify
        assert result.startswith("# Error\n\n")
        assert "Discord API error while fetching guilds" in result
        mock_discord_client.get_user_guilds.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channels_formatted_success(
        self, discord_service, mock_discord_client, mock_settings, sample_channel_data
    ):
        """Test successful channel list formatting."""
        guild_id = "123456789012345678"
        guild_data = {"name": "Test Guild"}

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_guild_channels.return_value = sample_channel_data
        mock_settings.get_allowed_channels_set.return_value = None

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        assert "# Channels in Test Guild" in result
        assert "general" in result
        assert "voice-chat" in result
        assert "announcements" in result
        assert "Text Channels" in result
        assert "Voice Channels" in result
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_discord_client.get_guild_channels.assert_called_once_with(guild_id)

    @pytest.mark.asyncio
    async def test_get_channels_formatted_guild_not_allowed(
        self, discord_service, mock_settings
    ):
        """Test channel list formatting when guild is not allowed."""
        guild_id = "123456789012345678"

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = False

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        expected = f"# Access Denied\n\nAccess to guild `{guild_id}` is not permitted."
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_channels_formatted_guild_not_found(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test channel list formatting when guild is not found."""
        guild_id = "999999999999999999"

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        assert (
            result
            == f"# Guild Not Found\n\nGuild with ID `{guild_id}` was not found or bot has no access."
        )

    @pytest.mark.asyncio
    async def test_get_channels_formatted_with_filter(
        self, discord_service, mock_discord_client, mock_settings, sample_channel_data
    ):
        """Test channel list formatting with channel filter."""
        guild_id = "123456789012345678"
        guild_data = {"name": "Test Guild"}

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_guild_channels.return_value = sample_channel_data
        mock_settings.get_allowed_channels_set.return_value = {
            "111111111111111111"
        }  # Only allow general channel

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        assert "# Channels in Test Guild" in result
        assert "general" in result
        assert "voice-chat" not in result  # Should be filtered out
        assert "announcements" not in result  # Should be filtered out

    @pytest.mark.asyncio
    async def test_get_channels_formatted_no_channels(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test channel list formatting when no channels are found."""
        guild_id = "123456789012345678"
        guild_data = {"name": "Test Guild"}

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_guild_channels.return_value = []
        mock_settings.get_allowed_channels_set.return_value = None

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        assert (
            result
            == "# Channels in Test Guild\n\nNo accessible channels found in this guild."
        )

    @pytest.mark.asyncio
    async def test_get_channels_formatted_api_error(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test channel list formatting with Discord API error."""
        guild_id = "123456789012345678"

        # Setup mocks
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_guild_channels.side_effect = DiscordAPIError(
            "API Error", 500
        )

        # Execute
        result = await discord_service.get_channels_formatted(guild_id)

        # Verify
        assert result.startswith("# Error\n\n")
        assert "Discord API error while fetching channels" in result

    # Tests for get_messages_formatted method
    @pytest.mark.asyncio
    async def test_get_messages_formatted_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful message retrieval and formatting."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True
        mock_settings.is_guild_allowed.return_value = True

        mock_channel = {
            "id": channel_id,
            "name": "general",
            "guild_id": "987654321098765432",
        }
        mock_discord_client.get_channel.return_value = mock_channel

        mock_messages = [
            {
                "id": "msg1",
                "author": {"username": "user1", "id": "user1_id"},
                "timestamp": "2023-01-01T12:00:00Z",
                "content": "Hello world!",
                "attachments": [],
                "embeds": [],
            },
            {
                "id": "msg2",
                "author": {"username": "user2", "id": "user2_id"},
                "timestamp": "2023-01-01T12:01:00Z",
                "content": "How are you?",
                "attachments": [{"filename": "image.png"}],
                "embeds": [{"title": "Test embed"}],
            },
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Messages in #general" in result
        assert "Showing 2 recent message(s)" in result
        assert "## Message from user1" in result
        assert "## Message from user2" in result
        assert "Hello world!" in result
        assert "How are you?" in result
        assert "2023-01-01 12:00:00 UTC" in result
        assert "2023-01-01 12:01:00 UTC" in result
        assert "**Attachments**: 1 file(s)" in result
        assert "image.png" in result
        assert "**Embeds**: 1 embed(s)" in result

        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_discord_client.get_channel_messages.assert_called_once_with(
            channel_id, limit=50
        )

    @pytest.mark.asyncio
    async def test_get_messages_formatted_with_custom_limit(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test message retrieval with custom limit."""
        # Setup
        channel_id = "123456789012345678"
        custom_limit = 25
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel
        mock_discord_client.get_channel_messages.return_value = []

        # Execute
        await discord_service.get_messages_formatted(channel_id, limit=custom_limit)

        # Verify
        mock_discord_client.get_channel_messages.assert_called_once_with(
            channel_id, limit=custom_limit
        )

    @pytest.mark.asyncio
    async def test_get_messages_formatted_channel_not_allowed(
        self, discord_service, mock_settings
    ):
        """Test access denied for disallowed channel."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = False

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Access Denied" in result
        assert f"Access to channel `{channel_id}` is not permitted" in result

    @pytest.mark.asyncio
    async def test_get_messages_formatted_guild_not_allowed(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test access denied for disallowed guild."""
        # Setup
        channel_id = "123456789012345678"
        guild_id = "987654321098765432"
        mock_settings.is_channel_allowed.return_value = True
        mock_settings.is_guild_allowed.return_value = False

        mock_channel = {"id": channel_id, "name": "general", "guild_id": guild_id}
        mock_discord_client.get_channel.return_value = mock_channel

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Access Denied" in result
        assert (
            f"Access to guild containing channel `{channel_id}` is not permitted"
            in result
        )

    @pytest.mark.asyncio
    async def test_get_messages_formatted_channel_not_found(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test channel not found error handling."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_discord_client.get_channel.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Channel Not Found" in result
        assert (
            f"Channel with ID `{channel_id}` was not found or bot has no access"
            in result
        )

    @pytest.mark.asyncio
    async def test_get_messages_formatted_no_messages(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test handling of empty message list."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "empty-channel"}
        mock_discord_client.get_channel.return_value = mock_channel
        mock_discord_client.get_channel_messages.return_value = []

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Messages in #empty-channel" in result
        assert "No messages found in this channel" in result

    @pytest.mark.asyncio
    async def test_get_messages_formatted_message_without_content(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test formatting of message without text content."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_messages = [
            {
                "id": "msg1",
                "author": {"username": "user1", "id": "user1_id"},
                "timestamp": "2023-01-01T12:00:00Z",
                "content": "",  # Empty content
                "attachments": [],
                "embeds": [],
            }
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "*(No text content)*" in result

    @pytest.mark.asyncio
    async def test_get_messages_formatted_invalid_timestamp(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test handling of invalid timestamp format."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_messages = [
            {
                "id": "msg1",
                "author": {"username": "user1", "id": "user1_id"},
                "timestamp": "invalid-timestamp",
                "content": "Test message",
                "attachments": [],
                "embeds": [],
            }
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "invalid-timestamp" in result  # Should fall back to original timestamp

    @pytest.mark.asyncio
    async def test_get_messages_formatted_missing_author_info(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test handling of missing author information."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_messages = [
            {
                "id": "msg1",
                "author": {},  # Missing username and id
                "timestamp": "2023-01-01T12:00:00Z",
                "content": "Test message",
                "attachments": [],
                "embeds": [],
            }
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "Unknown User" in result
        assert "Unknown" in result

    @pytest.mark.asyncio
    async def test_get_messages_formatted_discord_api_error(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test Discord API error handling during message fetch."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel
        mock_discord_client.get_channel_messages.side_effect = DiscordAPIError(
            "Server Error", 500
        )

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Error" in result
        assert "Discord API error while fetching messages" in result

    @pytest.mark.asyncio
    async def test_get_messages_formatted_unexpected_error(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test unexpected error handling."""
        # Setup
        channel_id = "123456789012345678"
        mock_settings.is_channel_allowed.return_value = True

        mock_discord_client.get_channel.side_effect = ValueError("Unexpected error")

        # Execute
        result = await discord_service.get_messages_formatted(channel_id)

        # Verify
        assert "# Error" in result
        assert "Unexpected error while fetching messages" in result

    # Tests for get_user_info_formatted method
    @pytest.mark.asyncio
    async def test_get_user_info_formatted_success(
        self, discord_service, mock_discord_client
    ):
        """Test successful user info retrieval and formatting."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id,
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User",
            "bot": False,
            "system": False,
            "avatar": "avatar_hash",
            "banner": "banner_hash",
            "accent_color": 16711680,  # Red color
            "public_flags": 64,
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# User: testuser" in result
        assert "**Username**: testuser" in result
        assert f"**User ID**: `{user_id}`" in result
        assert "**Discriminator**: #1234" in result
        assert "**Display Name**: Test User" in result
        assert "**Type**: User" in result
        assert "**Avatar**: [View Avatar](https://cdn.discordapp.com/avatars/" in result
        assert "**Banner**: [View Banner](https://cdn.discordapp.com/banners/" in result
        assert "**Accent Color**: #ff0000" in result
        assert "**Public Flags**: 64" in result

        mock_discord_client.get_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_bot_user(
        self, discord_service, mock_discord_client
    ):
        """Test formatting of bot user information."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id,
            "username": "testbot",
            "discriminator": "0",  # Modern Discord bots use "0"
            "bot": True,
            "system": False,
            "avatar": None,
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# User: testbot" in result
        assert "**Type**: Bot" in result
        assert "**Avatar**: Default avatar" in result
        assert (
            "**Discriminator**" not in result
        )  # Should not show discriminator when it's "0"

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_system_user(
        self, discord_service, mock_discord_client
    ):
        """Test formatting of system user information."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id,
            "username": "systemuser",
            "bot": False,
            "system": True,
            "avatar": None,
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "**System User**: Yes" in result
        assert "**Type**: User" in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_minimal_user(
        self, discord_service, mock_discord_client
    ):
        """Test formatting of user with minimal information."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {"id": user_id, "username": "minimaluser"}
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# User: minimaluser" in result
        assert "**Username**: minimaluser" in result
        assert f"**User ID**: `{user_id}`" in result
        assert "**Type**: User" in result
        assert "**Avatar**: Default avatar" in result
        # Should not contain optional fields
        assert "**Discriminator**" not in result
        assert "**Display Name**" not in result
        assert "**Banner**" not in result
        assert "**Accent Color**" not in result
        assert "**Public Flags**" not in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_same_username_and_display_name(
        self, discord_service, mock_discord_client
    ):
        """Test that display name is not shown when it's the same as username."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id,
            "username": "testuser",
            "global_name": "testuser",  # Same as username
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "**Display Name**" not in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_missing_username(
        self, discord_service, mock_discord_client
    ):
        """Test handling of user with missing username."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id
            # Missing username
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# User: Unknown" in result
        assert "**Username**: Unknown" in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_user_not_found(
        self, discord_service, mock_discord_client
    ):
        """Test user not found error handling."""
        # Setup
        user_id = "123456789012345678"
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# User Not Found" in result
        assert f"User with ID `{user_id}` was not found" in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_discord_api_error(
        self, discord_service, mock_discord_client
    ):
        """Test Discord API error handling."""
        # Setup
        user_id = "123456789012345678"
        mock_discord_client.get_user.side_effect = DiscordAPIError("Server Error", 500)

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# Error" in result
        assert "Discord API error while fetching user info" in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_unexpected_error(
        self, discord_service, mock_discord_client
    ):
        """Test unexpected error handling."""
        # Setup
        user_id = "123456789012345678"
        mock_discord_client.get_user.side_effect = ValueError("Unexpected error")

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "# Error" in result
        assert "Unexpected error while fetching user info" in result

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_accent_color_formatting(
        self, discord_service, mock_discord_client
    ):
        """Test proper formatting of accent color."""
        # Setup
        user_id = "123456789012345678"
        mock_user = {
            "id": user_id,
            "username": "coloruser",
            "accent_color": 255,  # Blue color
        }
        mock_discord_client.get_user.return_value = mock_user

        # Execute
        result = await discord_service.get_user_info_formatted(user_id)

        # Verify
        assert "**Accent Color**: #0000ff" in result  # Should format as hex

    @pytest.mark.asyncio
    async def test_send_message_not_implemented(self, discord_service):
        """Test that send_message raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.send_message("111111111111111111", "test message")

    @pytest.mark.asyncio
    async def test_send_direct_message_not_implemented(self, discord_service):
        """Test that send_direct_message raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.send_direct_message(
                "123456789012345678", "test message"
            )

    @pytest.mark.asyncio
    async def test_read_direct_messages_not_implemented(self, discord_service):
        """Test that read_direct_messages raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.read_direct_messages("123456789012345678")

    @pytest.mark.asyncio
    async def test_delete_message_not_implemented(self, discord_service):
        """Test that delete_message raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.delete_message(
                "111111111111111111", "222222222222222222"
            )

    @pytest.mark.asyncio
    async def test_edit_message_not_implemented(self, discord_service):
        """Test that edit_message raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.edit_message(
                "111111111111111111", "222222222222222222", "new content"
            )


class TestDiscordServiceHelperMethods:
    """Test helper methods and utilities for DiscordService."""

    @pytest.fixture
    def discord_service(self, mock_discord_client, mock_settings, mock_logger):
        """Create a DiscordService instance for testing."""
        return DiscordService(mock_discord_client, mock_settings, mock_logger)

    def test_service_has_required_dependencies(self, discord_service):
        """Test that service has all required dependencies."""
        assert hasattr(discord_service, "_discord_client")
        assert hasattr(discord_service, "_settings")
        assert hasattr(discord_service, "_logger")

    def test_service_dependencies_are_private(self, discord_service):
        """Test that service dependencies are stored as private attributes."""
        # Check that dependencies are private (start with underscore)
        assert discord_service._discord_client is not None
        assert discord_service._settings is not None
        assert discord_service._logger is not None

    def test_service_type_hints(self, discord_service):
        """Test that service has proper type hints."""
        # This test ensures the service was created with proper typing
        assert isinstance(discord_service._discord_client, (DiscordClient, AsyncMock))
        assert isinstance(discord_service._settings, (Settings, Mock))
        assert isinstance(discord_service._logger, (structlog.stdlib.BoundLogger, Mock))
