"""
Unit tests for DiscordService implementation.

This module contains comprehensive unit tests for the DiscordService class,
testing all methods in isolation with mocked dependencies.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import structlog

from src.discord_mcp.config import Settings
from src.discord_mcp.discord_client import DiscordAPIError, DiscordClient
from src.discord_mcp.services.discord_service import DiscordService
from src.discord_mcp.services.interfaces import IDiscordService


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

    def test_handle_discord_error_basic(self, discord_service, mock_logger):
        """Test centralized Discord API error handling without resource info."""
        error = DiscordAPIError("Test error", 500)
        operation = "testing operation"

        result = discord_service._handle_discord_error(error, operation)

        # Check error message format
        assert result.startswith("❌ Error:")
        assert "Discord API error while testing operation: Test error" in result

        # Check logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Discord API error in testing operation" in call_args[0]

    def test_handle_discord_error_with_resource_info(self, discord_service, mock_logger):
        """Test centralized Discord API error handling with resource info."""
        error = DiscordAPIError("Not found", 404)
        operation = "testing operation"
        resource_type = "Guild"
        resource_id = "123456789012345678"

        result = discord_service._handle_discord_error(error, operation, resource_type, resource_id)

        # Check that it uses the centralized not found response
        assert "# Guild Not Found" in result
        assert f"Guild with ID `{resource_id}` was not found" in result

        # Check logging was called with resource info
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["resource_type"] == resource_type
        assert call_args[1]["resource_id"] == resource_id

    def test_handle_discord_error_permission_denied_with_resource(self, discord_service, mock_logger):
        """Test Discord API error handling for permission denied with resource info."""
        error = DiscordAPIError("Forbidden", 403)
        operation = "testing operation"
        resource_type = "Channel"
        resource_id = "111111111111111111"

        result = discord_service._handle_discord_error(error, operation, resource_type, resource_id)

        # Check that it uses the centralized permission denied response
        assert "# Access Denied" in result
        assert f"Access to channel `{resource_id}` is not permitted" in result

    def test_handle_discord_error_rate_limit(self, discord_service, mock_logger):
        """Test Discord API error handling for rate limit."""
        error = DiscordAPIError("Rate limited", 429)
        operation = "testing operation"

        result = discord_service._handle_discord_error(error, operation)

        assert "❌ Error: Rate limit exceeded while testing operation" in result

    def test_handle_discord_error_bad_request(self, discord_service, mock_logger):
        """Test Discord API error handling for bad request."""
        error = DiscordAPIError("Bad request", 400)
        operation = "testing operation"

        result = discord_service._handle_discord_error(error, operation)

        assert "❌ Error: Invalid request while testing operation" in result

    def test_handle_unexpected_error_basic(self, discord_service, mock_logger):
        """Test centralized unexpected error handling without context."""
        error = ValueError("Test unexpected error")
        operation = "testing operation"

        result = discord_service._handle_unexpected_error(error, operation)

        # Check error message format
        assert result.startswith("❌ Unexpected error")
        assert (
            "Unexpected error while testing operation: Test unexpected error" in result
        )

        # Check logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Unexpected error in testing operation" in call_args[0]

    def test_handle_unexpected_error_with_context(self, discord_service, mock_logger):
        """Test centralized unexpected error handling with context."""
        error = ValueError("Test unexpected error")
        operation = "testing operation"
        context = "Additional context information"

        result = discord_service._handle_unexpected_error(error, operation, context)

        # Check error message format includes context
        assert "Context: Additional context information" in result

        # Check logging was called with context
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["context"] == context

    def test_create_permission_denied_response_basic(self, discord_service, mock_logger):
        """Test centralized permission denied response creation."""
        resource_type = "guild"
        resource_id = "123456789012345678"

        result = discord_service._create_permission_denied_response(resource_type, resource_id)

        assert "# Access Denied" in result
        assert f"Access to {resource_type} `{resource_id}` is not permitted" in result

        # Check logging was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[1]["resource_type"] == resource_type
        assert call_args[1]["resource_id"] == resource_id

    def test_create_permission_denied_response_with_context(self, discord_service, mock_logger):
        """Test centralized permission denied response creation with context."""
        resource_type = "channel"
        resource_id = "111111111111111111"
        context = "Additional permission context"

        result = discord_service._create_permission_denied_response(resource_type, resource_id, context)

        assert "# Access Denied" in result
        assert f"Access to {resource_type} `{resource_id}` is not permitted. {context}" in result

    def test_create_not_found_response_basic(self, discord_service, mock_logger):
        """Test centralized not found response creation."""
        resource_type = "User"
        resource_id = "999999999999999999"

        result = discord_service._create_not_found_response(resource_type, resource_id)

        assert f"# {resource_type} Not Found" in result
        assert f"{resource_type} with ID `{resource_id}` was not found or bot has no access" in result

        # Check logging was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[1]["resource_type"] == resource_type
        assert call_args[1]["resource_id"] == resource_id

    def test_create_not_found_response_with_context(self, discord_service, mock_logger):
        """Test centralized not found response creation with context."""
        resource_type = "Message"
        resource_id = "888888888888888888"
        context = "Message may have been deleted"

        result = discord_service._create_not_found_response(resource_type, resource_id, context)

        assert f"# {resource_type} Not Found" in result
        assert f"{resource_type} with ID `{resource_id}` was not found. {context}" in result

    def test_create_validation_error_response_basic(self, discord_service, mock_logger):
        """Test centralized validation error response creation."""
        validation_type = "Message content"
        details = "Content cannot be empty"

        result = discord_service._create_validation_error_response(validation_type, details)

        assert "❌ Error: Message content validation failed. Content cannot be empty" in result

        # Check logging was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[1]["validation_type"] == validation_type
        assert call_args[1]["details"] == details

    def test_create_validation_error_response_with_suggestions(self, discord_service, mock_logger):
        """Test centralized validation error response creation with suggestions."""
        validation_type = "Message length"
        details = "Content too long (2500 characters)"
        suggestions = "Please shorten your message to under 2000 characters"

        result = discord_service._create_validation_error_response(validation_type, details, suggestions)

        assert "❌ Error: Message length validation failed. Content too long (2500 characters)" in result
        assert "**Suggestions:**" in result
        assert "Please shorten your message to under 2000 characters" in result



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
        assert result.startswith("❌ Error:")
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
        assert result.startswith("❌ Error:")
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
        assert f"Access required for channel `{channel_id}`" in result

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
        assert "❌ Error:" in result
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
        assert "❌ Unexpected error" in result
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

    # Tests for moderation methods

    # Tests for timeout_user method
    @pytest.mark.asyncio
    async def test_timeout_user_success(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test successful user timeout."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        duration_minutes = 30
        reason = "Disruptive behavior"
        
        mock_settings.is_guild_allowed.return_value = True
        guild_info_with_roles = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.get_guild.return_value = guild_info_with_roles
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role2"]},  # Target member (first call in _validate_moderation_target)
            {"roles": ["role1"]},  # Bot member (first call in _validate_role_hierarchy)
            {"roles": ["role2"]}   # Target member (second call in _validate_role_hierarchy)
        ]
        mock_discord_client.edit_guild_member.return_value = None

        # Execute
        result = await discord_service.timeout_user(guild_id, user_id, duration_minutes, reason)

        # Verify
        assert "✅ User timed out successfully!" in result
        assert "Test User" in result
        assert "Test Guild" in result
        assert "30 minutes" in result
        assert "Disruptive behavior" in result
        
        # Verify Discord client calls
        mock_discord_client.edit_guild_member.assert_called_once()
        call_args = mock_discord_client.edit_guild_member.call_args
        assert call_args[1]["guild_id"] == guild_id
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["reason"] == reason
        assert "communication_disabled_until" in call_args[1]
        
        # Verify logging
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_timeout_user_invalid_duration_too_short(self, discord_service):
        """Test timeout with duration too short."""
        result = await discord_service.timeout_user("guild_id", "user_id", 0)
        assert "❌ Error: Timeout duration must be at least 1 minute." in result

    @pytest.mark.asyncio
    async def test_timeout_user_invalid_duration_too_long(self, discord_service):
        """Test timeout with duration too long."""
        result = await discord_service.timeout_user("guild_id", "user_id", 50000)
        assert "❌ Error: Timeout duration cannot exceed 28 days" in result
        assert "40320 minutes" in result

    @pytest.mark.asyncio
    async def test_timeout_user_guild_not_allowed(
        self, discord_service, mock_settings
    ):
        """Test timeout when guild is not allowed."""
        guild_id = "123456789012345678"
        mock_settings.is_guild_allowed.return_value = False
        
        result = await discord_service.timeout_user(guild_id, "user_id", 10)
        
        assert "# Access Denied" in result
        assert f"Access to guild `{guild_id}` is not permitted" in result

    @pytest.mark.asyncio
    async def test_timeout_user_guild_not_found(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when guild is not found."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not Found", 404)
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "Guild with ID `guild_id` was not found or bot has no access." in result

    @pytest.mark.asyncio
    async def test_timeout_user_guild_access_denied(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when guild access is denied."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Forbidden", 403)
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "Bot does not have permission to access guild `guild_id`." in result

    @pytest.mark.asyncio
    async def test_timeout_user_user_not_found(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when user is not found."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Error: User `user_id` not found." in result

    @pytest.mark.asyncio
    async def test_timeout_user_role_hierarchy_violation(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when role hierarchy prevents action."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        # Mock guild with roles where target has higher role
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 3, "name": "Bot Role"},
                {"id": "role2", "position": 5, "name": "Admin Role"}  # Higher position
            ]
        }
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Error: Cannot moderate `Test User` due to role hierarchy restrictions." in result
        assert "Bot's highest role" in result
        assert "Target user's highest role" in result

    @pytest.mark.asyncio
    async def test_timeout_user_missing_permissions(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when bot lacks moderate_members permission."""
        # Setup successful validation but API call fails with permission error
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.edit_guild_member.side_effect = DiscordAPIError(
            "Missing Permissions", 403
        )
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Error: Bot does not have 'moderate_members' permission in Test Guild." in result

    @pytest.mark.asyncio
    async def test_timeout_user_user_not_in_guild(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when user is not in guild."""
        # Setup successful validation but API call fails with 404
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.edit_guild_member.side_effect = DiscordAPIError(
            "Not Found", 404
        )
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Error: User `user_id` is not a member of Test Guild." in result

    @pytest.mark.asyncio
    async def test_timeout_user_already_timed_out(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test timeout when user is already timed out."""
        # Setup successful validation but API call fails with 400
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.edit_guild_member.side_effect = DiscordAPIError(
            "Bad Request", 400
        )
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Error: Invalid timeout request. User may already be timed out or parameters are invalid." in result

    @pytest.mark.asyncio
    async def test_timeout_user_unexpected_error(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test timeout with unexpected error."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.side_effect = ValueError("Unexpected error")
        
        result = await discord_service.timeout_user("guild_id", "user_id", 10)
        
        assert "❌ Unexpected error while timing out user: Unexpected error" in result
        mock_logger.error.assert_called()

    # Tests for untimeout_user method
    @pytest.mark.asyncio
    async def test_untimeout_user_success(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test successful user untimeout."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        reason = "Timeout period served"
        
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]},  # Target member
            {"communication_disabled_until": "2024-01-15T14:30:00Z"}  # Member with timeout
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.edit_guild_member.return_value = None

        # Execute
        result = await discord_service.untimeout_user(guild_id, user_id, reason)

        # Verify
        assert "✅ User timeout removed successfully!" in result
        assert "Test User" in result
        assert "Test Guild" in result
        assert "Timeout period served" in result
        assert "2024-01-15 14:30:00 UTC" in result
        
        # Verify Discord client calls
        mock_discord_client.edit_guild_member.assert_called_once()
        call_args = mock_discord_client.edit_guild_member.call_args
        assert call_args[1]["guild_id"] == guild_id
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["reason"] == reason
        assert call_args[1]["communication_disabled_until"] is None
        
        # Verify logging
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_untimeout_user_not_timed_out(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test untimeout when user is not currently timed out."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]},  # Target member
            {"communication_disabled_until": None}  # Member without timeout
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        
        result = await discord_service.untimeout_user("guild_id", "user_id")
        
        assert "ℹ️ User Test User is not currently timed out in Test Guild." in result

    # Tests for kick_user method
    @pytest.mark.asyncio
    async def test_kick_user_success(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test successful user kick."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        reason = "Violation of rules"
        
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role2"]},  # Member exists check
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.kick_guild_member.return_value = None

        # Execute
        result = await discord_service.kick_user(guild_id, user_id, reason)

        # Verify
        assert "✅ User kicked successfully!" in result
        assert "Test User" in result
        assert "Test Guild" in result
        assert "Violation of rules" in result
        
        # Verify Discord client calls
        mock_discord_client.kick_guild_member.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            reason=reason
        )
        
        # Verify logging
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_kick_user_not_in_guild(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test kick when user is not in guild."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Not Found", 404)
        
        result = await discord_service.kick_user("guild_id", "user_id")
        
        assert "❌ Error: User `user_id` is not a member of Test Guild." in result

    @pytest.mark.asyncio
    async def test_kick_user_missing_permissions(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test kick when bot lacks kick_members permission."""
        # Setup successful validation but API call fails with permission error
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role2"]},  # Member exists check
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.kick_guild_member.side_effect = DiscordAPIError(
            "kick_members permission required", 403
        )
        
        result = await discord_service.kick_user("guild_id", "user_id")
        
        assert "❌ Error: Bot does not have 'kick_members' permission in Test Guild." in result

    # Tests for ban_user method
    @pytest.mark.asyncio
    async def test_ban_user_success(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test successful user ban."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        reason = "Repeated violations"
        delete_message_days = 3
        
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get.side_effect = DiscordAPIError("Not Found", 404)  # Not banned
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        mock_discord_client.ban_guild_member.return_value = None

        # Execute
        result = await discord_service.ban_user(guild_id, user_id, reason, delete_message_days)

        # Verify
        assert "✅ User banned successfully!" in result
        assert "Test User" in result
        assert "Test Guild" in result
        assert "Repeated violations" in result
        assert "3 day(s) of messages deleted" in result
        
        # Verify Discord client calls
        mock_discord_client.ban_guild_member.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            reason=reason,
            delete_message_days=delete_message_days
        )
        
        # Verify logging
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_ban_user_invalid_delete_days_negative(self, discord_service):
        """Test ban with invalid negative delete_message_days."""
        result = await discord_service.ban_user("guild_id", "user_id", None, -1)
        assert "❌ Error: delete_message_days must be between 0 and 7 (got -1)." in result

    @pytest.mark.asyncio
    async def test_ban_user_invalid_delete_days_too_high(self, discord_service):
        """Test ban with invalid high delete_message_days."""
        result = await discord_service.ban_user("guild_id", "user_id", None, 8)
        assert "❌ Error: delete_message_days must be between 0 and 7 (got 8)." in result

    @pytest.mark.asyncio
    async def test_ban_user_already_banned(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test ban when user is already banned."""
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get.return_value = {"user": {"id": "user_id"}}  # Already banned
        
        result = await discord_service.ban_user("guild_id", "user_id")
        
        assert "❌ Error: User `Test User` (`user_id`) is already banned from Test Guild." in result

    @pytest.mark.asyncio
    async def test_ban_user_not_in_guild_success(
        self, discord_service, mock_discord_client, mock_settings, mock_logger
    ):
        """Test ban when user is not in guild (should still work)."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get.side_effect = DiscordAPIError("Not Found", 404)  # Not banned
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Not Found", 404)  # Not in guild
        mock_discord_client.ban_guild_member.return_value = None

        # Execute
        result = await discord_service.ban_user(guild_id, user_id)

        # Verify - should succeed even if user not in guild
        assert "✅ User banned successfully!" in result
        mock_discord_client.ban_guild_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_ban_user_missing_permissions(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test ban when bot lacks ban_members permission."""
        # Setup successful validation but API call fails with permission error
        mock_settings.is_guild_allowed.return_value = True
        mock_discord_client.get_guild.return_value = {"name": "Test Guild"}
        mock_discord_client.get_user.return_value = {
            "username": "testuser",
            "global_name": "Test User"
        }
        mock_discord_client.get.side_effect = DiscordAPIError("Not Found", 404)  # Not banned
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Not Found", 404)  # Not in guild
        mock_discord_client.ban_guild_member.side_effect = DiscordAPIError(
            "ban_members permission required", 403
        )
        
        result = await discord_service.ban_user("guild_id", "user_id")
        
        assert "❌ Error: Bot does not have 'ban_members' permission in Test Guild." in result

    # Tests for role hierarchy validation
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_success(
        self, discord_service, mock_discord_client
    ):
        """Test successful role hierarchy validation."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "roles": [
                {"id": "role1", "position": 5, "name": "Bot Role"},
                {"id": "role2", "position": 3, "name": "User Role"}
            ]
        }
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert result is None  # No error means validation passed

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_bot_lower_role(
        self, discord_service, mock_discord_client
    ):
        """Test role hierarchy validation when bot has lower role."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.return_value = {
            "roles": [
                {"id": "role1", "position": 3, "name": "Bot Role"},
                {"id": "role2", "position": 5, "name": "Admin Role"}  # Higher position
            ]
        }
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: Cannot moderate `Test User` due to role hierarchy restrictions." in result
        assert "**Bot's highest role**: Bot Role (position 3)" in result
        assert "**Target user's highest role**: Admin Role (position 5)" in result

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_equal_roles(
        self, discord_service, mock_discord_client
    ):
        """Test role hierarchy validation when roles are equal."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role1"]}   # Target member (same role)
        ]
        mock_discord_client.get_guild.return_value = {
            "roles": [
                {"id": "role1", "position": 5, "name": "Same Role"}
            ]
        }
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: Cannot moderate `Test User` due to role hierarchy restrictions." in result

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_target_not_in_guild(
        self, discord_service, mock_discord_client
    ):
        """Test role hierarchy validation when target user is not in guild."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            DiscordAPIError("Not Found", 404)  # Target member not found
        ]
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: User `Test User` (`987654321098765432`) is not a member of Test Guild." in result

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_bot_info_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test role hierarchy validation when bot info cannot be retrieved."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Server Error", 500)
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: Could not validate bot permissions in Test Guild." in result
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_guild_roles_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test role hierarchy validation when guild roles cannot be retrieved."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Server Error", 500)
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: Could not validate role hierarchy in Test Guild." in result
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_unexpected_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test role hierarchy validation with unexpected error."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.side_effect = ValueError("Unexpected error")
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        assert "❌ Error: Could not validate role hierarchy: Unexpected error" in result
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_no_roles(
        self, discord_service, mock_discord_client
    ):
        """Test role hierarchy validation when users have no roles (only @everyone)."""
        guild_id = "123456789012345678"
        target_user_id = "987654321098765432"
        guild_name = "Test Guild"
        target_username = "Test User"
        
        mock_discord_client.get_current_user.return_value = {"id": "bot_user_id"}
        mock_discord_client.get_guild_member.side_effect = [
            {"roles": []},  # Bot member with no roles
            {"roles": []}   # Target member with no roles
        ]
        mock_discord_client.get_guild.return_value = {"roles": []}
        
        result = await discord_service._validate_role_hierarchy(
            guild_id, target_user_id, guild_name, target_username
        )
        
        # Both have @everyone role (position -1), so bot cannot moderate
        assert "❌ Error: Cannot moderate `Test User` due to role hierarchy restrictions." in result
        assert "@everyone" in result
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
        assert "❌ Error:" in result
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
        assert "❌ Unexpected error" in result
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
    # Tests for send_message method
    async def test_send_message_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful message sending."""
        # Setup
        channel_id = "123456789012345678"
        content = "Hello, world!"
        mock_settings.is_channel_allowed.return_value = True
        mock_settings.is_guild_allowed.return_value = True

        mock_channel = {
            "id": channel_id,
            "name": "general",
            "guild_id": "987654321098765432",
        }
        mock_discord_client.get_channel.return_value = mock_channel

        mock_result = {"id": "msg123", "timestamp": "2023-01-01T12:00:00Z"}
        mock_discord_client.send_message.return_value = mock_result

        # Execute
        result = await discord_service.send_message(channel_id, content)

        # Verify
        assert "✅ Message sent successfully to #general!" in result
        assert "Message ID**: `msg123`" in result
        assert "Channel**: #general (`123456789012345678`)" in result
        assert "Content**: Hello, world!" in result
        assert "Sent at**: 2023-01-01T12:00:00Z" in result

        mock_discord_client.send_message.assert_called_once_with(
            channel_id=channel_id, content=content, message_reference=None
        )

    @pytest.mark.asyncio
    async def test_send_message_with_reply(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test message sending with reply."""
        # Setup
        channel_id = "123456789012345678"
        content = "This is a reply"
        reply_to = "reply123"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_result = {"id": "msg123", "timestamp": "2023-01-01T12:00:00Z"}
        mock_discord_client.send_message.return_value = mock_result

        # Execute
        result = await discord_service.send_message(channel_id, content, reply_to)

        # Verify
        assert "Reply to**: `reply123`" in result
        mock_discord_client.send_message.assert_called_once_with(
            channel_id=channel_id,
            content=content,
            message_reference={"message_id": reply_to, "channel_id": channel_id},
        )

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, discord_service):
        """Test sending message with empty content."""
        result = await discord_service.send_message("123", "")
        assert "❌ Error: Message content validation failed" in result
        assert "Content cannot be empty" in result

    @pytest.mark.asyncio
    async def test_send_message_content_too_long(self, discord_service):
        """Test sending message with content too long."""
        long_content = "a" * 2001
        result = await discord_service.send_message("123", long_content)
        assert "❌ Error: Message content validation failed" in result
        assert "Content too long (2001 characters)" in result

    @pytest.mark.asyncio
    async def test_send_message_channel_not_allowed(
        self, discord_service, mock_settings
    ):
        """Test sending message to disallowed channel."""
        mock_settings.is_channel_allowed.return_value = False
        result = await discord_service.send_message("123", "test")
        assert "# Access Denied" in result
        assert "Access to channel `123` is not permitted" in result

    # Tests for send_direct_message method
    @pytest.mark.asyncio
    async def test_send_direct_message_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful DM sending."""
        # Setup
        user_id = "123456789012345678"
        content = "Hello DM!"

        mock_user = {"id": user_id, "username": "testuser", "bot": False}
        mock_discord_client.get_user.return_value = mock_user

        mock_result = {"id": "dm123", "timestamp": "2023-01-01T12:00:00Z"}
        mock_discord_client.send_dm.return_value = mock_result

        # Execute
        result = await discord_service.send_direct_message(user_id, content)

        # Verify
        assert "✅ Direct message sent successfully to testuser!" in result
        assert "Message ID**: `dm123`" in result
        assert "Recipient**: testuser (`123456789012345678`)" in result
        assert "Content**: Hello DM!" in result

        mock_discord_client.send_dm.assert_called_once_with(user_id, content)

    @pytest.mark.asyncio
    async def test_send_direct_message_user_not_found(
        self, discord_service, mock_discord_client
    ):
        """Test DM to non-existent user."""
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)
        result = await discord_service.send_direct_message("123", "test")
        assert "❌ Error: User `123` not found." in result

    @pytest.mark.asyncio
    async def test_read_direct_messages_success(
        self, discord_service, mock_discord_client
    ):
        """Test successful DM reading."""
        # Setup
        user_id = "123456789012345678"

        mock_user = {"id": user_id, "username": "testuser", "discriminator": "1234"}
        mock_discord_client.get_user.return_value = mock_user

        mock_dm_channel = {"id": "dm_channel_123"}
        mock_discord_client.create_dm_channel.return_value = mock_dm_channel

        mock_bot_user = {"id": "bot123", "username": "TestBot"}
        mock_discord_client.get_current_user.return_value = mock_bot_user

        mock_messages = [
            {
                "id": "msg1",
                "author": {"id": user_id, "username": "testuser"},
                "content": "Hello bot!",
                "timestamp": "2023-01-01T12:00:00Z",
                "embeds": [],
                "attachments": [],
                "reactions": [],
            }
        ]
        mock_discord_client.get_channel_messages.return_value = mock_messages

        # Execute
        result = await discord_service.read_direct_messages(user_id)

        # Verify
        assert "📬 **Direct Messages with testuser#1234**" in result
        assert "DM Channel ID: `dm_channel_123`" in result
        assert "Retrieved 1 message(s)" in result
        assert "👤 testuser#1234" in result
        assert "Hello bot!" in result

    @pytest.mark.asyncio
    async def test_read_direct_messages_invalid_limit(self, discord_service):
        """Test DM reading with invalid limit."""
        result = await discord_service.read_direct_messages("123", limit=101)
        assert "❌ Error: Limit must be between 1 and 100." in result

    @pytest.mark.asyncio
    async def test_delete_message_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful message deletion."""
        # Setup
        channel_id = "123456789012345678"
        message_id = "msg123"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_message = {
            "id": message_id,
            "author": {"username": "testuser"},
            "content": "Test message content",
        }
        mock_discord_client.get_channel_message.return_value = mock_message

        mock_discord_client.delete_message.return_value = None

        # Execute
        result = await discord_service.delete_message(channel_id, message_id)

        # Verify
        assert "✅ Message deleted successfully from #general!" in result
        assert "Message ID**: `msg123`" in result
        assert "Author**: testuser" in result
        assert "Content**: Test message content" in result

        mock_discord_client.delete_message.assert_called_once_with(
            channel_id, message_id
        )

    @pytest.mark.asyncio
    async def test_delete_message_not_found(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test deleting non-existent message."""
        mock_settings.is_channel_allowed.return_value = True
        mock_channel = {"id": "123", "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel
        mock_discord_client.get_channel_message.side_effect = DiscordAPIError(
            "Not Found", 404
        )

        result = await discord_service.delete_message("123", "msg123")
        assert "❌ Error: Message `msg123` not found in channel #general." in result

    @pytest.mark.asyncio
    async def test_edit_message_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful message editing."""
        # Setup
        channel_id = "123456789012345678"
        message_id = "msg123"
        new_content = "Updated content"
        mock_settings.is_channel_allowed.return_value = True

        mock_channel = {"id": channel_id, "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_bot_user = {"id": "bot123"}
        mock_discord_client.get_current_user.return_value = mock_bot_user

        mock_message = {
            "id": message_id,
            "author": {"id": "bot123"},
            "content": "Original content",
        }
        mock_discord_client.get_channel_message.return_value = mock_message

        mock_discord_client.patch.return_value = {"id": message_id}

        # Execute
        result = await discord_service.edit_message(channel_id, message_id, new_content)

        # Verify
        assert "✅ Message edited successfully in #general!" in result
        assert "Message ID**: `msg123`" in result
        assert "Old Content**: Original content" in result
        assert "New Content**: Updated content" in result

        mock_discord_client.patch.assert_called_once_with(
            f"/channels/{channel_id}/messages/{message_id}",
            data={"content": new_content},
        )

    @pytest.mark.asyncio
    async def test_edit_message_not_own_message(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test editing message not owned by bot."""
        mock_settings.is_channel_allowed.return_value = True
        mock_channel = {"id": "123", "name": "general"}
        mock_discord_client.get_channel.return_value = mock_channel

        mock_bot_user = {"id": "bot123"}
        mock_discord_client.get_current_user.return_value = mock_bot_user

        mock_message = {"author": {"id": "other_user"}, "content": "test"}
        mock_discord_client.get_channel_message.return_value = mock_message

        result = await discord_service.edit_message("123", "msg123", "new content")
        assert "❌ Error: Can only edit bot's own messages" in result

    # Tests for ban_user method
    @pytest.mark.asyncio
    async def test_ban_user_success(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test successful user ban."""
        # Mock settings to allow guild
        mock_settings.get_allowed_guilds_set.return_value = {"guild123"}
        mock_settings.is_guild_allowed.return_value = True

        # Mock guild info (called multiple times for hierarchy validation)
        mock_guild = {
            "id": "guild123", 
            "name": "Test Guild",
            "roles": [
                {"id": "role1", "name": "Member", "position": 1},
                {"id": "role2", "name": "Moderator", "position": 2},
            ]
        }
        mock_discord_client.get_guild.return_value = mock_guild

        # Mock user info
        mock_user = {"id": "user123", "username": "testuser", "global_name": "Test User"}
        mock_discord_client.get_user.return_value = mock_user

        # Mock current bot user for hierarchy validation
        mock_discord_client.get_current_user.return_value = {
            "id": "bot123",
            "username": "TestBot"
        }

        # Mock guild member calls - ban_user calls get_guild_member multiple times:
        # 1. First to check if user is in guild (for hierarchy validation check)
        # 2. Then in hierarchy validation for bot member
        # 3. Then in hierarchy validation for target member
        mock_discord_client.get_guild_member.side_effect = [
            # First call - check if user is in guild
            {
                "user": {"id": "user123"},
                "roles": ["role1"]  # Target has member role
            },
            # Bot member (second call in hierarchy validation)
            {
                "user": {"id": "bot123"},
                "roles": ["role2"]  # Bot has moderator role
            },
            # Target member (third call in hierarchy validation)
            {
                "user": {"id": "user123"},
                "roles": ["role1"]  # Target has member role (lower)
            }
        ]

        # Mock ban check (404 means not banned)
        mock_discord_client.get.side_effect = DiscordAPIError("Not found", 404)

        # Mock successful ban
        mock_discord_client.ban_guild_member.return_value = None

        result = await discord_service.ban_user(
            "guild123", "user123", "Test reason", 1
        )

        # Verify the result
        assert "✅ User banned successfully!" in result
        assert "Test User" in result
        assert "Test Guild" in result
        assert "Test reason" in result
        assert "1 day(s) of messages deleted" in result

        # Verify the ban was called correctly
        mock_discord_client.ban_guild_member.assert_called_once_with(
            guild_id="guild123",
            user_id="user123", 
            reason="Test reason",
            delete_message_days=1
        )

    @pytest.mark.asyncio
    async def test_ban_user_invalid_delete_days(self, discord_service):
        """Test ban with invalid delete_message_days parameter."""
        result = await discord_service.ban_user(
            "guild123", "user123", "Test reason", 8
        )
        assert "❌ Error: delete_message_days must be between 0 and 7" in result

        result = await discord_service.ban_user(
            "guild123", "user123", "Test reason", -1
        )
        assert "❌ Error: delete_message_days must be between 0 and 7" in result

    @pytest.mark.asyncio
    async def test_ban_user_already_banned(
        self, discord_service, mock_discord_client, mock_settings
    ):
        """Test banning a user who is already banned."""
        # Mock settings to allow guild
        mock_settings.get_allowed_guilds_set.return_value = {"guild123"}
        mock_settings.is_guild_allowed.return_value = True

        # Mock guild info
        mock_guild = {"id": "guild123", "name": "Test Guild"}
        mock_discord_client.get_guild.return_value = mock_guild

        # Mock user info
        mock_user = {"id": "user123", "username": "testuser", "global_name": "Test User"}
        mock_discord_client.get_user.return_value = mock_user

        # Mock ban check (user is already banned)
        mock_discord_client.get.return_value = {"user": {"id": "user123"}}

        result = await discord_service.ban_user("guild123", "user123", "Test reason")

        assert "❌ Error: User `Test User` (`user123`) is already banned from Test Guild" in result


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

    # Tests for centralized resource retrieval methods

    @pytest.mark.asyncio
    async def test_get_guild_with_error_handling_success(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test successful guild retrieval with centralized error handling."""
        # Setup
        guild_id = "123456789012345678"
        expected_guild = {"id": guild_id, "name": "Test Guild"}
        mock_discord_client.get_guild.return_value = expected_guild

        # Execute
        guild_data, error_message = await discord_service._get_guild_with_error_handling(guild_id)

        # Verify
        assert guild_data == expected_guild
        assert error_message is None
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_guild_with_error_handling_not_found(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test guild retrieval when guild is not found."""
        # Setup
        guild_id = "999999999999999999"
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        guild_data, error_message = await discord_service._get_guild_with_error_handling(guild_id)

        # Verify
        assert guild_data is None
        assert error_message == f"Guild with ID `{guild_id}` was not found or bot has no access."
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_guild_with_error_handling_forbidden(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test guild retrieval when access is forbidden."""
        # Setup
        guild_id = "123456789012345678"
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Forbidden", 403)

        # Execute
        guild_data, error_message = await discord_service._get_guild_with_error_handling(guild_id)

        # Verify
        assert guild_data is None
        assert error_message == f"Bot does not have permission to access guild `{guild_id}`."
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_guild_with_error_handling_other_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test guild retrieval with other Discord API errors."""
        # Setup
        guild_id = "123456789012345678"
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Server Error", 500)

        # Execute
        guild_data, error_message = await discord_service._get_guild_with_error_handling(guild_id)

        # Verify
        assert guild_data is None
        assert error_message == "Failed to access guild: Server Error"
        mock_discord_client.get_guild.assert_called_once_with(guild_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_with_error_handling_success(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test successful user retrieval with centralized error handling."""
        # Setup
        user_id = "123456789012345678"
        expected_user = {"id": user_id, "username": "testuser"}
        mock_discord_client.get_user.return_value = expected_user

        # Execute
        user_data, error_message = await discord_service._get_user_with_error_handling(user_id)

        # Verify
        assert user_data == expected_user
        assert error_message is None
        mock_discord_client.get_user.assert_called_once_with(user_id)
        mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_with_error_handling_not_found(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test user retrieval when user is not found."""
        # Setup
        user_id = "999999999999999999"
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        user_data, error_message = await discord_service._get_user_with_error_handling(user_id)

        # Verify
        assert user_data is None
        assert error_message == f"User with ID `{user_id}` was not found."
        mock_discord_client.get_user.assert_called_once_with(user_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_with_error_handling_other_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test user retrieval with other Discord API errors."""
        # Setup
        user_id = "123456789012345678"
        mock_discord_client.get_user.side_effect = DiscordAPIError("Server Error", 500)

        # Execute
        user_data, error_message = await discord_service._get_user_with_error_handling(user_id)

        # Verify
        assert user_data is None
        assert error_message == "Failed to get user information: Server Error"
        mock_discord_client.get_user.assert_called_once_with(user_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_with_error_handling_success(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test successful channel retrieval with centralized error handling."""
        # Setup
        channel_id = "123456789012345678"
        expected_channel = {"id": channel_id, "name": "general", "type": 0}
        mock_discord_client.get_channel.return_value = expected_channel

        # Execute
        channel_data, error_message = await discord_service._get_channel_with_error_handling(channel_id)

        # Verify
        assert channel_data == expected_channel
        assert error_message is None
        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_channel_with_error_handling_not_found(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test channel retrieval when channel is not found."""
        # Setup
        channel_id = "999999999999999999"
        mock_discord_client.get_channel.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        channel_data, error_message = await discord_service._get_channel_with_error_handling(channel_id)

        # Verify
        assert channel_data is None
        assert error_message == f"Channel with ID `{channel_id}` was not found or bot has no access."
        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_with_error_handling_forbidden(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test channel retrieval when access is forbidden."""
        # Setup
        channel_id = "123456789012345678"
        mock_discord_client.get_channel.side_effect = DiscordAPIError("Forbidden", 403)

        # Execute
        channel_data, error_message = await discord_service._get_channel_with_error_handling(channel_id)

        # Verify
        assert channel_data is None
        assert error_message == f"Bot does not have permission to access channel `{channel_id}`."
        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_with_error_handling_other_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test channel retrieval with other Discord API errors."""
        # Setup
        channel_id = "123456789012345678"
        mock_discord_client.get_channel.side_effect = DiscordAPIError("Server Error", 500)

        # Execute
        channel_data, error_message = await discord_service._get_channel_with_error_handling(channel_id)

        # Verify
        assert channel_data is None
        assert error_message == "Failed to access channel: Server Error"
        mock_discord_client.get_channel.assert_called_once_with(channel_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_member_with_error_handling_success(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test successful member retrieval with centralized error handling."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        expected_member = {
            "user": {"id": user_id, "username": "testuser"},
            "roles": ["role1", "role2"],
            "joined_at": "2023-01-01T00:00:00Z"
        }
        mock_discord_client.get_guild_member.return_value = expected_member

        # Execute
        member_data, error_message = await discord_service._get_member_with_error_handling(guild_id, user_id)

        # Verify
        assert member_data == expected_member
        assert error_message is None
        mock_discord_client.get_guild_member.assert_called_once_with(guild_id, user_id)
        mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_member_with_error_handling_not_found(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test member retrieval when member is not found."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "999999999999999999"
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Not Found", 404)

        # Execute
        member_data, error_message = await discord_service._get_member_with_error_handling(guild_id, user_id)

        # Verify
        assert member_data is None
        assert error_message == f"User `{user_id}` is not a member of guild `{guild_id}`."
        mock_discord_client.get_guild_member.assert_called_once_with(guild_id, user_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_member_with_error_handling_forbidden(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test member retrieval when access is forbidden."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Forbidden", 403)

        # Execute
        member_data, error_message = await discord_service._get_member_with_error_handling(guild_id, user_id)

        # Verify
        assert member_data is None
        assert error_message == f"Bot does not have permission to access member information in guild `{guild_id}`."
        mock_discord_client.get_guild_member.assert_called_once_with(guild_id, user_id)
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_member_with_error_handling_other_error(
        self, discord_service, mock_discord_client, mock_logger
    ):
        """Test member retrieval with other Discord API errors."""
        # Setup
        guild_id = "123456789012345678"
        user_id = "987654321098765432"
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError("Server Error", 500)

        # Execute
        member_data, error_message = await discord_service._get_member_with_error_handling(guild_id, user_id)

        # Verify
        assert member_data is None
        assert error_message == "Failed to get member information: Server Error"
        mock_discord_client.get_guild_member.assert_called_once_with(guild_id, user_id)
        mock_logger.warning.assert_called_once()


class TestDiscordServiceFormattingUtilities:
    """Test formatting utility methods for DiscordService."""

    @pytest.fixture
    def discord_service(self, mock_discord_client, mock_settings, mock_logger):
        """Create a DiscordService instance for testing."""
        return DiscordService(mock_discord_client, mock_settings, mock_logger)

    # Tests for _format_success_response method

    def test_format_success_response_basic(self, discord_service):
        """Test basic success response formatting."""
        action = "Message sent"
        details = {
            "message_id": "123456789012345678",
            "channel": "#general",
            "content": "Hello world!"
        }

        result = discord_service._format_success_response(action, details)

        assert result.startswith("✅ Message sent successfully!")
        assert "- **Message Id**: `123456789012345678`" in result
        assert "- **Channel**: #general" in result
        assert "- **Content**: Hello world!" in result

    def test_format_success_response_with_long_content(self, discord_service):
        """Test success response formatting with content truncation."""
        action = "Message sent"
        long_content = "A" * 150  # Content longer than 100 characters
        details = {
            "message_id": "123456789012345678",
            "content": long_content
        }

        result = discord_service._format_success_response(action, details)

        assert result.startswith("✅ Message sent successfully!")
        assert "- **Message Id**: `123456789012345678`" in result
        assert "- **Content**: " + "A" * 97 + "..." in result
        assert len(result.split("- **Content**: ")[1].split("\n")[0]) == 100

    def test_format_success_response_with_none_values(self, discord_service):
        """Test success response formatting with None values."""
        action = "User kicked"
        details = {
            "user_id": "123456789012345678",
            "reason": None,  # None value should be skipped
            "guild": "Test Guild"
        }

        result = discord_service._format_success_response(action, details)

        assert result.startswith("✅ User kicked successfully!")
        assert "- **User Id**: `123456789012345678`" in result
        assert "- **Guild**: Test Guild" in result
        assert "reason" not in result.lower()  # None values should be excluded

    def test_format_success_response_empty_details(self, discord_service):
        """Test success response formatting with empty details."""
        action = "Operation completed"
        details = {}

        result = discord_service._format_success_response(action, details)

        assert result == "✅ Operation completed successfully!"

    def test_format_success_response_id_formatting(self, discord_service):
        """Test that ID fields are properly formatted with backticks."""
        action = "User banned"
        details = {
            "user_id": "123456789012345678",
            "guild_id": "987654321098765432",
            "id": "555555555555555555",
            "regular_field": "not an id"
        }

        result = discord_service._format_success_response(action, details)

        assert "- **User Id**: `123456789012345678`" in result
        assert "- **Guild Id**: `987654321098765432`" in result
        assert "- **Id**: `555555555555555555`" in result
        assert "- **Regular Field**: not an id" in result  # No backticks for non-ID

    # Tests for _format_user_display_name method

    def test_format_user_display_name_new_system_username_only(self, discord_service):
        """Test user display name formatting for new Discord username system."""
        user = {
            "username": "testuser",
            "discriminator": "0",
            "global_name": None
        }

        result = discord_service._format_user_display_name(user)

        assert result == "@testuser"

    def test_format_user_display_name_new_system_with_global_name(self, discord_service):
        """Test user display name formatting with global name in new system."""
        user = {
            "username": "testuser",
            "discriminator": "0",
            "global_name": "Test User"
        }

        result = discord_service._format_user_display_name(user)

        assert result == "Test User (@testuser)"

    def test_format_user_display_name_new_system_same_names(self, discord_service):
        """Test user display name formatting when global name equals username."""
        user = {
            "username": "testuser",
            "discriminator": "0",
            "global_name": "testuser"
        }

        result = discord_service._format_user_display_name(user)

        assert result == "@testuser"

    def test_format_user_display_name_legacy_system_username_only(self, discord_service):
        """Test user display name formatting for legacy Discord username system."""
        user = {
            "username": "testuser",
            "discriminator": "1234",
            "global_name": None
        }

        result = discord_service._format_user_display_name(user)

        assert result == "testuser#1234"

    def test_format_user_display_name_legacy_system_with_global_name(self, discord_service):
        """Test user display name formatting with global name in legacy system."""
        user = {
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User"
        }

        result = discord_service._format_user_display_name(user)

        assert result == "Test User (testuser#1234)"

    def test_format_user_display_name_legacy_system_same_names(self, discord_service):
        """Test user display name formatting when global name equals username in legacy system."""
        user = {
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "testuser"
        }

        result = discord_service._format_user_display_name(user)

        assert result == "testuser#1234"

    def test_format_user_display_name_missing_fields(self, discord_service):
        """Test user display name formatting with missing fields."""
        user = {}

        result = discord_service._format_user_display_name(user)

        assert result == "@Unknown User"

    def test_format_user_display_name_discriminator_0000(self, discord_service):
        """Test user display name formatting with discriminator 0000 (treated as new system)."""
        user = {
            "username": "testuser",
            "discriminator": "0000",
            "global_name": "Test User"
        }

        result = discord_service._format_user_display_name(user)

        assert result == "Test User (@testuser)"

    # Tests for _format_timestamp method

    def test_format_timestamp_valid_iso_format(self, discord_service):
        """Test timestamp formatting with valid ISO format."""
        timestamp = "2023-12-25T15:30:45Z"

        result = discord_service._format_timestamp(timestamp)

        assert result == "2023-12-25 15:30:45 UTC"

    def test_format_timestamp_valid_iso_format_with_timezone(self, discord_service):
        """Test timestamp formatting with ISO format including timezone."""
        timestamp = "2023-12-25T15:30:45+00:00"

        result = discord_service._format_timestamp(timestamp)

        assert result == "2023-12-25 15:30:45 UTC"

    def test_format_timestamp_empty_string(self, discord_service):
        """Test timestamp formatting with empty string."""
        timestamp = ""

        result = discord_service._format_timestamp(timestamp)

        assert result == "Unknown time"

    def test_format_timestamp_none_value(self, discord_service):
        """Test timestamp formatting with None value."""
        timestamp = None

        result = discord_service._format_timestamp(timestamp)

        assert result == "Unknown time"

    def test_format_timestamp_invalid_format(self, discord_service, mock_logger):
        """Test timestamp formatting with invalid format."""
        timestamp = "invalid-timestamp"

        result = discord_service._format_timestamp(timestamp)

        # Should return original timestamp if parsing fails
        assert result == "invalid-timestamp"
        # Should log a warning
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "Failed to parse timestamp" in call_args[0][0]

    def test_format_timestamp_partial_iso_format(self, discord_service):
        """Test timestamp formatting with partial ISO format."""
        timestamp = "2023-12-25T15:30:45"

        result = discord_service._format_timestamp(timestamp)

        assert result == "2023-12-25 15:30:45 UTC"

    # Tests for _truncate_content method

    def test_truncate_content_short_content(self, discord_service):
        """Test content truncation with content shorter than limit."""
        content = "Hello world!"
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == "Hello world!"

    def test_truncate_content_exact_length(self, discord_service):
        """Test content truncation with content exactly at limit."""
        content = "A" * 100
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == "A" * 100

    def test_truncate_content_long_content(self, discord_service):
        """Test content truncation with content longer than limit."""
        content = "A" * 150
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == "A" * 97 + "..."
        assert len(result) == 100

    def test_truncate_content_default_length(self, discord_service):
        """Test content truncation with default max length."""
        content = "A" * 150

        result = discord_service._truncate_content(content)

        assert result == "A" * 97 + "..."
        assert len(result) == 100

    def test_truncate_content_empty_string(self, discord_service):
        """Test content truncation with empty string."""
        content = ""
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == ""

    def test_truncate_content_none_value(self, discord_service):
        """Test content truncation with None value."""
        content = None
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == ""

    def test_truncate_content_whitespace_only(self, discord_service):
        """Test content truncation with whitespace-only content."""
        content = "   \n\t   "
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == ""  # Should be stripped to empty string

    def test_truncate_content_with_whitespace(self, discord_service):
        """Test content truncation with leading/trailing whitespace."""
        content = "  Hello world!  "
        max_length = 100

        result = discord_service._truncate_content(content, max_length)

        assert result == "Hello world!"

    def test_truncate_content_small_limit(self, discord_service):
        """Test content truncation with very small limit."""
        content = "Hello world!"
        max_length = 5

        result = discord_service._truncate_content(content, max_length)

        assert result == "He..."
        assert len(result) == 5

    def test_truncate_content_limit_too_small_for_ellipsis(self, discord_service):
        """Test content truncation with limit smaller than ellipsis."""
        content = "Hello world!"
        max_length = 2

        result = discord_service._truncate_content(content, max_length)

        # Should still add ellipsis even if it makes result longer than max_length
        assert result == "..."
        assert len(result) == 3

    def test_truncate_content_non_string_input(self, discord_service):
        """Test content truncation with non-string input."""
        content = 12345
        max_length = 3

        result = discord_service._truncate_content(content, max_length)

        assert result == "..."  # "12345" -> "..." (length 3)
