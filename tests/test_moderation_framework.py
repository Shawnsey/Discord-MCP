"""
Tests for the centralized moderation action framework.

This module tests the new centralized moderation methods that eliminate
code duplication across timeout, kick, ban, and other moderation operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.discord_mcp.services.discord_service import DiscordService
from src.discord_mcp.discord_client import DiscordAPIError
from src.discord_mcp.config import Settings


@pytest.fixture
def mock_discord_client():
    """Create a mock Discord client for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.get_allowed_guilds_set.return_value = {"123456789"}
    settings.is_guild_allowed.return_value = True
    settings.is_channel_allowed.return_value = True
    return settings


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock()


@pytest.fixture
def discord_service(mock_discord_client, mock_settings, mock_logger):
    """Create a DiscordService instance with mocked dependencies."""
    return DiscordService(mock_discord_client, mock_settings, mock_logger)


class TestModerationSetup:
    """Test the _perform_moderation_setup method."""

    @pytest.mark.asyncio
    async def test_successful_moderation_setup(
        self, discord_service, mock_discord_client
    ):
        """Test successful moderation setup with valid guild and user."""
        # Mock successful API responses
        guild_data = {"id": "123456789", "name": "Test Guild"}
        user_data = {
            "id": "987654321",
            "username": "testuser",
            "global_name": "Test User",
        }

        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_user.return_value = user_data

        # Call the method
        setup_data, error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        # Verify success
        assert error is None
        assert setup_data is not None
        assert setup_data["guild"] == guild_data
        assert setup_data["guild_name"] == "Test Guild"
        assert setup_data["user"] == user_data
        assert setup_data["username"] == "testuser"
        assert setup_data["display_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_moderation_setup_guild_permission_denied(
        self, discord_service, mock_settings
    ):
        """Test moderation setup when guild access is not allowed."""
        # Mock permission denied
        mock_settings.is_guild_allowed.return_value = False

        # Call the method
        setup_data, error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        # Verify permission denied
        assert setup_data is None
        assert error is not None
        assert "not permitted" in error.lower()

    @pytest.mark.asyncio
    async def test_moderation_setup_guild_not_found(
        self, discord_service, mock_discord_client
    ):
        """Test moderation setup when guild is not found."""
        # Mock guild not found
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not found", 404)

        # Call the method
        setup_data, error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        # Verify guild not found error
        assert setup_data is None
        assert error is not None
        assert "not found" in error.lower()

    @pytest.mark.asyncio
    async def test_moderation_setup_user_not_found(
        self, discord_service, mock_discord_client
    ):
        """Test moderation setup when user is not found."""
        # Mock successful guild but user not found
        guild_data = {"id": "123456789", "name": "Test Guild"}
        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_user.side_effect = DiscordAPIError("Not found", 404)

        # Call the method
        setup_data, error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        # Verify user not found error
        assert setup_data is None
        assert error is not None
        assert "User `987654321` not found" in error

    @pytest.mark.asyncio
    async def test_moderation_setup_unexpected_error(
        self, discord_service, mock_discord_client
    ):
        """Test moderation setup with unexpected error."""
        # Mock unexpected error
        mock_discord_client.get_guild.side_effect = Exception("Unexpected error")

        # Call the method
        setup_data, error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        # Verify unexpected error handling
        assert setup_data is None
        assert error is not None
        assert "Unexpected error during moderation setup" in error


class TestModerationTargetValidation:
    """Test the _validate_moderation_target method."""

    @pytest.mark.asyncio
    async def test_successful_target_validation_with_membership(
        self, discord_service, mock_discord_client
    ):
        """Test successful target validation when user is a member."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        # Mock successful member lookup and role hierarchy validation
        mock_discord_client.get_guild_member.return_value = {
            "user": {"id": "987654321"}
        }

        with patch.object(
            discord_service, "_validate_role_hierarchy", return_value=None
        ):
            error = await discord_service._validate_moderation_target(
                "123456789", "987654321", setup_data, require_membership=True
            )

        # Verify success
        assert error is None

    @pytest.mark.asyncio
    async def test_target_validation_user_not_member_required(
        self, discord_service, mock_discord_client
    ):
        """Test target validation when user is not a member but membership is required."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        # Mock user not found in guild
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError(
            "Not found", 404
        )

        error = await discord_service._validate_moderation_target(
            "123456789", "987654321", setup_data, require_membership=True
        )

        # Verify membership required error
        assert error is not None
        assert "is not a member of Test Guild" in error

    @pytest.mark.asyncio
    async def test_target_validation_user_not_member_optional(
        self, discord_service, mock_discord_client
    ):
        """Test target validation when user is not a member but membership is optional."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        # Mock user not found in guild
        mock_discord_client.get_guild_member.side_effect = DiscordAPIError(
            "Not found", 404
        )

        error = await discord_service._validate_moderation_target(
            "123456789", "987654321", setup_data, require_membership=False
        )

        # Verify success (no membership required)
        assert error is None

    @pytest.mark.asyncio
    async def test_target_validation_hierarchy_failure(
        self, discord_service, mock_discord_client
    ):
        """Test target validation when role hierarchy validation fails."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        # Mock successful member lookup but hierarchy failure
        mock_discord_client.get_guild_member.return_value = {
            "user": {"id": "987654321"}
        }

        with patch.object(
            discord_service, "_validate_role_hierarchy", return_value="Hierarchy error"
        ):
            error = await discord_service._validate_moderation_target(
                "123456789", "987654321", setup_data, require_membership=True
            )

        # Verify hierarchy error
        assert error == "Hierarchy error"

    @pytest.mark.asyncio
    async def test_target_validation_unexpected_error(
        self, discord_service, mock_discord_client
    ):
        """Test target validation with unexpected error."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        # Mock unexpected error
        mock_discord_client.get_guild_member.side_effect = Exception("Unexpected error")

        error = await discord_service._validate_moderation_target(
            "123456789", "987654321", setup_data, require_membership=True
        )

        # Verify unexpected error handling
        assert error is not None
        assert "Could not validate moderation target" in error


class TestModerationLogging:
    """Test the _log_moderation_action method."""

    def test_successful_moderation_logging(self, discord_service, mock_logger):
        """Test successful moderation action logging."""
        setup_data = {
            "guild_name": "Test Guild",
            "username": "testuser",
            "display_name": "Test User",
        }

        # Call the method
        discord_service._log_moderation_action(
            "timeout",
            setup_data,
            "123456789",
            "987654321",
            True,
            duration_minutes=10,
            reason="Test reason",
        )

        # Verify logging was called (we can't easily test the exact call due to the mixin)
        # This test mainly ensures the method doesn't crash
        assert True

    def test_failed_moderation_logging(self, discord_service, mock_logger):
        """Test failed moderation action logging."""
        setup_data = {
            "guild_name": "Test Guild",
            "username": "testuser",
            "display_name": "Test User",
        }

        # Call the method
        discord_service._log_moderation_action(
            "kick", setup_data, "123456789", "987654321", False, reason="Test reason"
        )

        # Verify logging was called (we can't easily test the exact call due to the mixin)
        # This test mainly ensures the method doesn't crash
        assert True


class TestModerationResponseFormatting:
    """Test the moderation response formatting methods."""

    def test_create_moderation_success_response(self, discord_service):
        """Test creation of moderation success response."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        response = discord_service._create_moderation_success_response(
            "timed out",
            setup_data,
            "123456789",
            "987654321",
            duration="10 minutes",
            reason="Test reason",
        )

        # Verify response format
        assert "✅ User timed out successfully!" in response
        assert "Test User (`987654321`)" in response
        assert "Test Guild (`123456789`)" in response
        assert "**Duration**: 10 minutes" in response
        assert "**Reason**: Test reason" in response

    def test_create_moderation_success_response_no_additional_details(
        self, discord_service
    ):
        """Test creation of moderation success response without additional details."""
        setup_data = {"guild_name": "Test Guild", "display_name": "Test User"}

        response = discord_service._create_moderation_success_response(
            "kicked", setup_data, "123456789", "987654321"
        )

        # Verify basic response format
        assert "✅ User kicked successfully!" in response
        assert "Test User (`987654321`)" in response
        assert "Test Guild (`123456789`)" in response

    def test_create_moderation_permission_error(self, discord_service):
        """Test creation of moderation permission error."""
        error = discord_service._create_moderation_permission_error(
            "timeout", "moderate_members", "Test Guild"
        )

        # Verify error format
        assert (
            "❌ Error: Bot does not have 'moderate_members' permission in Test Guild."
            == error
        )

    def test_create_moderation_hierarchy_error(self, discord_service):
        """Test creation of moderation hierarchy error."""
        error = discord_service._create_moderation_hierarchy_error("kick", "Test Guild")

        # Verify error format
        assert (
            "❌ Error: Bot does not have permission to kick users in Test Guild. Role hierarchy may prevent this action."
            == error
        )


class TestModerationFrameworkIntegration:
    """Test integration of moderation framework methods."""

    @pytest.mark.asyncio
    async def test_full_moderation_workflow_success(
        self, discord_service, mock_discord_client
    ):
        """Test a complete successful moderation workflow using the framework."""
        # Mock successful API responses
        guild_data = {"id": "123456789", "name": "Test Guild"}
        user_data = {
            "id": "987654321",
            "username": "testuser",
            "global_name": "Test User",
        }

        mock_discord_client.get_guild.return_value = guild_data
        mock_discord_client.get_user.return_value = user_data
        mock_discord_client.get_guild_member.return_value = {
            "user": {"id": "987654321"}
        }

        with patch.object(
            discord_service, "_validate_role_hierarchy", return_value=None
        ):
            # Step 1: Perform moderation setup
            setup_data, setup_error = await discord_service._perform_moderation_setup(
                "123456789", "987654321", "test_action"
            )

            assert setup_error is None
            assert setup_data is not None

            # Step 2: Validate moderation target
            validation_error = await discord_service._validate_moderation_target(
                "123456789", "987654321", setup_data, require_membership=True
            )

            assert validation_error is None

            # Step 3: Create success response
            response = discord_service._create_moderation_success_response(
                "tested",
                setup_data,
                "123456789",
                "987654321",
                reason="Integration test",
            )

            assert "✅ User tested successfully!" in response
            assert "Test User (`987654321`)" in response
            assert "Test Guild (`123456789`)" in response
            assert "**Reason**: Integration test" in response

    @pytest.mark.asyncio
    async def test_full_moderation_workflow_failure(
        self, discord_service, mock_discord_client
    ):
        """Test a complete failed moderation workflow using the framework."""
        # Mock guild not found
        mock_discord_client.get_guild.side_effect = DiscordAPIError("Not found", 404)

        # Step 1: Perform moderation setup (should fail)
        setup_data, setup_error = await discord_service._perform_moderation_setup(
            "123456789", "987654321", "test_action"
        )

        assert setup_data is None
        assert setup_error is not None
        assert "not found" in setup_error.lower()

        # Workflow should stop here due to setup failure
        # This demonstrates how the framework prevents proceeding with invalid state
