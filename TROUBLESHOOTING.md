# Discord MCP Server - Troubleshooting Guide

This guide covers common issues and their solutions when using the Discord MCP Server.

## Common Issues

### 1. Bot Token Issues

#### Problem: "Invalid Bot Token" or Authentication Errors
**Symptoms:**
- Server fails to start with authentication errors
- Discord API returns 401 Unauthorized

**Solutions:**
1. **Verify Token Format**
   ```bash
   # Token should start with a specific pattern
   echo $DISCORD_BOT_TOKEN | head -c 10
   # Should show something like "MTIzNDU2Nz"
   ```

2. **Check Token in Discord Developer Portal**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Select your application → Bot section
   - Regenerate token if necessary
   - Copy the new token to your `.env` file

3. **Environment Variable Loading**
   ```bash
   # Test if environment variables are loaded
   python -c "from src.discord_mcp.config import get_settings; print(get_settings().discord_bot_token[:10])"
   ```

### 2. Permission Issues

#### Problem: "Missing Permissions" or "Forbidden" Errors
**Symptoms:**
- Can't read messages from channels
- Can't send messages to channels
- Bot appears offline in Discord

**Solutions:**
1. **Check Bot Permissions in Server**
   - Right-click on your bot in Discord
   - Check "Roles" and ensure it has required permissions
   - Required permissions: Send Messages, Read Message History, View Channels

2. **Verify Bot is in Server**
   ```bash
   # Test guild access
   python -c "
   import asyncio
   from src.discord_mcp.discord_client import DiscordClient
   from src.discord_mcp.config import get_settings
   
   async def test():
       client = DiscordClient(get_settings())
       await client.start()
       guilds = await client.get_guilds()
       print(f'Bot is in {len(guilds)} servers')
       await client.close()
   
   asyncio.run(test())
   "
   ```

3. **Re-invite Bot with Correct Permissions**
   - Go to Discord Developer Portal → OAuth2 → URL Generator
   - Select "bot" scope and required permissions
   - Use generated URL to re-invite bot

### 3. Rate Limiting Issues

#### Problem: "Rate Limited" or Slow Responses
**Symptoms:**
- Server becomes slow or unresponsive
- Discord API returns 429 Too Many Requests

**Solutions:**
1. **Adjust Rate Limiting Settings**
   ```bash
   # In .env file
   RATE_LIMIT_REQUESTS_PER_SECOND=3  # Reduce from default 5
   ```

2. **Check Current Rate Limit Status**
   ```bash
   # Enable debug logging to see rate limit info
   export LOG_LEVEL=DEBUG
   python -m discord_mcp
   ```

3. **Implement Request Batching**
   - Avoid making many rapid requests
   - Use pagination parameters for large data sets

### 4. MCP Integration Issues

#### Problem: MCP Server Won't Start or Connect
**Symptoms:**
- `mcp dev` command fails
- Import errors when starting server
- Connection timeouts

**Solutions:**
1. **Test Server Import**
   ```bash
   python -c "import mcp_server; print('Import successful')"
   ```

2. **Check Dependencies**
   ```bash
   pip install -r requirements.txt
   python -c "import mcp.server.fastmcp; print('MCP available')"
   ```

3. **Test with MCP Dev Tools**
   ```bash
   # Test server startup
   timeout 5s mcp dev mcp_server.py || echo "Server started (timeout reached)"
   ```

4. **Verify Configuration**
   ```bash
   python test_mcp_integration.py
   ```

### 5. Channel/Guild Access Issues

#### Problem: "Channel Not Found" or "Guild Not Found"
**Symptoms:**
- Can't access specific channels or servers
- Empty responses from resources

**Solutions:**
1. **Check Guild/Channel Restrictions**
   ```bash
   # In .env file, verify these settings
   ALLOWED_GUILDS=123456789,987654321  # Optional restriction
   ALLOWED_CHANNELS=111111111,222222222  # Optional restriction
   ```

2. **Verify Channel/Guild IDs**
   ```bash
   # Enable Developer Mode in Discord
   # Right-click channel/server → Copy ID
   ```

3. **Test Channel Access**
   ```python
   # Test script to verify access
   import asyncio
   from src.discord_mcp.discord_client import DiscordClient
   from src.discord_mcp.config import get_settings
   
   async def test_channel(channel_id):
       client = DiscordClient(get_settings())
       await client.start()
       try:
           messages = await client.get_channel_messages(channel_id, limit=1)
           print(f"✅ Can access channel {channel_id}")
       except Exception as e:
           print(f"❌ Cannot access channel {channel_id}: {e}")
       await client.close()
   
   # Replace with your channel ID
   asyncio.run(test_channel("YOUR_CHANNEL_ID"))
   ```

### 6. Environment and Dependencies

#### Problem: Import Errors or Missing Dependencies
**Symptoms:**
- ModuleNotFoundError when starting server
- Version compatibility issues

**Solutions:**
1. **Verify Virtual Environment**
   ```bash
   which python  # Should point to venv/bin/python
   pip list | grep mcp  # Should show mcp package
   ```

2. **Reinstall Dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Check Python Version**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

## Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export PYTHONPATH=/path/to/Discord-MCP

# Run with debug output
python -m discord_mcp 2>&1 | tee debug.log
```

## Performance Monitoring

Monitor server performance:

```bash
# Check memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Monitor Discord API calls
grep -i "discord api" debug.log | wc -l
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - Enable DEBUG logging and review output
2. **Test components individually** - Use the test scripts provided
3. **Verify Discord setup** - Ensure bot permissions and server access
4. **Check MCP compatibility** - Test with `mcp dev` command

## Reporting Issues

When reporting issues, please include:

1. **Environment Information**
   ```bash
   python --version
   pip list | grep -E "(mcp|aiohttp|pydantic)"
   ```

2. **Configuration** (without sensitive tokens)
   ```bash
   env | grep -E "(DISCORD|LOG)" | sed 's/=.*/=***/'
   ```

3. **Error Messages** - Full stack traces and log output
4. **Steps to Reproduce** - Exact commands and actions taken

## Security Notes

- **Never share your bot token** in logs or issue reports
- **Use environment variables** for all sensitive configuration
- **Regularly rotate tokens** if you suspect compromise
- **Monitor bot activity** in Discord's audit logs
