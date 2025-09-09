"""
Integration tests for validation layer with DiscordService.

This module tests that the DiscordService can properly use
the validation layer components.
"""

import sys
import os
from unittest.mock import Mock, AsyncMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from discord_mcp.services.discord_service import DiscordService
from discord_mcp.services.validation import ValidationResult, ValidationErrorType
from discord_mcp.discord_client import DiscordClient
from discord_mcp.config import Settings
import structlog


def test_discord_service_validation_integration():
    """Test that DiscordService can use validation methods."""
    # Create mock dependencies
    mock_client = AsyncMock(spec=DiscordClient)
    mock_settings = Mock(spec=Settings)
    mock_logger = Mock(spec=structlog.stdlib.BoundLogger)

    # Create DiscordService instance
    service = DiscordService(mock_client, mock_settings, mock_logger)

    # Test that service has validation methods from ValidationMixin
    assert hasattr(service, "_validate_string_content")
    assert hasattr(service, "_validate_numeric_range")
    assert hasattr(service, "_validate_discord_id")
    assert hasattr(service, "_validate_message_content")
    assert hasattr(service, "_validate_timeout_duration")
    assert hasattr(service, "_validate_message_limit")
    assert hasattr(service, "_validate_ban_delete_days")
    assert hasattr(service, "_create_validation_error_response")
    assert hasattr(service, "_create_permission_denied_response")
    assert hasattr(service, "_create_not_found_response")

    # Test that validation methods work correctly (these will be implemented in future tasks)
    # For now, just test that the service has the expected structure
    assert hasattr(service, "_logger")
    assert hasattr(service, "_discord_client")
    assert hasattr(service, "_settings")

    # Test response creation
    error_response = service._create_validation_error_response(
        "Message content",
        "Content cannot be empty",
        "Please provide a non-empty message.",
    )
    assert "❌ Error:" in error_response
    assert "cannot be empty" in error_response

    # Test permission denied response
    perm_response = service._create_permission_denied_response("guild", "123456789")
    expected = "# Access Denied\n\nAccess to guild `123456789` is not permitted."
    assert perm_response == expected

    # Test not found response
    not_found_response = service._create_not_found_response("User", "987654321")
    expected = "# User Not Found\n\nUser with ID `987654321` was not found or bot has no access."
    assert not_found_response == expected

    print("✅ DiscordService validation integration test passed")


if __name__ == "__main__":
    test_discord_service_validation_integration()
    print("\n🎉 Validation integration tests passed successfully!")
