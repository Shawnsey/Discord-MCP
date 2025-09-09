"""
Consolidated tests for Discord MCP tools.
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
from discord_mcp.services import IDiscordService
from discord_mcp.tools import register_tools


@pytest.fixture
def server_with_tools():
    """Create FastMCP server with tools registered."""
    server = FastMCP("Test Server")
    register_tools(server)
    return server


@pytest.fixture
def mock_discord_service():
    """Create a mock DiscordService."""
    mock_service = AsyncMock(spec=IDiscordService)
    return mock_service


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


def extract_result(call_tool_result):
    """Extract the actual result string from FastMCP call_tool return value."""
    # call_tool returns (content_list, metadata_dict)
    # We want the 'result' from metadata or the text from content
    content_list, metadata = call_tool_result
    if "result" in metadata:
        return metadata["result"]
    elif content_list and len(content_list) > 0:
        return content_list[0].text
    else:
        return str(call_tool_result)


class TestToolsIntegration:
    """Test tools integration with DiscordService."""

    @pytest.mark.asyncio
    async def test_list_guilds_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test list_guilds tool integration with DiscordService."""
        expected_response = (
            "# Discord Guilds\n\nFound 2 accessible guild(s):\n\n## Test Guild"
        )
        mock_discord_service.get_guilds_formatted.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool("list_guilds", {})
        actual_result = extract_result(result)

        # Verify the service was called
        mock_discord_service.get_guilds_formatted.assert_called_once()

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_list_channels_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test list_channels tool integration with DiscordService."""
        guild_id = "guild123"
        expected_response = "# Channels in Test Guild\n\nFound 3 accessible channel(s):"
        mock_discord_service.get_channels_formatted.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "list_channels", {"guild_id": guild_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_channels_formatted.assert_called_once_with(guild_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_get_messages_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test get_messages tool integration with DiscordService."""
        channel_id = "channel123"
        expected_response = "# Messages in #general\n\nShowing 2 recent message(s):"
        mock_discord_service.get_messages_formatted.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "get_messages", {"channel_id": channel_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_messages_formatted.assert_called_once_with(channel_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_get_user_info_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test get_user_info tool integration with DiscordService."""
        user_id = "user123"
        expected_response = "# User: TestUser\n\n- **Username**: TestUser"
        mock_discord_service.get_user_info_formatted.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "get_user_info", {"user_id": user_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.get_user_info_formatted.assert_called_once_with(user_id)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_send_message_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test send_message tool integration with DiscordService."""
        channel_id = "channel123"
        content = "Hello world!"
        expected_response = "✅ Message sent successfully to #general!"
        mock_discord_service.send_message.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "send_message", {"channel_id": channel_id, "content": content}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.send_message.assert_called_once_with(
            channel_id, content, None
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_send_message_with_reply_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test send_message tool with reply integration with DiscordService."""
        channel_id = "channel123"
        content = "This is a reply"
        reply_to = "msg456"
        expected_response = "✅ Message sent successfully to #general!"
        mock_discord_service.send_message.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "send_message",
            {
                "channel_id": channel_id,
                "content": content,
                "reply_to_message_id": reply_to,
            },
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.send_message.assert_called_once_with(
            channel_id, content, reply_to
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_send_dm_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test send_dm tool integration with DiscordService."""
        user_id = "user123"
        content = "Hello DM!"
        expected_response = "✅ Direct message sent successfully to TestUser!"
        mock_discord_service.send_direct_message.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "send_dm", {"user_id": user_id, "content": content}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.send_direct_message.assert_called_once_with(
            user_id, content
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_read_direct_messages_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test read_direct_messages tool integration with DiscordService."""
        user_id = "user123"
        limit = 10
        expected_response = "📬 **Direct Messages with TestUser**"
        mock_discord_service.read_direct_messages.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "read_direct_messages", {"user_id": user_id, "limit": limit}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.read_direct_messages.assert_called_once_with(
            user_id, limit
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_delete_message_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test delete_message tool integration with DiscordService."""
        channel_id = "channel123"
        message_id = "msg123"
        expected_response = "✅ Message deleted successfully from #general!"
        mock_discord_service.delete_message.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "delete_message", {"channel_id": channel_id, "message_id": message_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.delete_message.assert_called_once_with(
            channel_id, message_id
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_edit_message_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test edit_message tool integration with DiscordService."""
        channel_id = "channel123"
        message_id = "msg123"
        new_content = "Updated content"
        expected_response = "✅ Message edited successfully in #general!"
        mock_discord_service.edit_message.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "edit_message",
            {
                "channel_id": channel_id,
                "message_id": message_id,
                "new_content": new_content,
            },
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.edit_message.assert_called_once_with(
            channel_id, message_id, new_content
        )

        # Verify the result
        assert actual_result == expected_response


class TestModerationToolsIntegration:
    """Test moderation tools integration with DiscordService."""

    @pytest.mark.asyncio
    async def test_timeout_user_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test timeout_user tool integration with DiscordService."""
        guild_id = "guild123"
        user_id = "user123"
        duration_minutes = 30
        reason = "Disruptive behavior"
        expected_response = "✅ User timed out successfully!"
        mock_discord_service.timeout_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "timeout_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "duration_minutes": duration_minutes,
                "reason": reason,
            },
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.timeout_user.assert_called_once_with(
            guild_id, user_id, duration_minutes, reason
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_timeout_user_tool_default_duration(
        self, server_with_tools, mock_discord_service
    ):
        """Test timeout_user tool with default duration parameter."""
        guild_id = "guild123"
        user_id = "user123"
        expected_response = "✅ User timed out successfully!"
        mock_discord_service.timeout_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool without duration_minutes (should use default of 10)
        result = await server_with_tools.call_tool(
            "timeout_user", {"guild_id": guild_id, "user_id": user_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with default duration
        mock_discord_service.timeout_user.assert_called_once_with(
            guild_id, user_id, 10, None
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_timeout_user_tool_parameter_validation_too_short(
        self, server_with_tools, mock_discord_service
    ):
        """Test timeout_user tool parameter validation for duration too short."""
        guild_id = "guild123"
        user_id = "user123"
        duration_minutes = 0  # Invalid: too short

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool with invalid duration
        result = await server_with_tools.call_tool(
            "timeout_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "duration_minutes": duration_minutes,
            },
        )
        actual_result = extract_result(result)

        # Verify error message is returned
        assert "❌ Error: Timeout duration must be at least 1 minute." in actual_result

        # Verify the service was NOT called
        mock_discord_service.timeout_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_timeout_user_tool_parameter_validation_too_long(
        self, server_with_tools, mock_discord_service
    ):
        """Test timeout_user tool parameter validation for duration too long."""
        guild_id = "guild123"
        user_id = "user123"
        duration_minutes = 50000  # Invalid: exceeds 28 days (40320 minutes)

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool with invalid duration
        result = await server_with_tools.call_tool(
            "timeout_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "duration_minutes": duration_minutes,
            },
        )
        actual_result = extract_result(result)

        # Verify error message is returned
        assert (
            "❌ Error: Timeout duration cannot exceed 28 days (40320 minutes)."
            in actual_result
        )

        # Verify the service was NOT called
        mock_discord_service.timeout_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_untimeout_user_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test untimeout_user tool integration with DiscordService."""
        guild_id = "guild123"
        user_id = "user123"
        reason = "Timeout period served"
        expected_response = "✅ User timeout removed successfully!"
        mock_discord_service.untimeout_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "untimeout_user",
            {"guild_id": guild_id, "user_id": user_id, "reason": reason},
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.untimeout_user.assert_called_once_with(
            guild_id, user_id, reason
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_untimeout_user_tool_without_reason(
        self, server_with_tools, mock_discord_service
    ):
        """Test untimeout_user tool without reason parameter."""
        guild_id = "guild123"
        user_id = "user123"
        expected_response = "✅ User timeout removed successfully!"
        mock_discord_service.untimeout_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool without reason
        result = await server_with_tools.call_tool(
            "untimeout_user", {"guild_id": guild_id, "user_id": user_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with None reason
        mock_discord_service.untimeout_user.assert_called_once_with(
            guild_id, user_id, None
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_kick_user_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test kick_user tool integration with DiscordService."""
        guild_id = "guild123"
        user_id = "user123"
        reason = "Violation of server rules"
        expected_response = "✅ User kicked successfully!"
        mock_discord_service.kick_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "kick_user", {"guild_id": guild_id, "user_id": user_id, "reason": reason}
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.kick_user.assert_called_once_with(
            guild_id, user_id, reason
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_kick_user_tool_without_reason(
        self, server_with_tools, mock_discord_service
    ):
        """Test kick_user tool without reason parameter."""
        guild_id = "guild123"
        user_id = "user123"
        expected_response = "✅ User kicked successfully!"
        mock_discord_service.kick_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool without reason
        result = await server_with_tools.call_tool(
            "kick_user", {"guild_id": guild_id, "user_id": user_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with None reason
        mock_discord_service.kick_user.assert_called_once_with(guild_id, user_id, None)

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_ban_user_tool_integration(
        self, server_with_tools, mock_discord_service
    ):
        """Test ban_user tool integration with DiscordService."""
        guild_id = "guild123"
        user_id = "user123"
        reason = "Repeated violations"
        delete_message_days = 3
        expected_response = "✅ User banned successfully!"
        mock_discord_service.ban_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool through the server
        result = await server_with_tools.call_tool(
            "ban_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "reason": reason,
                "delete_message_days": delete_message_days,
            },
        )
        actual_result = extract_result(result)

        # Verify the service was called with correct parameters
        mock_discord_service.ban_user.assert_called_once_with(
            guild_id, user_id, reason, delete_message_days
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_ban_user_tool_default_parameters(
        self, server_with_tools, mock_discord_service
    ):
        """Test ban_user tool with default parameters."""
        guild_id = "guild123"
        user_id = "user123"
        expected_response = "✅ User banned successfully!"
        mock_discord_service.ban_user.return_value = expected_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool with minimal parameters
        result = await server_with_tools.call_tool(
            "ban_user", {"guild_id": guild_id, "user_id": user_id}
        )
        actual_result = extract_result(result)

        # Verify the service was called with default values
        mock_discord_service.ban_user.assert_called_once_with(
            guild_id, user_id, None, 0
        )

        # Verify the result
        assert actual_result == expected_response

    @pytest.mark.asyncio
    async def test_ban_user_tool_parameter_validation_negative_days(
        self, server_with_tools, mock_discord_service
    ):
        """Test ban_user tool parameter validation for negative delete_message_days."""
        guild_id = "guild123"
        user_id = "user123"
        delete_message_days = -1  # Invalid: negative

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool with invalid delete_message_days
        result = await server_with_tools.call_tool(
            "ban_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "delete_message_days": delete_message_days,
            },
        )
        actual_result = extract_result(result)

        # Verify error message is returned
        assert "❌ Error: delete_message_days must be 0 or greater." in actual_result

        # Verify the service was NOT called
        mock_discord_service.ban_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_ban_user_tool_parameter_validation_too_many_days(
        self, server_with_tools, mock_discord_service
    ):
        """Test ban_user tool parameter validation for delete_message_days too high."""
        guild_id = "guild123"
        user_id = "user123"
        delete_message_days = 10  # Invalid: exceeds 7 days limit

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool with invalid delete_message_days
        result = await server_with_tools.call_tool(
            "ban_user",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "delete_message_days": delete_message_days,
            },
        )
        actual_result = extract_result(result)

        # Verify error message is returned
        assert (
            "❌ Error: delete_message_days cannot exceed 7 days (Discord API limit)."
            in actual_result
        )

        # Verify the service was NOT called
        mock_discord_service.ban_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_moderation_tools_context_retrieval(
        self, server_with_tools, mock_discord_service
    ):
        """Test that moderation tools properly retrieve context and delegate to service."""
        # Setup mock responses for all moderation service methods
        mock_discord_service.timeout_user.return_value = "Timeout response"
        mock_discord_service.untimeout_user.return_value = "Untimeout response"
        mock_discord_service.kick_user.return_value = "Kick response"
        mock_discord_service.ban_user.return_value = "Ban response"

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Test each moderation tool calls the appropriate service method
        await server_with_tools.call_tool(
            "timeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.timeout_user.assert_called_once_with(
            "guild123", "user123", 10, None
        )

        await server_with_tools.call_tool(
            "untimeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.untimeout_user.assert_called_once_with(
            "guild123", "user123", None
        )

        await server_with_tools.call_tool(
            "kick_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.kick_user.assert_called_once_with(
            "guild123", "user123", None
        )

        await server_with_tools.call_tool(
            "ban_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.ban_user.assert_called_once_with(
            "guild123", "user123", None, 0
        )

    @pytest.mark.asyncio
    async def test_moderation_tools_error_handling(
        self, server_with_tools, mock_discord_service
    ):
        """Test that moderation tools preserve error handling from service layer."""
        error_response = (
            "❌ Error: Bot does not have 'moderate_members' permission in this server."
        )
        mock_discord_service.timeout_user.return_value = error_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool
        result = await server_with_tools.call_tool(
            "timeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        actual_result = extract_result(result)

        # Verify error response is returned
        assert actual_result == error_response
        assert "❌ Error:" in actual_result
        assert "moderate_members" in actual_result

    @pytest.mark.asyncio
    async def test_moderation_tools_response_formatting(
        self, server_with_tools, mock_discord_service
    ):
        """Test that moderation tools return properly formatted responses."""
        success_response = "✅ User timed out successfully!\n- **User**: TestUser (123456789)\n- **Duration**: 10 minutes"
        mock_discord_service.timeout_user.return_value = success_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool
        result = await server_with_tools.call_tool(
            "timeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        actual_result = extract_result(result)

        # Verify response formatting is preserved
        assert actual_result == success_response
        assert "✅" in actual_result
        assert "User timed out successfully!" in actual_result
        assert "Duration" in actual_result

    @pytest.mark.asyncio
    async def test_all_tools_registered(self, server_with_tools):
        """Test that all expected tools are registered."""
        tools = await server_with_tools.list_tools()
        tool_names = {tool.name for tool in tools}

        expected_tools = {
            "list_guilds",
            "list_channels",
            "get_messages",
            "get_user_info",
            "send_message",
            "send_dm",
            "read_direct_messages",
            "delete_message",
            "edit_message",
            "timeout_user",
            "untimeout_user",
            "kick_user",
            "ban_user",
        }

        # Verify all expected tools are registered
        for tool_name in expected_tools:
            assert (
                tool_name in tool_names
            ), f"Tool {tool_name} not found in registered tools"

    @pytest.mark.asyncio
    async def test_tools_use_discord_service_context(
        self, server_with_tools, mock_discord_service
    ):
        """Test that tools properly access DiscordService from context."""
        # Setup mock responses for all service methods
        mock_discord_service.get_guilds_formatted.return_value = "Guilds response"
        mock_discord_service.get_channels_formatted.return_value = "Channels response"
        mock_discord_service.get_messages_formatted.return_value = "Messages response"
        mock_discord_service.get_user_info_formatted.return_value = "User info response"
        mock_discord_service.send_message.return_value = "Message sent response"
        mock_discord_service.send_direct_message.return_value = "DM sent response"
        mock_discord_service.read_direct_messages.return_value = "DM read response"
        mock_discord_service.delete_message.return_value = "Message deleted response"
        mock_discord_service.edit_message.return_value = "Message edited response"
        mock_discord_service.timeout_user.return_value = "Timeout response"
        mock_discord_service.untimeout_user.return_value = "Untimeout response"
        mock_discord_service.kick_user.return_value = "Kick response"
        mock_discord_service.ban_user.return_value = "Ban response"

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Test each tool calls the appropriate service method
        await server_with_tools.call_tool("list_guilds", {})
        mock_discord_service.get_guilds_formatted.assert_called_once()

        await server_with_tools.call_tool("list_channels", {"guild_id": "guild123"})
        mock_discord_service.get_channels_formatted.assert_called_once_with("guild123")

        await server_with_tools.call_tool("get_messages", {"channel_id": "channel123"})
        mock_discord_service.get_messages_formatted.assert_called_once_with(
            "channel123"
        )

        await server_with_tools.call_tool("get_user_info", {"user_id": "user123"})
        mock_discord_service.get_user_info_formatted.assert_called_once_with("user123")

        await server_with_tools.call_tool(
            "send_message", {"channel_id": "channel123", "content": "content"}
        )
        mock_discord_service.send_message.assert_called_once_with(
            "channel123", "content", None
        )

        await server_with_tools.call_tool(
            "send_dm", {"user_id": "user123", "content": "content"}
        )
        mock_discord_service.send_direct_message.assert_called_once_with(
            "user123", "content"
        )

        await server_with_tools.call_tool(
            "read_direct_messages", {"user_id": "user123", "limit": 10}
        )
        mock_discord_service.read_direct_messages.assert_called_once_with("user123", 10)

        await server_with_tools.call_tool(
            "delete_message", {"channel_id": "channel123", "message_id": "msg123"}
        )
        mock_discord_service.delete_message.assert_called_once_with(
            "channel123", "msg123"
        )

        await server_with_tools.call_tool(
            "edit_message",
            {
                "channel_id": "channel123",
                "message_id": "msg123",
                "new_content": "new content",
            },
        )
        mock_discord_service.edit_message.assert_called_once_with(
            "channel123", "msg123", "new content"
        )

        await server_with_tools.call_tool(
            "timeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.timeout_user.assert_called_once_with(
            "guild123", "user123", 10, None
        )

        await server_with_tools.call_tool(
            "untimeout_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.untimeout_user.assert_called_once_with(
            "guild123", "user123", None
        )

        await server_with_tools.call_tool(
            "kick_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.kick_user.assert_called_once_with(
            "guild123", "user123", None
        )

        await server_with_tools.call_tool(
            "ban_user", {"guild_id": "guild123", "user_id": "user123"}
        )
        mock_discord_service.ban_user.assert_called_once_with(
            "guild123", "user123", None, 0
        )

    @pytest.mark.asyncio
    async def test_error_handling_preserved(
        self, server_with_tools, mock_discord_service
    ):
        """Test that error handling is preserved through service layer."""
        error_response = "# Error\n\nDiscord API error while fetching guilds: API Error"
        mock_discord_service.get_guilds_formatted.return_value = error_response

        # Mock the server context
        server_with_tools.get_context = MagicMock(
            return_value=create_mock_context(mock_discord_service)
        )

        # Call the tool
        result = await server_with_tools.call_tool("list_guilds", {})
        actual_result = extract_result(result)

        # Verify error response is returned
        assert actual_result == error_response
        assert "Error" in actual_result
        assert "Discord API error" in actual_result
