# Discord MCP Server - Usage Examples

This document provides comprehensive examples of how to use the Discord MCP Server with various MCP clients and scenarios.

## Table of Contents

- [Basic Resource Access](#basic-resource-access)
- [Tool Usage Examples](#tool-usage-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)

## Basic Resource Access

### 1. List Available Guilds

```python
# Through MCP client
guilds = await client.read_resource("guilds://")
print(f"Bot has access to {len(guilds)} servers")

# Example response:
# [
#   {
#     "id": "123456789012345678",
#     "name": "My Discord Server",
#     "member_count": 150,
#     "owner": true
#   }
# ]
```

### 2. List Channels in a Guild

```python
# Get channels for a specific guild
guild_id = "123456789012345678"
channels = await client.read_resource(f"channels://{guild_id}")

# Filter text channels only
text_channels = [ch for ch in channels if ch["type"] == "text"]
print(f"Found {len(text_channels)} text channels")

# Example response:
# [
#   {
#     "id": "987654321098765432",
#     "name": "general",
#     "type": "text",
#     "topic": "General discussion",
#     "position": 0
#   }
# ]
```

### 3. Read Messages from a Channel

```python
# Get recent messages from a channel
channel_id = "987654321098765432"
messages = await client.read_resource(f"messages://{channel_id}")

# Process messages
for message in messages:
    print(f"{message['author']['username']}: {message['content']}")

# Example response:
# [
#   {
#     "id": "111111111111111111",
#     "content": "Hello everyone!",
#     "author": {
#       "id": "222222222222222222",
#       "username": "john_doe",
#       "avatar": "avatar_hash"
#     },
#     "timestamp": "2024-01-15T10:30:00Z",
#     "edited_timestamp": null
#   }
# ]
```

### 4. Get User Information

```python
# Get information about a specific user
user_id = "222222222222222222"
user_info = await client.read_resource(f"user://{user_id}")

print(f"User: {user_info['username']}#{user_info['discriminator']}")

# Example response:
# {
#   "id": "222222222222222222",
#   "username": "john_doe",
#   "discriminator": "1234",
#   "avatar": "avatar_hash",
#   "bot": false,
#   "system": false
# }
```

### 4. Using Tools for Read Operations

While resources provide direct access to Discord data, tools can also be used for read operations with additional formatting and processing:

```python
# List all accessible guilds using tool
guilds_info = await client.call_tool("list_guilds", {})
print(guilds_info)  # Returns formatted markdown string

# List channels in a guild using tool  
channels_info = await client.call_tool("list_channels", {
    "guild_id": "123456789012345678"
})
print(channels_info)  # Returns formatted markdown string

# Get messages from a channel using tool
messages_info = await client.call_tool("get_messages", {
    "channel_id": "987654321098765432"
})
print(messages_info)  # Returns formatted markdown string

# Get user information using tool
user_info = await client.call_tool("get_user_info", {
    "user_id": "222222222222222222"
})
print(user_info)  # Returns formatted markdown string
```

**Note**: The difference between resources and tools for read operations:
- **Resources** (`read_resource`) return raw JSON data for programmatic use
- **Tools** (`call_tool`) return formatted markdown strings for display/reporting

## Tool Usage Examples

### 1. Send Message to Channel

```python
# Send a simple message
result = await client.call_tool("send_message", {
    "channel_id": "987654321098765432",
    "content": "Hello from the AI assistant! 👋"
})

print(f"Message sent with ID: {result['message_id']}")

# Send a message with mentions
result = await client.call_tool("send_message", {
    "channel_id": "987654321098765432",
    "content": "Hey <@222222222222222222>, check this out!"
})

# Send a formatted message
result = await client.call_tool("send_message", {
    "channel_id": "987654321098765432",
    "content": "**Important Update**\n\n```python\nprint('Hello, World!')\n```\n\n*This is italic text*"
})
```

### 2. Send Direct Messages

```python
# Send a private message to a user
result = await client.call_tool("send_dm", {
    "user_id": "222222222222222222",
    "content": "Hi! I have some information for you privately."
})

print(f"DM sent successfully: {result['success']}")

# Handle DM failures gracefully
try:
    result = await client.call_tool("send_dm", {
        "user_id": "333333333333333333",
        "content": "Private message"
    })
except Exception as e:
    print(f"Failed to send DM: {e}")
    # User might have DMs disabled
```

### 3. Read Direct Messages

```python
# Read DM conversation with a specific user
result = await client.call_tool("read_direct_messages", {
    "user_id": "222222222222222222",
    "limit": 10
})

print(result)  # Formatted conversation history

# Read recent DMs with limit
result = await client.call_tool("read_direct_messages", {
    "user_id": "222222222222222222", 
    "limit": 5
})
```

### 3. Message Management

```python
# Delete a message (requires permissions)
result = await client.call_tool("delete_message", {
    "channel_id": "987654321098765432",
    "message_id": "111111111111111111"
})

if result["success"]:
    print("Message deleted successfully")

# Edit a message (bot's own messages only)
result = await client.call_tool("edit_message", {
    "channel_id": "987654321098765432",
    "message_id": "444444444444444444",
    "content": "Updated message content"
})
```

### 4. User Moderation

```python
# Timeout a user for 30 minutes
result = await client.call_tool("timeout_user", {
    "guild_id": "123456789012345678",
    "user_id": "222222222222222222",
    "duration_minutes": 30,
    "reason": "Disruptive behavior in chat"
})

print(f"Timeout result: {result}")

# Timeout a user with default duration (10 minutes)
result = await client.call_tool("timeout_user", {
    "guild_id": "123456789012345678",
    "user_id": "222222222222222222",
    "reason": "Spam messages"
})

# Remove timeout from a user
result = await client.call_tool("untimeout_user", {
    "guild_id": "123456789012345678",
    "user_id": "222222222222222222",
    "reason": "Timeout period served, user apologized"
})

# Kick a user from the server
result = await client.call_tool("kick_user", {
    "guild_id": "123456789012345678",
    "user_id": "333333333333333333",
    "reason": "Violation of server rules - first offense"
})

# Ban a user from the server with message deletion
result = await client.call_tool("ban_user", {
    "guild_id": "123456789012345678",
    "user_id": "444444444444444444",
    "reason": "Repeated rule violations and harassment",
    "delete_message_days": 1  # Delete messages from last 1 day
})

# Ban a user without deleting messages
result = await client.call_tool("ban_user", {
    "guild_id": "123456789012345678",
    "user_id": "555555555555555555",
    "reason": "Serious rule violation"
    # delete_message_days defaults to 0 (no deletion)
})
```

## Advanced Scenarios

### 1. Channel Monitoring and Response

```python
async def monitor_channel_and_respond():
    """Monitor a channel for specific keywords and respond."""
    channel_id = "987654321098765432"
    
    # Get recent messages
    messages = await client.read_resource(f"messages://{channel_id}")
    
    # Look for messages containing "help"
    for message in messages:
        if "help" in message["content"].lower():
            # Respond to the user
            response = f"Hi <@{message['author']['id']}>, I saw you need help! How can I assist you?"
            
            await client.call_tool("send_message", {
                "channel_id": channel_id,
                "content": response
            })
            break
```

### 2. Multi-Server Information Gathering

```python
async def gather_server_statistics():
    """Gather statistics across all accessible servers."""
    guilds = await client.read_resource("guilds://")
    
    total_channels = 0
    total_members = 0
    
    for guild in guilds:
        # Get channels for this guild
        channels = await client.read_resource(f"channels://{guild['id']}")
        total_channels += len(channels)
        total_members += guild.get("member_count", 0)
        
        print(f"Server: {guild['name']} - {len(channels)} channels, {guild.get('member_count', 0)} members")
    
    print(f"\nTotal: {len(guilds)} servers, {total_channels} channels, {total_members} members")
```

### 3. Message Analysis and Reporting

```python
async def analyze_channel_activity():
    """Analyze recent activity in a channel."""
    channel_id = "987654321098765432"
    messages = await client.read_resource(f"messages://{channel_id}")
    
    # Analyze message patterns
    user_counts = {}
    total_messages = len(messages)
    
    for message in messages:
        author_id = message["author"]["id"]
        user_counts[author_id] = user_counts.get(author_id, 0) + 1
    
    # Create summary report
    report = f"**Channel Activity Report**\n\n"
    report += f"Total messages analyzed: {total_messages}\n"
    report += f"Unique users: {len(user_counts)}\n\n"
    report += "**Top Contributors:**\n"
    
    # Sort users by message count
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    for user_id, count in sorted_users[:5]:
        # Get user info
        user_info = await client.read_resource(f"user://{user_id}")
        report += f"- {user_info['username']}: {count} messages\n"
    
    # Send report to channel
    await client.call_tool("send_message", {
        "channel_id": channel_id,
        "content": report
    })
```

## Integration Examples

### 1. Claude Desktop Integration

```json
{
  "mcpServers": {
    "discord": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_bot_token_here",
        "DISCORD_APPLICATION_ID": "your_app_id_here",
        "ALLOWED_GUILDS": "123456789012345678,987654321098765432",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 2. Custom MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def discord_bot_interaction():
    """Example of custom MCP client interaction."""
    
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env={
            "DISCORD_BOT_TOKEN": "your_token_here",
            "DISCORD_APPLICATION_ID": "your_app_id_here"
        }
    )
    
    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # List available resources
            resources = await session.list_resources()
            print(f"Available resources: {[r.name for r in resources]}")
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")
            
            # Use the Discord server
            guilds = await session.read_resource("guilds://")
            print(f"Connected to {len(guilds)} Discord servers")
            
            # Send a message
            result = await session.call_tool("send_message", {
                "channel_id": "your_channel_id",
                "content": "Hello from custom MCP client!"
            })
            print(f"Message sent: {result}")

# Run the example
asyncio.run(discord_bot_interaction())
```

### 3. Automated Moderation Bot

```python
async def moderation_bot():
    """Example of automated moderation using Discord MCP."""
    
    # Keywords to monitor
    banned_words = ["spam", "inappropriate", "violation"]
    
    # Get all accessible guilds
    guilds = await client.read_resource("guilds://")
    
    for guild in guilds:
        # Get text channels
        channels = await client.read_resource(f"channels://{guild['id']}")
        text_channels = [ch for ch in channels if ch["type"] == "text"]
        
        for channel in text_channels:
            # Check recent messages
            messages = await client.read_resource(f"messages://{channel['id']}")
            
            for message in messages:
                content = message["content"].lower()
                
                # Check for banned words
                if any(word in content for word in banned_words):
                    # Delete the message
                    await client.call_tool("delete_message", {
                        "channel_id": channel["id"],
                        "message_id": message["id"]
                    })
                    
                    # Send warning to user
                    await client.call_tool("send_dm", {
                        "user_id": message["author"]["id"],
                        "content": "Your message was removed for violating server rules."
                    })
                    
                    print(f"Moderated message from {message['author']['username']}")

async def advanced_moderation_system():
    """Advanced moderation system with escalating punishments."""
    
    # Track user violations (in production, use persistent storage)
    user_violations = {}
    
    # Moderation rules
    rules = {
        "spam": {"timeout": 10, "kick_threshold": 3, "ban_threshold": 5},
        "harassment": {"timeout": 30, "kick_threshold": 2, "ban_threshold": 3},
        "inappropriate": {"timeout": 60, "kick_threshold": 2, "ban_threshold": 4}
    }
    
    guild_id = "123456789012345678"
    
    # Get recent messages from all channels
    channels = await client.read_resource(f"channels://{guild_id}")
    
    for channel in channels:
        if channel["type"] != "text":
            continue
            
        messages = await client.read_resource(f"messages://{channel['id']}")
        
        for message in messages:
            user_id = message["author"]["id"]
            content = message["content"].lower()
            
            # Check for rule violations
            for rule_type, rule_config in rules.items():
                if rule_type in content:
                    # Track violation
                    if user_id not in user_violations:
                        user_violations[user_id] = {}
                    if rule_type not in user_violations[user_id]:
                        user_violations[user_id][rule_type] = 0
                    
                    user_violations[user_id][rule_type] += 1
                    violation_count = user_violations[user_id][rule_type]
                    
                    # Delete the offending message
                    await client.call_tool("delete_message", {
                        "channel_id": channel["id"],
                        "message_id": message["id"]
                    })
                    
                    # Apply escalating punishment
                    if violation_count >= rule_config["ban_threshold"]:
                        # Ban user
                        await client.call_tool("ban_user", {
                            "guild_id": guild_id,
                            "user_id": user_id,
                            "reason": f"Repeated {rule_type} violations ({violation_count} times)",
                            "delete_message_days": 1
                        })
                        print(f"🔨 Banned user {user_id} for repeated {rule_type}")
                        
                    elif violation_count >= rule_config["kick_threshold"]:
                        # Kick user
                        await client.call_tool("kick_user", {
                            "guild_id": guild_id,
                            "user_id": user_id,
                            "reason": f"Multiple {rule_type} violations ({violation_count} times)"
                        })
                        print(f"👢 Kicked user {user_id} for {rule_type}")
                        
                    else:
                        # Timeout user
                        await client.call_tool("timeout_user", {
                            "guild_id": guild_id,
                            "user_id": user_id,
                            "duration_minutes": rule_config["timeout"],
                            "reason": f"{rule_type.title()} violation (warning {violation_count})"
                        })
                        print(f"⏰ Timed out user {user_id} for {rule_config['timeout']} minutes")
                    
                    # Send DM with violation notice
                    await client.call_tool("send_dm", {
                        "user_id": user_id,
                        "content": f"Your message was removed for {rule_type}. "
                                 f"This is violation #{violation_count}. "
                                 f"Please review the server rules."
                    })
                    
                    break  # Only process first rule violation per message

async def moderation_dashboard():
    """Create a moderation dashboard with server statistics."""
    
    guild_id = "123456789012345678"
    
    # Get guild information
    guilds = await client.read_resource("guilds://")
    guild = next((g for g in guilds if g["id"] == guild_id), None)
    
    if not guild:
        print("Guild not found")
        return
    
    # Get channels and recent activity
    channels = await client.read_resource(f"channels://{guild_id}")
    text_channels = [ch for ch in channels if ch["type"] == "text"]
    
    total_messages = 0
    active_users = set()
    
    for channel in text_channels:
        messages = await client.read_resource(f"messages://{channel['id']}")
        total_messages += len(messages)
        
        for message in messages:
            active_users.add(message["author"]["id"])
    
    # Create dashboard report
    dashboard = f"""
**🛡️ Moderation Dashboard - {guild['name']}**

**Server Statistics:**
- Total Members: {guild.get('member_count', 'Unknown')}
- Text Channels: {len(text_channels)}
- Recent Messages: {total_messages}
- Active Users: {len(active_users)}

**Channel Activity:**
"""
    
    for channel in text_channels[:5]:  # Top 5 channels
        messages = await client.read_resource(f"messages://{channel['id']}")
        dashboard += f"- #{channel['name']}: {len(messages)} recent messages\n"
    
    from datetime import datetime
    dashboard += f"\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Send dashboard to a moderation channel
    mod_channel = next((ch for ch in text_channels if "mod" in ch["name"].lower()), text_channels[0])
    
    await client.call_tool("send_message", {
        "channel_id": mod_channel["id"],
        "content": dashboard
    })
    
    print("📊 Moderation dashboard sent")
```

## Error Handling

### 1. Graceful Error Handling

```python
async def robust_discord_interaction():
    """Example with comprehensive error handling."""
    
    try:
        # Try to get guilds
        guilds = await client.read_resource("guilds://")
        
        for guild in guilds:
            try:
                # Try to get channels
                channels = await client.read_resource(f"channels://{guild['id']}")
                
                for channel in channels:
                    try:
                        # Try to send message
                        await client.call_tool("send_message", {
                            "channel_id": channel["id"],
                            "content": "Test message"
                        })
                        print(f"✅ Sent message to {channel['name']}")
                        
                    except Exception as e:
                        print(f"❌ Failed to send to {channel['name']}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Failed to access guild {guild['name']}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Failed to get guilds: {e}")
        return False
    
    return True
```

### 2. Rate Limit Handling

```python
import asyncio

async def rate_limited_operations():
    """Handle rate limits gracefully."""
    
    channels_to_message = ["123", "456", "789"]  # Channel IDs
    
    for i, channel_id in enumerate(channels_to_message):
        try:
            await client.call_tool("send_message", {
                "channel_id": channel_id,
                "content": f"Batch message {i+1}"
            })
            
            # Add delay to respect rate limits
            await asyncio.sleep(1)  # 1 second between messages
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                print("Rate limited, waiting longer...")
                await asyncio.sleep(5)  # Wait 5 seconds
                # Retry the operation
                await client.call_tool("send_message", {
                    "channel_id": channel_id,
                    "content": f"Batch message {i+1} (retry)"
                })
            else:
                print(f"Other error: {e}")
```

### 3. Moderation Error Handling

```python
async def safe_moderation_action(action_type, guild_id, user_id, **kwargs):
    """Safely perform moderation actions with comprehensive error handling."""
    
    try:
        if action_type == "timeout":
            result = await client.call_tool("timeout_user", {
                "guild_id": guild_id,
                "user_id": user_id,
                **kwargs
            })
        elif action_type == "untimeout":
            result = await client.call_tool("untimeout_user", {
                "guild_id": guild_id,
                "user_id": user_id,
                **kwargs
            })
        elif action_type == "kick":
            result = await client.call_tool("kick_user", {
                "guild_id": guild_id,
                "user_id": user_id,
                **kwargs
            })
        elif action_type == "ban":
            result = await client.call_tool("ban_user", {
                "guild_id": guild_id,
                "user_id": user_id,
                **kwargs
            })
        else:
            raise ValueError(f"Unknown action type: {action_type}")
            
        print(f"✅ {action_type.title()} successful: {result}")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "role hierarchy" in error_msg:
            print(f"❌ Cannot {action_type} user: Bot role is not high enough")
        elif "missing permissions" in error_msg:
            print(f"❌ Cannot {action_type} user: Bot lacks required permissions")
        elif "user not found" in error_msg:
            print(f"❌ Cannot {action_type} user: User not found in server")
        elif "already banned" in error_msg:
            print(f"❌ Cannot ban user: User is already banned")
        elif "not timed out" in error_msg:
            print(f"❌ Cannot remove timeout: User is not currently timed out")
        elif "invalid duration" in error_msg:
            print(f"❌ Cannot timeout user: Duration must be between 1 minute and 28 days")
        elif "rate limit" in error_msg:
            print(f"⏳ Rate limited, waiting before retry...")
            await asyncio.sleep(5)
            return await safe_moderation_action(action_type, guild_id, user_id, **kwargs)
        else:
            print(f"❌ Unexpected error during {action_type}: {e}")
        
        return False

# Usage examples
async def moderation_examples():
    """Examples of safe moderation with error handling."""
    
    guild_id = "123456789012345678"
    user_id = "987654321098765432"
    
    # Safe timeout with error handling
    success = await safe_moderation_action(
        "timeout", guild_id, user_id,
        duration_minutes=30,
        reason="Disruptive behavior"
    )
    
    if success:
        print("User timed out successfully")
    else:
        print("Failed to timeout user, trying alternative action...")
        # Maybe just send a warning DM instead
        await client.call_tool("send_dm", {
            "user_id": user_id,
            "content": "Please follow server rules. This is a warning."
        })
    
    # Safe kick with fallback
    success = await safe_moderation_action(
        "kick", guild_id, user_id,
        reason="Rule violation"
    )
    
    if not success:
        print("Kick failed, trying timeout instead...")
        await safe_moderation_action(
            "timeout", guild_id, user_id,
            duration_minutes=60,
            reason="Rule violation - timeout as fallback"
        )

async def validate_moderation_permissions():
    """Check if bot has required permissions before attempting moderation."""
    
    guild_id = "123456789012345678"
    
    try:
        # Try a harmless operation first to check permissions
        guilds = await client.read_resource("guilds://")
        guild = next((g for g in guilds if g["id"] == guild_id), None)
        
        if not guild:
            print("❌ Bot is not in the specified guild")
            return False
        
        # Check if we can access channels (basic permission check)
        channels = await client.read_resource(f"channels://{guild_id}")
        
        if not channels:
            print("❌ Bot cannot access channels in this guild")
            return False
        
        print("✅ Basic permissions validated")
        return True
        
    except Exception as e:
        print(f"❌ Permission validation failed: {e}")
        return False

# Example of permission-aware moderation
async def smart_moderation():
    """Perform moderation with permission awareness."""
    
    guild_id = "123456789012345678"
    user_id = "987654321098765432"
    
    # Validate permissions first
    if not await validate_moderation_permissions():
        print("Cannot proceed with moderation - insufficient permissions")
        return
    
    # Try moderation actions in order of severity
    actions = [
        ("timeout", {"duration_minutes": 10, "reason": "First warning"}),
        ("kick", {"reason": "Continued violations"}),
        ("ban", {"reason": "Severe violations", "delete_message_days": 1})
    ]
    
    for action_type, params in actions:
        success = await safe_moderation_action(action_type, guild_id, user_id, **params)
        if success:
            break
        else:
            print(f"Failed {action_type}, trying next action...")
    else:
        print("All moderation actions failed - manual intervention required")
```

## Best Practices

1. **Always handle exceptions** when making Discord API calls
2. **Respect rate limits** by adding delays between operations
3. **Validate permissions** before attempting operations
4. **Use appropriate message formatting** for better readability
5. **Monitor bot activity** and resource usage
6. **Test with small datasets** before scaling up operations
7. **Keep sensitive information secure** (tokens, user data)
8. **Validate role hierarchy** before moderation actions to avoid failures
9. **Use escalating punishments** (timeout → kick → ban) for repeat offenders
10. **Always provide clear reasons** for moderation actions for audit trails
11. **Test moderation features** in a controlled environment before production
12. **Implement fallback actions** when primary moderation fails due to permissions
13. **Log all moderation actions** for accountability and review

## Performance Tips

1. **Batch operations** when possible to reduce API calls
2. **Cache frequently accessed data** (user info, channel lists)
3. **Use pagination** for large datasets
4. **Implement exponential backoff** for retries
5. **Monitor memory usage** with large message histories
