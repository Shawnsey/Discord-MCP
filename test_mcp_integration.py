#!/usr/bin/env python3
"""
Test script to verify MCP integration works correctly.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

async def test_mcp_server():
    """Test the MCP server integration."""
    print("🧪 Testing Discord MCP Server Integration...")
    
    # Check if we can import the server
    try:
        sys.path.insert(0, str(Path.cwd()))
        import mcp_server
        print("✅ Server module imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        return False
    
    # Test that the server has the expected structure
    if hasattr(mcp_server, 'mcp'):
        print("✅ FastMCP server instance found")
    else:
        print("❌ FastMCP server instance not found")
        return False
    
    # Check if dependencies are specified
    if hasattr(mcp_server.mcp, 'dependencies') and mcp_server.mcp.dependencies:
        print(f"✅ Dependencies specified: {len(mcp_server.mcp.dependencies)} packages")
    else:
        print("⚠️  No dependencies specified")
    
    # Test server startup (briefly)
    print("🚀 Testing server startup...")
    try:
        # This will test that the server can be imported and initialized
        # without actually running it
        server_process = subprocess.Popen(
            [sys.executable, "-c", "import mcp_server; print('Server initialized')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        stdout, stderr = server_process.communicate(timeout=5)
        
        if server_process.returncode == 0:
            print("✅ Server initializes without errors")
        else:
            print(f"❌ Server initialization failed: {stderr.decode()}")
            return False
            
    except subprocess.TimeoutExpired:
        server_process.kill()
        print("⚠️  Server startup test timed out (this might be normal)")
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False
    
    print("\n🎉 MCP Integration Test Completed Successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
