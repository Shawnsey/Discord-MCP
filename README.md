# Discord MCP Server

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to interact with Discord servers. This server provides full bidirectional communication capabilities including reading from channels, sending messages, managing direct messages, and performing moderation actions through a standardized MCP interface.

## Features

### Resources (Read Operations)
- **Guild Listing** (`guilds://`) - List accessible Discord servers with member counts and permissions
- **Channel Listing** (`channels://{guild_id}`) - List channels in a specific server with metadata
- **Message Reading** (`messages://{channel_id}`) - Read messages from channels with pagination support
- **User Information** (`user://{user_id}`) - Get detailed user profile information
- **Health Check** (`health://status`) - Server status and configuration information

### Tools (Write Operations)
- **Send Message** (`send_message`) - Send messages to Discord channels with reply support
- **Send Direct Message** (`send_dm`) - Send private messages to users
- **Read Direct Messages** (`read_direct_messages`) - Read DM conversations with specific users
- **Message Management** - Delete (`delete_message`) and edit (`edit_message`) messages with permissions
- **Advanced Features** - Support for embeds, attachments, reactions, and rich formatting

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token (see [Discord Bot Setup](#discord-bot-setup))
- MCP-compatible client (Amazon Q CLI, Claude Desktop, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Discord-MCP
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Discord bot token and settings
   ```

5. **Run the server**

   **Option A: Local HTTP Server (SSE Mode)**
   ```bash
   # Run as local HTTP server (like prompt-mcp)
   python discord_server.py --transport sse --port 8000
   
   # Or using module
   python -m discord_mcp --transport sse --port 8000
   
   # With custom host and debug logging
   python discord_server.py --transport sse --host 0.0.0.0 --port 8000 --log-level DEBUG
   ```
   
   **Option B: MCP Client Integration (stdio Mode)**
   ```bash
   # For MCP client integration
   python discord_server.py --transport stdio
   
   # Or using module
   python -m discord_mcp --transport stdio
   ```

## Server Modes

The Discord MCP Server supports dual transport modes for maximum flexibility:

### SSE Mode (Local HTTP Server)

Run the server as a local HTTP server that you can connect to directly:

```bash
# Start local server
python discord_server.py --transport sse --port 8000

# Server will be available at:
# http://localhost:8000/sse
# Health check: http://localhost:8000/health
```

**Benefits of SSE Mode:**
- ✅ Runs independently as a local service
- ✅ Can be accessed by multiple clients simultaneously
- ✅ Easier debugging and development
- ✅ Direct HTTP API access
- ✅ Built-in health check endpoint
- ✅ Real-time server monitoring

### stdio Mode (MCP Client Integration)

Run the server for integration with MCP clients (Claude Desktop, Amazon Q, etc.):

```bash
# For MCP client integration
python discord_server.py --transport stdio
```

**Benefits of stdio Mode:**
- ✅ Standard MCP client integration
- ✅ Managed lifecycle by MCP client
- ✅ Automatic process management
- ✅ Secure subprocess communication
- ✅ Built-in error handling and recovery

### Command Line Options

```bash
python discord_server.py --help

Options:
  --transport {stdio,sse}    Transport protocol (default: stdio)
  --host HOST               Host for SSE mode (default: 127.0.0.1)
  --port PORT               Port for SSE mode (default: 8000)
  --mount-path PATH         Mount path for SSE (default: /sse)
  --log-level LEVEL         Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  --log-format FORMAT       Log format: text or json (default: text)

Examples:
  # Run with stdio transport (for MCP clients)
  python discord_server.py --transport stdio
  
  # Run with SSE transport (local HTTP server)
  python discord_server.py --transport sse --host 0.0.0.0 --port 8000
  
  # Run with debug logging
  python discord_server.py --log-level DEBUG --transport sse
```

## MCP Integration

### Development and Testing

Test the server with MCP development tools:

```bash
# Test with MCP dev tools
mcp dev mcp_server.py

# Run integration tests
python test_mcp_integration.py

# Test local server functionality
python test_local_server.py
```

### Amazon Q CLI Integration

For Amazon Q CLI integration, add to your MCP configuration:

```json
{
  "mcpServers": {
    "discord-server": {
      "command": "/path/to/Discord-MCP/venv/bin/python",
      "args": ["-m", "discord_mcp.cli", "--transport", "stdio"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_discord_bot_token_here",
        "DISCORD_APPLICATION_ID": "your_discord_application_id_here",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "/path/to/Discord-MCP/src"
      }
    }
  }
}
```

### Claude Desktop Integration

For Claude Desktop, add to your configuration file:

```json
{
  "mcpServers": {
    "discord-server": {
      "command": "python",
      "args": ["/path/to/Discord-MCP/discord_server.py", "--transport", "stdio"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_discord_bot_token_here",
        "DISCORD_APPLICATION_ID": "your_discord_application_id_here",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Discord Bot Setup

### 1. Create Discord Application
- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Click "New Application" and give it a name
- Note the **Application ID** (you'll need this)

### 2. Create Bot User
- Go to the "Bot" section
- Click "Add Bot"
- Copy the **Bot Token** (keep this secure!)
- Enable necessary **Privileged Gateway Intents** if needed

### 3. Configure Bot Permissions
Required permissions for full functionality:
- **View Channels** - To see channels in servers
- **Send Messages** - To send messages via MCP tools
- **Read Message History** - To read messages via MCP resources
- **Manage Messages** - To delete/edit messages (optional)
- **Use Slash Commands** - For future slash command support (optional)

### 4. Invite Bot to Server
- Go to "OAuth2" > "URL Generator"
- Select "bot" scope
- Select required permissions
- Use generated URL to invite bot to your Discord server

### 5. Get Bot Invite URL
Replace `YOUR_CLIENT_ID` with your Discord Application ID:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=3072&scope=bot
```

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | **Yes** | Discord bot token (min 50 chars) | - |
| `DISCORD_APPLICATION_ID` | **Yes** | Discord application ID (min 17 chars) | - |
| `ALLOWED_GUILDS` | No | Comma-separated list of allowed guild IDs | All |
| `ALLOWED_CHANNELS` | No | Comma-separated list of allowed channel IDs | All |
| `RATE_LIMIT_REQUESTS_PER_SECOND` | No | API rate limiting | 5 |
| `RATE_LIMIT_BURST_SIZE` | No | Rate limit burst size | 10 |
| `LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `LOG_FORMAT` | No | Log format (text, json) | text |
| `SERVER_NAME` | No | Custom server name | Discord MCP Server |
| `DEBUG` | No | Enable debug mode | false |
| `DEVELOPMENT_MODE` | No | Enable development features | false |

### Security Considerations

- **🔒 Token Security**: Never commit your bot token to version control
- **🛡️ Guild Restrictions**: Use `ALLOWED_GUILDS` to restrict server access
- **⚡ Rate Limiting**: Configured to respect Discord API limits automatically
- **🔐 Permissions**: Bot only accesses channels it has permissions for
- **📝 Audit Logging**: All actions are logged for security monitoring

## API Reference

### Resources

| Resource | URI Pattern | Description |
|----------|-------------|-------------|
| Guild Listing | `guilds://` | List all accessible Discord servers |
| Channel Listing | `channels://{guild_id}` | List channels in a specific server |
| Message Reading | `messages://{channel_id}` | Read messages from a channel |
| User Information | `user://{user_id}` | Get user profile information |
| Health Check | `health://status` | Server status and configuration |

### Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `send_message` | `channel_id`, `content`, `reply_to_message_id?` | Send message to channel |
| `send_dm` | `user_id`, `content` | Send direct message to user |
| `read_direct_messages` | `user_id`, `limit?` | Read DM conversation |
| `delete_message` | `channel_id`, `message_id` | Delete a message |
| `edit_message` | `channel_id`, `message_id`, `new_content` | Edit a message |

## Usage Examples

### Reading Messages
```python
# Through MCP client - get recent messages from a channel
messages = await client.read_resource("messages://123456789012345678")

# Get user information
user_info = await client.read_resource("user://987654321098765432")

# List servers the bot has access to
guilds = await client.read_resource("guilds://")
```

### Sending Messages
```python
# Send a message to a channel
result = await client.call_tool("send_message", {
    "channel_id": "123456789012345678",
    "content": "Hello from AI assistant! 👋"
})

# Reply to a specific message
result = await client.call_tool("send_message", {
    "channel_id": "123456789012345678",
    "content": "This is a reply!",
    "reply_to_message_id": "111111111111111111"
})
```

### Direct Messages
```python
# Send a direct message
result = await client.call_tool("send_dm", {
    "user_id": "123456789012345678",
    "content": "Private message from AI assistant"
})

# Read DM conversation
conversation = await client.call_tool("read_direct_messages", {
    "user_id": "123456789012345678",
    "limit": 10
})
```

### Message Management
```python
# Delete a message (requires permissions)
result = await client.call_tool("delete_message", {
    "channel_id": "123456789012345678",
    "message_id": "111111111111111111"
})

# Edit a message (bot's own messages only)
result = await client.call_tool("edit_message", {
    "channel_id": "123456789012345678",
    "message_id": "222222222222222222",
    "new_content": "Updated message content"
})
```

## Development

### Project Structure
```
Discord-MCP/
├── src/discord_mcp/          # Main package
│   ├── __init__.py
│   ├── __main__.py           # Module entry point
│   ├── cli.py                # Command line interface
│   ├── config.py             # Configuration management
│   ├── discord_client.py     # Discord API client
│   ├── resources.py          # MCP resources
│   ├── server.py             # Main server implementation
│   └── tools.py              # MCP tools
├── tests/                    # Test suite
├── discord_server.py         # Standalone server entry point
├── mcp_server.py            # MCP dev compatible entry point
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/discord_mcp

# Run integration tests
python test_mcp_integration.py

# Test local server functionality
python test_local_server.py
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Adding New Features
1. **Resources**: Add to `src/discord_mcp/resources.py`
2. **Tools**: Add to `src/discord_mcp/tools.py`
3. **Configuration**: Update `src/discord_mcp/config.py`
4. **Tests**: Add corresponding tests in `tests/`

## Troubleshooting

### Common Issues

#### 1. Bot Token Issues
**Symptoms**: Authentication errors, "Invalid Bot Token"
**Solutions**:
- Verify token format (should be ~70 characters)
- Check token in Discord Developer Portal
- Ensure token starts with correct prefix
- Regenerate token if compromised

#### 2. Permission Issues
**Symptoms**: "Missing Permissions", "Forbidden" errors
**Solutions**:
- Check bot permissions in Discord server settings
- Verify bot has required permissions for the action
- Re-invite bot with correct permissions
- Check channel-specific permission overrides

#### 3. MCP Integration Issues
**Symptoms**: "Still loading", connection timeouts
**Solutions**:
- Verify environment variables are set correctly
- Check MCP configuration file syntax
- Test server startup manually
- Review logs for specific error messages

#### 4. Rate Limiting
**Symptoms**: Slow responses, "Rate Limited" errors
**Solutions**:
- Reduce request frequency
- Adjust `RATE_LIMIT_REQUESTS_PER_SECOND` setting
- Implement request batching
- Monitor Discord API rate limits

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export LOG_FORMAT=json

# Run with debug output
python discord_server.py --transport sse --log-level DEBUG 2>&1 | tee debug.log
```

### Health Monitoring

Check server health:
```bash
# For SSE mode
curl http://localhost:8000/health

# Check MCP resources
python -c "
import asyncio
from mcp.client.session import ClientSession
# ... health check code
"
```

## Performance

### Benchmarks
- **Message Reading**: ~100ms average response time
- **Message Sending**: ~200ms average response time
- **Rate Limiting**: 5 requests/second (configurable)
- **Memory Usage**: ~50MB baseline
- **Concurrent Connections**: Supports multiple MCP clients

### Optimization Tips
- Use pagination for large message sets
- Implement caching for frequently accessed data
- Monitor rate limits to avoid API blocks
- Use appropriate log levels in production

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with proper documentation
4. **Add tests** for new functionality
5. **Run the test suite** (`pytest tests/`)
6. **Check code quality** (`black`, `isort`, `mypy`)
7. **Submit a pull request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/Discord-MCP.git
cd Discord-MCP

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run tests
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Resources

- **📚 Documentation**: [MCP Specification](https://modelcontextprotocol.io)
- **🔧 Discord API**: [Discord Developer Documentation](https://discord.com/developers/docs)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **📖 Examples**: See [EXAMPLES.md](EXAMPLES.md) for detailed usage examples
- **🔍 Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

## Changelog

### v0.2.0 (Latest)
- ✅ Added `read_direct_messages` tool for bidirectional DM support
- ✅ Implemented dual transport support (stdio + SSE)
- ✅ Added comprehensive command line interface
- ✅ Enhanced error handling and logging
- ✅ Added health check endpoint
- ✅ Improved documentation and examples
- ✅ Added comprehensive test suite

### v0.1.0 (Initial Release)
- ✅ Basic MCP server implementation
- ✅ Discord API integration
- ✅ Channel and message operations
- ✅ Direct message support
- ✅ Amazon Q CLI integration

---

**Built with ❤️ for the MCP community**
