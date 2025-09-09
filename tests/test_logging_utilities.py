"""
Tests for centralized logging utilities in Discord service.
"""

import pytest
from unittest.mock import Mock, MagicMock
import structlog

from src.discord_mcp.services.discord_service import DiscordService
from src.discord_mcp.config import Settings
from src.discord_mcp.discord_client import DiscordClient


class TestLoggingUtilities:
    """Test centralized logging utilities."""

    @pytest.fixture
    def mock_discord_client(self):
        """Create a mock Discord client."""
        return Mock(spec=DiscordClient)

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock(spec=Settings)
        settings.get_allowed_guilds_set.return_value = set()
        settings.get_allowed_channels_set.return_value = set()
        return settings

    @pytest.fixture
    def mock_logger(self):
        """Create a mock structured logger."""
        return Mock(spec=structlog.stdlib.BoundLogger)

    @pytest.fixture
    def discord_service(self, mock_discord_client, mock_settings, mock_logger):
        """Create a Discord service instance with mocked dependencies."""
        return DiscordService(mock_discord_client, mock_settings, mock_logger)

    def test_log_operation_start(self, discord_service, mock_logger):
        """Test _log_operation_start method."""
        # Test basic operation start logging
        discord_service._log_operation_start("test operation")

        mock_logger.info.assert_called_once_with(
            "Starting test operation", operation="test operation"
        )

    def test_log_operation_start_with_context(self, discord_service, mock_logger):
        """Test _log_operation_start method with additional context."""
        # Test operation start logging with additional context
        discord_service._log_operation_start(
            "message sending",
            channel_id="123456789",
            content_length=50,
            reply_to="987654321",
        )

        mock_logger.info.assert_called_once_with(
            "Starting message sending",
            operation="message sending",
            channel_id="123456789",
            content_length=50,
            reply_to="987654321",
        )

    def test_log_operation_success(self, discord_service, mock_logger):
        """Test _log_operation_success method."""
        # Test basic operation success logging
        discord_service._log_operation_success("test operation")

        mock_logger.info.assert_called_once_with(
            "test operation completed successfully",
            operation="test operation",
            success=True,
        )

    def test_log_operation_success_with_context(self, discord_service, mock_logger):
        """Test _log_operation_success method with additional context."""
        # Test operation success logging with additional context
        discord_service._log_operation_success(
            "guild list retrieval", guild_count=5, filtered=True
        )

        mock_logger.info.assert_called_once_with(
            "guild list retrieval completed successfully",
            operation="guild list retrieval",
            success=True,
            guild_count=5,
            filtered=True,
        )

    def test_log_operation_error(self, discord_service, mock_logger):
        """Test _log_operation_error method."""
        # Create a test exception
        test_error = ValueError("Test error message")

        # Test basic operation error logging
        discord_service._log_operation_error("test operation", test_error)

        mock_logger.error.assert_called_once_with(
            "Error in test operation",
            operation="test operation",
            error="Test error message",
            error_type="ValueError",
            success=False,
        )

    def test_log_operation_error_with_context(self, discord_service, mock_logger):
        """Test _log_operation_error method with additional context."""
        # Create a test exception
        test_error = RuntimeError("Connection failed")

        # Test operation error logging with additional context
        discord_service._log_operation_error(
            "message sending", test_error, channel_id="123456789", user_id="987654321"
        )

        mock_logger.error.assert_called_once_with(
            "Error in message sending",
            operation="message sending",
            error="Connection failed",
            error_type="RuntimeError",
            success=False,
            channel_id="123456789",
            user_id="987654321",
        )

    def test_log_operation_error_with_different_exception_types(
        self, discord_service, mock_logger
    ):
        """Test _log_operation_error method with different exception types."""
        # Test with different exception types
        exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
            RuntimeError("Runtime error"),
        ]

        for i, exception in enumerate(exceptions):
            mock_logger.reset_mock()

            discord_service._log_operation_error(f"operation_{i}", exception)

            mock_logger.error.assert_called_once_with(
                f"Error in operation_{i}",
                operation=f"operation_{i}",
                error=str(exception),
                error_type=type(exception).__name__,
                success=False,
            )

    def test_logging_utilities_integration(self, discord_service, mock_logger):
        """Test that logging utilities work together in a typical flow."""
        # Simulate a typical operation flow
        operation_name = "user info retrieval"
        user_id = "123456789"

        # Start operation
        discord_service._log_operation_start(operation_name, user_id=user_id)

        # Success case
        discord_service._log_operation_success(
            operation_name, user_id=user_id, username="testuser"
        )

        # Verify calls
        assert mock_logger.info.call_count == 2

        # Check start call
        start_call = mock_logger.info.call_args_list[0]
        assert start_call[0][0] == f"Starting {operation_name}"
        assert start_call[1]["operation"] == operation_name
        assert start_call[1]["user_id"] == user_id

        # Check success call
        success_call = mock_logger.info.call_args_list[1]
        assert success_call[0][0] == f"{operation_name} completed successfully"
        assert success_call[1]["operation"] == operation_name
        assert success_call[1]["success"] is True
        assert success_call[1]["user_id"] == user_id
        assert success_call[1]["username"] == "testuser"

    def test_logging_utilities_error_flow(self, discord_service, mock_logger):
        """Test logging utilities in an error flow."""
        # Simulate an error operation flow
        operation_name = "message sending"
        channel_id = "123456789"
        error = ConnectionError("Network timeout")

        # Start operation
        discord_service._log_operation_start(operation_name, channel_id=channel_id)

        # Error case
        discord_service._log_operation_error(
            operation_name, error, channel_id=channel_id
        )

        # Verify calls
        assert mock_logger.info.call_count == 1
        assert mock_logger.error.call_count == 1

        # Check start call
        start_call = mock_logger.info.call_args_list[0]
        assert start_call[0][0] == f"Starting {operation_name}"
        assert start_call[1]["operation"] == operation_name
        assert start_call[1]["channel_id"] == channel_id

        # Check error call
        error_call = mock_logger.error.call_args_list[0]
        assert error_call[0][0] == f"Error in {operation_name}"
        assert error_call[1]["operation"] == operation_name
        assert error_call[1]["error"] == "Network timeout"
        assert error_call[1]["error_type"] == "ConnectionError"
        assert error_call[1]["success"] is False
        assert error_call[1]["channel_id"] == channel_id

    def test_logging_with_empty_context(self, discord_service, mock_logger):
        """Test logging utilities with empty context."""
        # Test with no additional context
        discord_service._log_operation_start("simple operation")
        discord_service._log_operation_success("simple operation")
        discord_service._log_operation_error("simple operation", ValueError("error"))

        # Verify all calls were made
        assert mock_logger.info.call_count == 2
        assert mock_logger.error.call_count == 1

        # Check that basic structure is maintained
        for call in mock_logger.info.call_args_list:
            assert "operation" in call[1]

        error_call = mock_logger.error.call_args_list[0]
        assert "operation" in error_call[1]
        assert "error" in error_call[1]
        assert "error_type" in error_call[1]
        assert "success" in error_call[1]

    def test_logging_with_none_values(self, discord_service, mock_logger):
        """Test logging utilities with None values in context."""
        # Test with None values in context
        discord_service._log_operation_start(
            "test operation", user_id=None, channel_id="123456789", guild_id=None
        )

        # Verify call includes None values
        call_args = mock_logger.info.call_args_list[0]
        assert call_args[1]["user_id"] is None
        assert call_args[1]["channel_id"] == "123456789"
        assert call_args[1]["guild_id"] is None

    def test_logging_with_complex_context_data(self, discord_service, mock_logger):
        """Test logging utilities with complex context data."""
        # Test with various data types
        complex_context = {
            "string_value": "test",
            "int_value": 42,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "dict_value": {"key": "value"},
            "none_value": None,
        }

        discord_service._log_operation_success("complex operation", **complex_context)

        # Verify all context data is passed through
        call_args = mock_logger.info.call_args_list[0]
        for key, value in complex_context.items():
            assert call_args[1][key] == value
