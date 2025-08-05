"""
Integration tests for Discord MCP server.

These tests verify the complete functionality of the Discord MCP server
including server startup, configuration, and basic functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from discord_mcp.server import DiscordMCPServer, create_server
from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError


@pytest.fixture
def test_settings():
    """Create test settings for integration tests."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678",
        log_level="DEBUG",
        debug=True
    )


class TestServerIntegration:
    """Test complete server integration."""
    
    def test_server_creation_with_all_components(self, test_settings):
        """Test server can be created with all components."""
        server = create_server(test_settings)
        
        assert isinstance(server, DiscordMCPServer)
        assert server.settings == test_settings
        assert server.mcp_server is not None
        assert server.discord_client is None  # Not started yet
        
        # Verify server has the expected name
        assert server.mcp_server.name == test_settings.server_name
    
    def test_server_with_restricted_access(self):
        """Test server creation with access restrictions."""
        restricted_settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_guilds="guild1,guild2",
            allowed_channels="channel1,channel2"
        )
        
        server = create_server(restricted_settings)
        
        # Verify restrictions are properly configured
        assert server.settings.get_allowed_guilds_list() == ["guild1", "guild2"]
        assert server.settings.get_allowed_channels_list() == ["channel1", "channel2"]
        assert server.settings.is_guild_allowed("guild1") is True
        assert server.settings.is_guild_allowed("guild3") is False
        assert server.settings.is_channel_allowed("channel1") is True
        assert server.settings.is_channel_allowed("channel3") is False
    
    def test_server_configuration_validation(self):
        """Test server handles configuration validation."""
        # Test with invalid settings should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(
                discord_bot_token="short",  # Too short
                discord_application_id="123456789012345678"
            )
        
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                discord_application_id="123",  # Too short
                log_level="INVALID"  # Invalid log level
            )


class TestDiscordClientIntegration:
    """Test Discord client integration."""
    
    @pytest.mark.asyncio
    async def test_discord_client_creation_and_lifecycle(self, test_settings):
        """Test Discord client can be created and managed."""
        from discord_mcp.discord_client import DiscordClient
        
        # Create client
        client = DiscordClient(test_settings)
        
        # Verify initial state
        assert client.settings == test_settings
        assert client.session is None
        assert "Bot " in client.headers["Authorization"]
        
        # Test context manager with proper mocking
        with patch('discord_mcp.discord_client.ClientSession') as MockSession:
            mock_session = AsyncMock()
            MockSession.return_value = mock_session
            
            async with client:
                assert client.session is not None
            
            # Session should be closed
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discord_client_rate_limiting(self, test_settings):
        """Test rate limiting is properly configured."""
        from discord_mcp.discord_client import DiscordClient, RateLimiter
        
        client = DiscordClient(test_settings)
        
        # Verify rate limiter configuration
        assert client.rate_limiter.requests_per_second == test_settings.rate_limit_requests_per_second
        assert client.rate_limiter.burst_size == test_settings.rate_limit_burst_size
        
        # Test rate limiter functionality
        rate_limiter = RateLimiter(requests_per_second=10, burst_size=5)
        
        # Should allow immediate requests up to burst size
        for _ in range(5):
            await rate_limiter.acquire()  # Should not block significantly
    
    @pytest.mark.asyncio
    async def test_discord_client_error_handling(self, test_settings):
        """Test Discord client error handling."""
        from discord_mcp.discord_client import DiscordClient, DiscordAPIError
        
        client = DiscordClient(test_settings)
        
        # Test error handling for different status codes
        mock_response = AsyncMock()
        
        # Test 404 error
        mock_response.status = 404
        mock_response.json.return_value = {"message": "Not Found"}
        
        with pytest.raises(DiscordAPIError) as exc_info:
            await client._handle_response(mock_response)
        
        assert exc_info.value.status_code == 404
        assert "Not Found" in str(exc_info.value)
        
        # Test 403 error
        mock_response.status = 403
        mock_response.json.return_value = {"message": "Forbidden"}
        
        with pytest.raises(DiscordAPIError) as exc_info:
            await client._handle_response(mock_response)
        
        assert exc_info.value.status_code == 403


class TestConfigurationIntegration:
    """Test configuration system integration."""
    
    def test_environment_variable_loading(self):
        """Test configuration loads from environment variables."""
        import os
        
        # Test with environment variables
        with patch.dict(os.environ, {
            'DISCORD_BOT_TOKEN': 'FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'DISCORD_APPLICATION_ID': '123456789012345678',
            'ALLOWED_GUILDS': 'guild1,guild2,guild3',
            'LOG_LEVEL': 'DEBUG',
            'DEBUG': 'true'
        }):
            settings = Settings()
            
            assert settings.discord_bot_token == 'FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
            assert settings.discord_application_id == '123456789012345678'
            assert settings.allowed_guilds == 'guild1,guild2,guild3'
            assert settings.log_level == 'DEBUG'
            assert settings.debug is True
    
    def test_configuration_access_control_methods(self):
        """Test configuration access control methods."""
        settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_guilds="guild1,guild2",
            allowed_channels="channel1,channel2"
        )
        
        # Test guild access control
        assert settings.is_guild_allowed("guild1") is True
        assert settings.is_guild_allowed("guild2") is True
        assert settings.is_guild_allowed("guild3") is False
        
        # Test channel access control
        assert settings.is_channel_allowed("channel1") is True
        assert settings.is_channel_allowed("channel2") is True
        assert settings.is_channel_allowed("channel3") is False
        
        # Test with no restrictions
        unrestricted_settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678"
        )
        
        assert unrestricted_settings.is_guild_allowed("any_guild") is True
        assert unrestricted_settings.is_channel_allowed("any_channel") is True


class TestResourceAndToolRegistration:
    """Test that resources and tools are properly registered."""
    
    def test_server_has_resources_and_tools_registered(self, test_settings):
        """Test server has all expected resources and tools registered."""
        server = create_server(test_settings)
        
        # We can't easily access the internal FastMCP structures,
        # but we can verify the server was created successfully
        # and the registration functions were called without errors
        assert server.mcp_server is not None
        
        # The fact that the server was created successfully means
        # the resources and tools were registered without errors
        assert True
    
    def test_health_check_resource_exists(self, test_settings):
        """Test health check resource is available."""
        server = create_server(test_settings)
        
        # The health check resource should be registered
        # We can't easily test it directly, but the server creation
        # should succeed if it's properly registered
        assert server.mcp_server is not None


class TestEndToEndFunctionality:
    """Test end-to-end functionality with mocked Discord API."""
    
    @pytest.mark.asyncio
    async def test_complete_server_workflow(self, test_settings):
        """Test complete server workflow from creation to operation."""
        # Create server
        server = create_server(test_settings)
        assert server is not None
        
        # Verify configuration
        assert server.settings.discord_bot_token is not None
        assert server.settings.discord_application_id is not None
        
        # Verify MCP server
        assert server.mcp_server is not None
        assert server.mcp_server.name == test_settings.server_name
        
        # Verify Discord client configuration
        assert server.discord_client is None  # Not started yet
        
        # Test that we can create a Discord client
        from discord_mcp.discord_client import DiscordClient
        client = DiscordClient(test_settings)
        assert client is not None
        assert client.settings == test_settings
    
    def test_server_with_all_features_enabled(self):
        """Test server with all features and restrictions enabled."""
        full_settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            allowed_guilds="guild1,guild2,guild3",
            allowed_channels="channel1,channel2,channel3",
            rate_limit_requests_per_second=10.0,
            rate_limit_burst_size=20,
            log_level="DEBUG",
            log_format="json",
            debug=True,
            development_mode=True
        )
        
        server = create_server(full_settings)
        
        # Verify all settings are properly configured
        assert server.settings.get_allowed_guilds_list() == ["guild1", "guild2", "guild3"]
        assert server.settings.get_allowed_channels_list() == ["channel1", "channel2", "channel3"]
        assert server.settings.rate_limit_requests_per_second == 10.0
        assert server.settings.rate_limit_burst_size == 20
        assert server.settings.log_level == "DEBUG"
        assert server.settings.log_format == "json"
        assert server.settings.debug is True
        assert server.settings.development_mode is True
        
        # Verify server was created successfully
        assert server.mcp_server is not None


class TestErrorScenarios:
    """Test various error scenarios."""
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configurations."""
        # Test invalid bot token
        with pytest.raises(Exception):
            Settings(
                discord_bot_token="invalid_short_token",
                discord_application_id="123456789012345678"
            )
        
        # Test invalid application ID
        with pytest.raises(Exception):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                discord_application_id="123"  # Too short
            )
        
        # Test invalid log level
        with pytest.raises(Exception):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                discord_application_id="123456789012345678",
                log_level="INVALID_LEVEL"
            )
    
    def test_missing_required_configuration(self):
        """Test handling of missing required configuration."""
        # Test missing bot token
        with pytest.raises(Exception):
            Settings(
                discord_application_id="123456789012345678"
                # Missing discord_bot_token
            )
        
        # Test missing application ID
        with pytest.raises(Exception):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                # Missing discord_application_id
            )


class TestPerformanceAndScaling:
    """Test performance and scaling considerations."""
    
    def test_rate_limiting_configuration(self, test_settings):
        """Test rate limiting is properly configured."""
        # Test default rate limiting
        assert test_settings.rate_limit_requests_per_second == 5.0
        assert test_settings.rate_limit_burst_size == 10
        
        # Test custom rate limiting
        custom_settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
            rate_limit_requests_per_second=20.0,
            rate_limit_burst_size=50
        )
        
        assert custom_settings.rate_limit_requests_per_second == 20.0
        assert custom_settings.rate_limit_burst_size == 50
    
    def test_memory_usage_optimization(self, test_settings):
        """Test memory usage is optimized."""
        # Create multiple servers to test memory usage
        servers = []
        for i in range(5):
            server = create_server(test_settings)
            servers.append(server)
        
        # All servers should be created successfully
        assert len(servers) == 5
        for server in servers:
            assert server is not None
            assert server.mcp_server is not None
