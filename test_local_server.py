#!/usr/bin/env python3
"""
Test script to verify the Discord MCP server can run locally.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord_mcp.server import DiscordMCPServer
from discord_mcp.config import Settings


async def test_server_creation():
    """Test that we can create a server instance."""
    print("🧪 Testing Discord MCP Server Local Functionality...")
    
    # Create mock settings with proper length tokens
    settings = Settings(
        discord_bot_token="x" * 50,  # Minimum 50 characters
        discord_application_id="1" * 17,  # Minimum 17 characters
        log_level="INFO"
    )
    
    try:
        # Create server instance
        server = DiscordMCPServer(settings)
        print("✅ Server instance created successfully")
        
        # Test that we can create the MCP server (without starting it)
        mcp_server = server._create_mcp_server()
        print("✅ FastMCP server created successfully")
        
        # Check that it has the expected attributes
        if hasattr(mcp_server, 'name'):
            print(f"✅ Server name: {mcp_server.name}")
        
        if hasattr(mcp_server, 'dependencies'):
            print(f"✅ Dependencies: {len(mcp_server.dependencies)} packages")
        
        print("\n🎉 Local Server Test Completed Successfully!")
        print("\n📋 Available Run Modes:")
        print("  1. SSE Mode (Local HTTP Server):")
        print("     python discord_server.py --transport sse --port 8000")
        print("  2. stdio Mode (MCP Client Integration):")
        print("     python discord_server.py --transport stdio")
        print("  3. Module Mode:")
        print("     python -m discord_mcp --transport sse --port 8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_creation())
    sys.exit(0 if success else 1)
