"""
Tests for Discord MCP resources.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.server.fastmcp import FastMCP

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError
from discord_mcp.resources import register_resources
from discord_mcp.services import IDiscordService


@pytest.fixture
def server_with_resources():
    """Create FastMCP server with resources registered."""
    server = FastMCP("Test Server")
    register_resources(server)
    return server


@pytest.fixture
def mock_discord_service():
    """Create a mock DiscordService."""
    mock_service = AsyncMock(spec=IDiscordService)
    return mock_service


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678",
    )


def create_mock_context(mock_discord_service, settings=None):
    """Helper function to create mock context."""
    if settings is None:
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
        )

    context = MagicMock()
    context.request_context.lifespan_context = {
        "discord_service": mock_discord_service,
        "settings": settings,
    }
    return context


def extract_resource_result(read_resource_result):
    """Extract the actual result string from FastMCP read_resource return value."""
    # read_resource returns a list of ReadResourceContents objects
    if isinstance(read_resource_result, list) and len(read_resource_result) > 0:
        return read_resource_result[0].content
    else:
        return str(read_resource_result)


class TestResourcesIntegration:
    """Test resources integration with DiscordService."""

    @pytest.mark.asyncio
    async def test_guilds_resource_integration(
        self, server_with_resources, mock_discord_service
    ):
        """Test guilds resource integration with DiscordService."""
        expected_response = (
            "# Discord Guilds\n\nFound 2 accessible guild(s):\n\n## Test Guild"
        )
        mock_discord_service.get_guilds_formatted.return_value = expected_response

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the resource through the server
        result = await server_with_resources.read_resource("guilds://")
        actual_result = extract_resource_result(result)

        # Verify the service was called
        mock_discord_service.get_guilds_formatted.assert_called_once()

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_channels_resource_integration(
        self, server_with_resources, mock_discord_service
    ):
        """Test channels resource integration with DiscordService."""
        guild_id = "guild123"
        expected_response = "# Channels in Test Guild\n\nFound 3 accessible channel(s):"
        mock_discord_service.get_channels_formatted.return_value = expected_response

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the resource through the server
        result = await server_with_resources.read_resource(f"channels://{guild_id}")
        actual_result = extract_resource_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_channels_formatted.assert_called_once_with(guild_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_messages_resource_integration(
        self, server_with_resources, mock_discord_service
    ):
        """Test messages resource integration with DiscordService."""
        channel_id = "channel123"
        expected_response = "# Messages in #general\n\nShowing 2 recent message(s):"
        mock_discord_service.get_messages_formatted.return_value = expected_response

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the resource through the server
        result = await server_with_resources.read_resource(f"messages://{channel_id}")
        actual_result = extract_resource_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_messages_formatted.assert_called_once_with(channel_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_user_resource_integration(
        self, server_with_resources, mock_discord_service
    ):
        """Test user resource integration with DiscordService."""
        user_id = "user123"
        expected_response = "# User: TestUser\n\n- **Username**: TestUser"
        mock_discord_service.get_user_info_formatted.return_value = expected_response

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the resource through the server
        result = await server_with_resources.read_resource(f"user://{user_id}")
        actual_result = extract_resource_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_user_info_formatted.assert_called_once_with(user_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_resources_use_discord_service_context(
        self, server_with_resources, mock_discord_service
    ):
        """Test that resources properly access DiscordService from context."""
        # Setup mock responses for all service methods
        mock_discord_service.get_guilds_formatted.return_value = "Guilds response"
        mock_discord_service.get_channels_formatted.return_value = "Channels response"
        mock_discord_service.get_messages_formatted.return_value = "Messages response"
        mock_discord_service.get_user_info_formatted.return_value = "User info response"

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Test each resource calls the appropriate service method
        await server_with_resources.read_resource("guilds://")
        mock_discord_service.get_guilds_formatted.assert_called_once()

        await server_with_resources.read_resource("channels://guild123")
        mock_discord_service.get_channels_formatted.assert_called_once_with("guild123")

        await server_with_resources.read_resource("messages://channel123")
        mock_discord_service.get_messages_formatted.assert_called_once_with(
            "channel123"
        )

        await server_with_resources.read_resource("user://user123")
        mock_discord_service.get_user_info_formatted.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_resource_parameter_handling(
        self, server_with_resources, mock_discord_service
    ):
        """Test that resources handle parameters correctly."""
        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Setup mock responses
        mock_discord_service.get_channels_formatted.return_value = "Channels response"
        mock_discord_service.get_messages_formatted.return_value = "Messages response"
        mock_discord_service.get_user_info_formatted.return_value = "User info response"

        # Test parameter passing
        test_guild_id = "test_guild_123"
        test_channel_id = "test_channel_456"
        test_user_id = "test_user_789"

        await server_with_resources.read_resource(f"channels://{test_guild_id}")
        mock_discord_service.get_channels_formatted.assert_called_with(test_guild_id)

        await server_with_resources.read_resource(f"messages://{test_channel_id}")
        mock_discord_service.get_messages_formatted.assert_called_with(test_channel_id)

        await server_with_resources.read_resource(f"user://{test_user_id}")
        mock_discord_service.get_user_info_formatted.assert_called_with(test_user_id)

    @pytest.mark.asyncio
    async def test_error_handling_preserved(
        self, server_with_resources, mock_discord_service
    ):
        """Test that error handling is preserved through service layer."""
        error_response = "# Error\n\nDiscord API error while fetching guilds: API Error"
        mock_discord_service.get_guilds_formatted.return_value = error_response

        # Mock the server context
        server_with_resources.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the resource
        result = await server_with_resources.read_resource("guilds://")
        actual_result = extract_resource_result(result)

        # Verify error response is returned
        assert actual_result == error_response
        assert "Error" in actual_result
        assert "Discord API error" in actual_result
