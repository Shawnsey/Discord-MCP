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
    async def test_get_guilds_formatted_not_implemented(self, discord_service):
        """Test that get_guilds_formatted raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.get_guilds_formatted()

    @pytest.mark.asyncio
    async def test_get_channels_formatted_not_implemented(self, discord_service):
        """Test that get_channels_formatted raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.get_channels_formatted("123456789012345678")

    @pytest.mark.asyncio
    async def test_get_messages_formatted_not_implemented(self, discord_service):
        """Test that get_messages_formatted raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.get_messages_formatted("111111111111111111")

    @pytest.mark.asyncio
    async def test_get_user_info_formatted_not_implemented(self, discord_service):
        """Test that get_user_info_formatted raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Method implementation pending"):
            await discord_service.get_user_info_formatted("123456789012345678")

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
