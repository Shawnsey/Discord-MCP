"""
Main FastMCP server implementation for Discord integration.

This module creates and configures the FastMCP server with Discord-specific
resources and tools for AI assistant integration.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

import structlog
from mcp.server.fastmcp import FastMCP

from .config import Settings, get_settings
from .discord_client import DiscordClient
from .resources import register_resources
from .tools import register_tools

logger = structlog.get_logger(__name__)


class DiscordMCPServer:
    """Discord MCP Server wrapper with lifecycle management."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.discord_client: DiscordClient = None
        self.mcp_server: FastMCP = None
        self._shutdown_event = asyncio.Event()
        
        # Configure logging
        self._configure_logging()
    
    def _configure_logging(self) -> None:
        """Configure structured logging."""
        log_level = self.settings.log_level.upper()
        
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        if self.settings.log_format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Set root logger level
        import logging
        logging.basicConfig(level=getattr(logging, log_level))
        
        logger.info("Logging configured", 
                   level=log_level, 
                   format=self.settings.log_format)
    
    def _create_mcp_server(self) -> FastMCP:
        """Create and configure the FastMCP server."""
        if self.mcp_server is not None:
            return self.mcp_server
        
        @asynccontextmanager
        async def discord_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
            """Manage Discord client lifecycle."""
            logger.info("Starting Discord MCP Server", 
                       server_name=self.settings.server_name,
                       version=self.settings.server_version)
            
            # Initialize Discord client
            self.discord_client = DiscordClient(self.settings)
            
            try:
                # Start the Discord client
                await self.discord_client.start()
                
                # Test Discord connection
                user_info = await self.discord_client.get_current_user()
                logger.info("Discord connection established", 
                           bot_username=user_info.get('username'),
                           bot_id=user_info.get('id'))
                
                # Provide context to resources and tools
                yield {
                    "discord_client": self.discord_client,
                    "settings": self.settings
                }
                
            except Exception as e:
                logger.error("Failed to establish Discord connection", error=str(e))
                raise
            finally:
                # Cleanup
                if self.discord_client:
                    await self.discord_client.close()
                    logger.info("Discord client closed")
        
        # Create FastMCP server with lifespan
        self.mcp_server = FastMCP(
            name=self.settings.server_name,
            lifespan=discord_lifespan,
            dependencies=[
                "aiohttp>=3.8.0",
                "pydantic>=2.0.0",
                "pydantic-settings>=2.0.0",
                "python-dotenv>=1.0.0",
                "structlog>=23.0.0",
            ]
        )
        
        # Add health check resource
        self._add_health_check()
        
        # Register Discord resources
        register_resources(self.mcp_server)
        
        # Register Discord tools
        register_tools(self.mcp_server)
        
        logger.info("FastMCP server created", name=self.settings.server_name)
        return self.mcp_server
    
    def _add_health_check(self) -> None:
        """Add health check resource."""
        
        @self.mcp_server.resource("health://status")
        def health_check() -> str:
            """Health check endpoint for the Discord MCP server."""
            return f"""# Discord MCP Server Health Check

**Server**: {self.settings.server_name} v{self.settings.server_version}
**Status**: ✅ Healthy
**Discord API**: Connected
**Rate Limiting**: {self.settings.rate_limit_requests_per_second} req/sec
**Debug Mode**: {self.settings.debug}
**Development Mode**: {self.settings.development_mode}

## Configuration
- **Allowed Guilds**: {len(self.settings.get_allowed_guilds_list()) if self.settings.get_allowed_guilds_list() else 'All'}
- **Allowed Channels**: {len(self.settings.get_allowed_channels_list()) if self.settings.get_allowed_channels_list() else 'All'}
- **Log Level**: {self.settings.log_level}
- **Log Format**: {self.settings.log_format}

## Discord Bot Info
The server is connected and ready to process Discord operations.
"""
    
    def run_stdio(self) -> None:
        """Run the server with stdio transport (for MCP clients)."""
        mcp_server = self._create_mcp_server()
        logger.info("Starting Discord MCP server with stdio transport")
        mcp_server.run(transport="stdio")
    
    def run_sse(self, host: str = "127.0.0.1", port: int = 8000, mount_path: str = "/sse") -> None:
        """Run the server with SSE transport (local HTTP server)."""
        mcp_server = self._create_mcp_server()
        logger.info(
            "Starting Discord MCP server with SSE transport",
            host=host,
            port=port,
            mount_path=mount_path
        )
        mcp_server.run(transport="sse", host=host, port=port, mount_path=mount_path)
    
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def create_server(settings: Settings = None) -> DiscordMCPServer:
    """Create a Discord MCP server instance."""
    if settings is None:
        settings = get_settings()
    
    return DiscordMCPServer(settings)


def main() -> None:
    """Main entry point for the Discord MCP server (stdio mode)."""
    try:
        settings = get_settings()
        server = create_server(settings)
        server.run_stdio()
    except Exception as e:
        logger.error("Failed to start server", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
