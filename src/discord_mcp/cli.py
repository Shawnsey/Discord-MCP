"""Command line interface for the Discord MCP server."""

import argparse
import logging
import signal
import sys

import structlog

from .config import get_settings
from .server import DiscordMCPServer


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """Configure structured logging."""
    level = getattr(logging, log_level.upper(), logging.INFO)

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

    if log_format == "json":
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
    logging.basicConfig(level=level)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Discord MCP Server - Model Context Protocol server for "
            "Discord integration"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio transport (for MCP clients)
  python -m discord_mcp --transport stdio

  # Run with SSE transport (local HTTP server)
  python -m discord_mcp --transport sse --host 0.0.0.0 --port 8000

  # Run with debug logging
  python -m discord_mcp --log-level DEBUG --transport sse
        """,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for SSE transport (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for SSE transport (default: 8000)",
    )

    parser.add_argument(
        "--mount-path",
        default="/sse",
        help="Mount path for SSE transport (default: /sse)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-format",
        choices=["text", "json"],
        default="text",
        help="Log output format (default: text)",
    )

    return parser


async def run_server(
    transport: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    mount_path: str = "/sse",
) -> None:
    """Run the Discord MCP server with specified transport."""
    logger = structlog.get_logger(__name__)

    try:
        settings = get_settings()
        server = DiscordMCPServer(settings)

        if transport == "stdio":
            logger.info(
                "Starting Discord MCP server with stdio transport"
            )
            server.run_stdio()  # This will handle the asyncio loop
        elif transport == "sse":
            logger.info(
                "Starting Discord MCP server with SSE transport",
                host=host,
                port=port,
                mount_path=mount_path,
            )
            server.run_sse(
                host=host, port=port, mount_path=mount_path
            )  # This will handle the asyncio loop
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping server...")
    except Exception as e:
        logger.error("Server error", error=str(e), exc_info=True)
        raise


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_format)
    logger = structlog.get_logger(__name__)

    logger.info("Starting Discord MCP Server", version="0.1.0")

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the server - don't use asyncio.run() since FastMCP handles the event
    # loop
    try:
        # Create settings and server
        settings = get_settings()
        server = DiscordMCPServer(settings)

        if args.transport == "stdio":
            logger.info(
                "Starting Discord MCP server with stdio transport"
            )
            server.run_stdio()
        elif args.transport == "sse":
            logger.info(
                "Starting Discord MCP server with SSE transport",
                host=args.host,
                port=args.port,
                mount_path=args.mount_path,
            )
            server.run_sse(
                host=args.host, port=args.port, mount_path=args.mount_path
            )
        else:
            raise ValueError(f"Unsupported transport: {args.transport}")

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Failed to start server", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
