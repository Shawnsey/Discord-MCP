#!/usr/bin/env python3
"""
Standalone Discord MCP Server for development and deployment.

This file can be used directly with `mcp dev` and `mcp install` commands.
It runs in stdio mode by default for MCP client compatibility.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from discord_mcp.config import get_settings
from discord_mcp.server import DiscordMCPServer

# Create the server instance for mcp dev
settings = get_settings()
discord_server = DiscordMCPServer(settings)

# Create the FastMCP server instance that mcp dev expects
mcp = discord_server._create_mcp_server()

def main():
    """Main entry point for the server."""
    discord_server.run_stdio()

if __name__ == "__main__":
    main()
