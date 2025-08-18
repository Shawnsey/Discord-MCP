"""
Unit tests for centralized error handling methods in DiscordService.
"""

import pytest
from unittest.mock import Mock, AsyncMock
import structlog

from src.discord_mcp.services.discord_service import DiscordService
from src.discord_mcp.discord_client import DiscordAPIError
from src.discord_mcp.config import Settings


@pytest.fixture
def mock_discord_client():
    """Create a mock Discord client."""
    client = Mock()
    client.get_user_guilds = AsyncMock()
    client.get_guild = AsyncMock()
    client.get_channel = AsyncMock()
    client.get_user = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.get_allowed_guilds_set.return_value = set()
    settings.get_allowed_channels_set.return_value = set()
    settings.is_guild_allowed.return_value = True
    settings.is_channel_allowed.return_value = True
    return settings


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock(spec=structlog.stdlib.BoundLogger)


@pytest.fixture
def discord_service(mock_discord_client, mock_settings, mock_logger):
    """Create a DiscordService instance with mocked dependencies."""
    return DiscordService(mock_discord_client, mock_settings, mock_logger)


class TestCentralizedErrorHandling:
    """Test cases for centralized error handling methods."""

    def test_create_permission_denied_response_basic(self, discord_service, mock_logger):
        """Test basic permission denied response creation."""
        result = discord_service._create_permission_denied_response("guild", "123456789")
        
        expected = "# Access Denied\n\nAccess to guild `123456789` is not permitted."
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Permission denied",
            resource_type="guild",
            resource_id="123456789",
            context=None,
        )

    def test_create_permission_denied_response_with_context(self, discord_service, mock_logger):
        """Test permission denied response with additional context."""
        context = "Bot is not a member of this guild."
        result = discord_service._create_permission_denied_response("guild", "123456789", context)
        
        expected = f"# Access Denied\n\nAccess to guild `123456789` is not permitted. {context}"
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Permission denied",
            resource_type="guild",
            resource_id="123456789",
            context=context,
        )

    def test_create_not_found_response_basic(self, discord_service, mock_logger):
        """Test basic not found response creation."""
        result = discord_service._create_not_found_response("Guild", "123456789")
        
        expected = "# Guild Not Found\n\nGuild with ID `123456789` was not found or bot has no access."
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Resource not found",
            resource_type="Guild",
            resource_id="123456789",
            context=None,
        )

    def test_create_not_found_response_with_context(self, discord_service, mock_logger):
        """Test not found response with additional context."""
        context = "The guild may have been deleted."
        result = discord_service._create_not_found_response("Guild", "123456789", context)
        
        expected = f"# Guild Not Found\n\nGuild with ID `123456789` was not found. {context}"
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Resource not found",
            resource_type="Guild",
            resource_id="123456789",
            context=context,
        )

    def test_create_validation_error_response_basic(self, discord_service, mock_logger):
        """Test basic validation error response creation."""
        result = discord_service._create_validation_error_response(
            "Message content", "Content cannot be empty."
        )
        
        expected = "❌ Error: Message content validation failed. Content cannot be empty."
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Validation error",
            validation_type="Message content",
            details="Content cannot be empty.",
            suggestions=None,
        )

    def test_create_validation_error_response_with_suggestions(self, discord_service, mock_logger):
        """Test validation error response with suggestions."""
        suggestions = "- Ensure message content is not empty\n- Check for whitespace-only content"
        result = discord_service._create_validation_error_response(
            "Message content", "Content cannot be empty.", suggestions
        )
        
        expected = (
            "❌ Error: Message content validation failed. Content cannot be empty.\n\n"
            f"**Suggestions:**\n{suggestions}"
        )
        assert result == expected
        
        # Verify logging
        mock_logger.warning.assert_called_once_with(
            "Validation error",
            validation_type="Message content",
            details="Content cannot be empty.",
            suggestions=suggestions,
        )

    def test_handle_discord_error_403(self, discord_service, mock_logger):
        """Test Discord API error handling for 403 Forbidden."""
        error = DiscordAPIError("Forbidden", status_code=403)
        result = discord_service._handle_discord_error(error, "sending message")
        
        expected = "❌ Error: Bot does not have permission to perform this operation while sending message."
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in sending message",
            error="Forbidden",
            status_code=403,
            operation="sending message",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_discord_error_404(self, discord_service, mock_logger):
        """Test Discord API error handling for 404 Not Found."""
        error = DiscordAPIError("Not Found", status_code=404)
        result = discord_service._handle_discord_error(error, "fetching user")
        
        expected = "❌ Error: Resource not found while fetching user."
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in fetching user",
            error="Not Found",
            status_code=404,
            operation="fetching user",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_discord_error_429(self, discord_service, mock_logger):
        """Test Discord API error handling for 429 Rate Limited."""
        error = DiscordAPIError("Too Many Requests", status_code=429)
        result = discord_service._handle_discord_error(error, "fetching messages")
        
        expected = "❌ Error: Rate limit exceeded while fetching messages. Please try again later."
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in fetching messages",
            error="Too Many Requests",
            status_code=429,
            operation="fetching messages",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_discord_error_400(self, discord_service, mock_logger):
        """Test Discord API error handling for 400 Bad Request."""
        error = DiscordAPIError("Bad Request", status_code=400)
        result = discord_service._handle_discord_error(error, "creating channel")
        
        expected = "❌ Error: Invalid request while creating channel. Please check your parameters."
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in creating channel",
            error="Bad Request",
            status_code=400,
            operation="creating channel",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_discord_error_unknown_status(self, discord_service, mock_logger):
        """Test Discord API error handling for unknown status codes."""
        error = DiscordAPIError("Internal Server Error", status_code=500)
        result = discord_service._handle_discord_error(error, "updating guild")
        
        expected = "❌ Error: Discord API error while updating guild: Internal Server Error"
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in updating guild",
            error="Internal Server Error",
            status_code=500,
            operation="updating guild",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_discord_error_no_status_code(self, discord_service, mock_logger):
        """Test Discord API error handling when no status code is available."""
        error = DiscordAPIError("Connection Error")
        result = discord_service._handle_discord_error(error, "connecting to API")
        
        expected = "❌ Error: Discord API error while connecting to API: Connection Error"
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Discord API error in connecting to API",
            error="Connection Error",
            status_code=None,
            operation="connecting to API",
            resource_type=None,
            resource_id=None,
        )

    def test_handle_unexpected_error(self, discord_service, mock_logger):
        """Test unexpected error handling."""
        error = ValueError("Invalid input parameter")
        result = discord_service._handle_unexpected_error(error, "processing request")
        
        expected = (
            "❌ Unexpected error while processing request: Invalid input parameter\n\n"
            "Please try again or contact support if the issue persists."
        )
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Unexpected error in processing request",
            error="Invalid input parameter",
            error_type="ValueError",
            operation="processing request",
            context=None,
        )

    def test_handle_unexpected_error_different_exception_types(self, discord_service, mock_logger):
        """Test unexpected error handling with different exception types."""
        # Test with KeyError
        error = KeyError("missing_key")
        result = discord_service._handle_unexpected_error(error, "accessing data")
        
        expected = (
            "❌ Unexpected error while accessing data: 'missing_key'\n\n"
            "Please try again or contact support if the issue persists."
        )
        assert result == expected
        
        # Verify logging
        mock_logger.error.assert_called_once_with(
            "Unexpected error in accessing data",
            error="'missing_key'",
            error_type="KeyError",
            operation="accessing data",
            context=None,
        )


class TestErrorHandlingIntegration:
    """Integration tests for error handling methods."""

    def test_permission_denied_different_resource_types(self, discord_service):
        """Test permission denied responses for different resource types."""
        # Test guild permission denied
        guild_result = discord_service._create_permission_denied_response("guild", "123")
        assert "guild `123`" in guild_result
        
        # Test channel permission denied
        channel_result = discord_service._create_permission_denied_response("channel", "456")
        assert "channel `456`" in channel_result
        
        # Test user permission denied
        user_result = discord_service._create_permission_denied_response("user", "789")
        assert "user `789`" in user_result

    def test_not_found_different_resource_types(self, discord_service):
        """Test not found responses for different resource types."""
        # Test Guild not found
        guild_result = discord_service._create_not_found_response("Guild", "123")
        assert "# Guild Not Found" in guild_result
        assert "Guild with ID `123`" in guild_result
        
        # Test Channel not found
        channel_result = discord_service._create_not_found_response("Channel", "456")
        assert "# Channel Not Found" in channel_result
        assert "Channel with ID `456`" in channel_result
        
        # Test User not found
        user_result = discord_service._create_not_found_response("User", "789")
        assert "# User Not Found" in user_result
        assert "User with ID `789`" in user_result

    def test_validation_error_different_types(self, discord_service):
        """Test validation error responses for different validation types."""
        # Test message content validation
        content_result = discord_service._create_validation_error_response(
            "Message content", "Too long (2500 characters). Maximum is 2000."
        )
        assert "Message content validation failed" in content_result
        assert "Too long" in content_result
        
        # Test user input validation
        input_result = discord_service._create_validation_error_response(
            "User input", "Invalid user ID format."
        )
        assert "User input validation failed" in input_result
        assert "Invalid user ID format" in input_result