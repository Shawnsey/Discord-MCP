# Discord MCP Server - Local Server Implementation

## Overview

The Discord MCP Server now supports **local HTTP server functionality** similar to your `prompt-mcp` server. It can run in two modes:

1. **SSE Mode** - Local HTTP server for direct connections
2. **stdio Mode** - MCP client subprocess integration

## Implementation Details

### New Files Created

1. **`src/discord_mcp/cli.py`** - Command line interface with argument parsing
2. **`discord_server.py`** - Standalone server entry point
3. **Updated `src/discord_mcp/server.py`** - Added SSE transport support
4. **Updated `src/discord_mcp/__main__.py`** - Uses new CLI

### Transport Modes

#### SSE Mode (Local HTTP Server)
```bash
# Start local server
python discord_server.py --transport sse --port 8000

# Server available at: http://localhost:8000/sse
```

**Features:**
- ✅ Runs as independent HTTP service
- ✅ Multiple client connections
- ✅ Health check endpoint
- ✅ Direct API access
- ✅ Easy debugging and development

#### stdio Mode (MCP Client Integration)
```bash
# For MCP clients (Claude Desktop, Amazon Q, etc.)
python discord_server.py --transport stdio
```

**Features:**
- ✅ Standard MCP protocol compliance
- ✅ Managed by MCP client
- ✅ Secure subprocess communication
- ✅ Automatic lifecycle management

## Usage Examples

### 1. Local Development Server
```bash
# Start with debug logging
python discord_server.py --transport sse --port 8000 --log-level DEBUG

# Custom host and port
python discord_server.py --transport sse --host 0.0.0.0 --port 9000
```

### 2. MCP Client Integration
```bash
# For mcp dev
mcp dev mcp_server.py

# For Claude Desktop (in config)
{
  "mcpServers": {
    "discord": {
      "command": "python",
      "args": ["discord_server.py", "--transport", "stdio"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_token",
        "DISCORD_APPLICATION_ID": "your_app_id"
      }
    }
  }
}
```

### 3. Module Execution
```bash
# Using Python module
python -m discord_mcp --transport sse --port 8000
python -m discord_mcp --transport stdio
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--transport` | Protocol: `stdio` or `sse` | `stdio` |
| `--host` | Host for SSE mode | `127.0.0.1` |
| `--port` | Port for SSE mode | `8000` |
| `--mount-path` | SSE mount path | `/sse` |
| `--log-level` | Logging level | `INFO` |
| `--log-format` | Log format: `text` or `json` | `text` |

## Architecture

### Server Structure
```
DiscordMCPServer
├── _configure_logging()     # Structured logging setup
├── _create_mcp_server()     # FastMCP server creation
├── _add_health_check()      # Health endpoint
├── run_stdio()              # stdio transport
└── run_sse()                # SSE transport
```

### Lifecycle Management
- **Startup**: Discord client initialization
- **Runtime**: Request handling and rate limiting
- **Shutdown**: Graceful cleanup and connection closure

## Comparison with prompt-mcp

| Feature | Discord MCP | prompt-mcp |
|---------|-------------|------------|
| **Local HTTP Server** | ✅ SSE transport | ✅ SSE transport |
| **MCP Client Integration** | ✅ stdio transport | ✅ stdio transport |
| **Health Check** | ✅ `/health` endpoint | ✅ `/health` endpoint |
| **Command Line Interface** | ✅ Full CLI | ✅ Full CLI |
| **Multiple Transports** | ✅ stdio + SSE | ✅ stdio + SSE |
| **Structured Logging** | ✅ JSON/text formats | ✅ JSON/text formats |

## Testing

### Local Server Test
```bash
python test_local_server.py
```

### MCP Integration Test
```bash
mcp dev mcp_server.py
python test_mcp_integration.py
```

### Manual Testing
```bash
# Start server
python discord_server.py --transport sse --port 8000

# In another terminal, test health endpoint
curl http://localhost:8000/sse/health
```

## Benefits

### For Development
- **Easy debugging** with local HTTP server
- **Multiple client connections** for testing
- **Direct API access** for development tools
- **Flexible configuration** via command line

### For Production
- **Standard MCP compliance** for client integration
- **Secure subprocess model** with stdio transport
- **Automatic lifecycle management** by MCP clients
- **Comprehensive logging** for monitoring

## Next Steps

The Discord MCP Server now has **feature parity** with your prompt-mcp server in terms of local execution capabilities. You can:

1. **Run it locally** like prompt-mcp for development
2. **Integrate with MCP clients** for production use
3. **Deploy as HTTP service** for multi-client scenarios
4. **Use with Amazon Q CLI** when MCP support is available

The server is now **production-ready** and **locally runnable**! 🎉
