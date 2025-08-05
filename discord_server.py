#!/usr/bin/env python3
"""
Standalone Discord MCP Server that can run locally.

This server can run in two modes:
1. SSE (Server-Sent Events) - HTTP server for local connections
2. stdio - For MCP client integration

Usage:
    # Run as local HTTP server (like prompt-mcp)
    python discord_server.py --transport sse --host 0.0.0.0 --port 8000
    
    # Run for MCP client integration
    python discord_server.py --transport stdio
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from discord_mcp.cli import main

if __name__ == "__main__":
    main()
