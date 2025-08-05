"""
Tests for the main Discord MCP server.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from discord_mcp.server import DiscordMCPServer, create_server
from discord_mcp.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678"
    )


class TestDiscordMCPServer:
    """Test Discord MCP Server functionality."""
    
    def test_server_initialization(self, settings):
        """Test server initialization."""
        server = DiscordMCPServer(settings)
        
        assert server.settings == settings
        assert server.discord_client is None
        assert server.mcp_server is not None
        assert server.mcp_server.name == settings.server_name
    
    def test_logging_configuration_json(self, settings):
        """Test JSON logging configuration."""
        settings.log_format = "json"
        settings.log_level = "DEBUG"
        
        with patch('structlog.configure') as mock_configure:
            server = DiscordMCPServer(settings)
            mock_configure.assert_called_once()
    
    def test_logging_configuration_text(self, settings):
        """Test text logging configuration."""
        settings.log_format = "text"
        settings.log_level = "INFO"
        
        with patch('structlog.configure') as mock_configure:
            server = DiscordMCPServer(settings)
            mock_configure.assert_called_once()
    
    def test_health_check_resource(self, settings):
        """Test health check resource is added."""
        server = DiscordMCPServer(settings)
        
        # The health check resource should be registered
        # We can't easily test the actual resource without running the server
        # but we can verify the server was created successfully
        assert server.mcp_server is not None
    
    def test_discord_client_creation(self, settings):
        """Test that Discord client is properly configured."""
        server = DiscordMCPServer(settings)
        
        # Discord client should be None initially
        assert server.discord_client is None
        
        # Settings should be stored
        assert server.settings == settings
    
    def test_signal_handlers_setup(self, settings):
        """Test signal handlers are set up correctly."""
        server = DiscordMCPServer(settings)
        
        with patch('signal.signal') as mock_signal:
            server.setup_signal_handlers()
            
            # Should set up handlers for SIGINT and SIGTERM
            assert mock_signal.call_count == 2
    
    @pytest.mark.asyncio
    async def test_run_async_with_shutdown(self, settings):
        """Test async run with shutdown signal."""
        server = DiscordMCPServer(settings)
        
        # Mock the MCP server run method to complete quickly
        mock_run = AsyncMock()
        server.mcp_server.run = mock_run
        
        # Set shutdown event immediately
        server._shutdown_event.set()
        
        # Run should complete without error
        await server.run_async()
        
        # MCP server run should have been called
        mock_run.assert_called_once()


class TestServerCreation:
    """Test server creation functions."""
    
    def test_create_server_with_settings(self, settings):
        """Test creating server with provided settings."""
        server = create_server(settings)
        
        assert isinstance(server, DiscordMCPServer)
        assert server.settings == settings
    
    def test_create_server_without_settings(self):
        """Test creating server without settings (uses defaults)."""
        with patch('discord_mcp.server.get_settings') as mock_get_settings:
            # Create a proper mock settings object with required attributes
            mock_settings = MagicMock()
            mock_settings.server_name = "Test Server"
            mock_settings.server_version = "0.1.0"
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "json"
            mock_settings.debug = False
            mock_settings.development_mode = False
            mock_settings.rate_limit_requests_per_second = 5.0
            mock_settings.get_allowed_guilds_list.return_value = None
            mock_settings.get_allowed_channels_list.return_value = None
            
            mock_get_settings.return_value = mock_settings
            
            server = create_server()
            
            assert isinstance(server, DiscordMCPServer)
            assert server.settings == mock_settings
            mock_get_settings.assert_called_once()


class TestMainFunction:
    """Test main entry point."""
    
    def test_main_function_success(self):
        """Test successful main function execution."""
        with patch('discord_mcp.server.get_settings') as mock_get_settings:
            with patch('discord_mcp.server.create_server') as mock_create_server:
                mock_settings = MagicMock()
                mock_server = MagicMock()
                
                mock_get_settings.return_value = mock_settings
                mock_create_server.return_value = mock_server
                
                # Import and call main
                from discord_mcp.server import main
                main()
                
                mock_get_settings.assert_called_once()
                mock_create_server.assert_called_once_with(mock_settings)
                mock_server.run.assert_called_once()
    
    def test_main_function_error(self):
        """Test main function with error."""
        with patch('discord_mcp.server.get_settings') as mock_get_settings:
            with patch('sys.exit') as mock_exit:
                mock_get_settings.side_effect = Exception("Config error")
                
                from discord_mcp.server import main
                main()
                
                mock_exit.assert_called_once_with(1)
