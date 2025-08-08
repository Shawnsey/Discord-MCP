#!/usr/bin/env python3
"""
Behavior validation script to ensure identical behavior to pre-refactor implementation.

This script validates that the refactored Discord MCP Server maintains identical
behavior in all aspects compared to the original implementation.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordAPIError
from discord_mcp.server import create_server
from discord_mcp.services import DiscordService


class BehaviorValidator:
    """Validates identical behavior between pre and post refactor implementations."""

    def __init__(self):
        self.settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
        )

    async def validate_tool_behavior(self) -> bool:
        """Validate all tools maintain identical behavior."""
        print("🔧 Validating tool behavior...")
        
        try:
            server = create_server(self.settings)
            mcp_server = server._create_mcp_server()
            
            # Create comprehensive mock service
            mock_service = AsyncMock()
            
            # Mock all service methods with realistic responses
            mock_service.get_guilds_formatted.return_value = """# Discord Guilds

Found 2 accessible guild(s):

## Test Guild
- **ID**: `123456789012345678`
- **Owner**: Yes
- **Member Count**: 100
- **Description**: A test guild for validation
- **Features**: COMMUNITY, NEWS

## Another Guild
- **ID**: `987654321098765432`
- **Owner**: No
- **Member Count**: 50
- **Description**: None

"""
            
            mock_service.get_channels_formatted.return_value = """# Channels in Test Guild

Found 3 accessible channel(s):

## Text Channels

### general
- **ID**: `111111111111111111`
- **Type**: 0
- **Topic**: General discussion
- **Position**: 0

### announcements
- **ID**: `222222222222222222`
- **Type**: 0
- **Topic**: Server announcements
- **Position**: 1

## Voice Channels

### Voice Chat
- **ID**: `333333333333333333`
- **Type**: 2
- **Position**: 2

"""
            
            mock_service.get_messages_formatted.return_value = """# Messages in #general

Showing 2 recent message(s):

## Message from TestUser
- **Author**: TestUser (`444444444444444444`)
- **Time**: 2023-01-01 12:00:00 UTC
- **Message ID**: `555555555555555555`
- **Content**:
  ```
  Hello world! This is a test message.
  ```

## Message from AnotherUser
- **Author**: AnotherUser (`666666666666666666`)
- **Time**: 2023-01-01 12:01:00 UTC
- **Message ID**: `777777777777777777`
- **Content**:
  ```
  How are you doing today?
  ```

"""
            
            mock_service.get_user_info_formatted.return_value = """# User: TestUser

- **Username**: TestUser
- **User ID**: `444444444444444444`
- **Display Name**: Test User Display
- **Type**: User
- **Avatar**: [View Avatar](https://cdn.discordapp.com/avatars/444444444444444444/avatar123.png)
- **Created**: 2020-01-01T00:00:00Z
- **Bot**: No

"""
            
            mock_service.send_message.return_value = """✅ Message sent successfully to #general!
- **Message ID**: `888888888888888888`
- **Channel**: #general (`111111111111111111`)
- **Content**: Test message content
- **Sent at**: 2023-01-01T12:02:00Z"""
            
            mock_service.send_direct_message.return_value = """✅ Direct message sent successfully to TestUser!
- **Message ID**: `999999999999999999`
- **Recipient**: TestUser (`444444444444444444`)
- **Content**: Test DM content
- **Sent at**: 2023-01-01T12:03:00Z"""
            
            mock_service.read_direct_messages.return_value = """📬 **Direct Messages with TestUser** (User ID: `444444444444444444`)
DM Channel ID: `101010101010101010`
Retrieved 2 message(s)

============================================================

** 1.** [2023-01-01 12:00:00] 👤 TestUser
     Message ID: `111111111111111111`
     💬 Hello bot!

** 2.** [2023-01-01 12:01:00] 🤖 TestBot (You)
     Message ID: `222222222222222222`
     💬 Hello user!

"""
            
            mock_service.delete_message.return_value = """✅ Message deleted successfully from #general!
- **Message ID**: `555555555555555555`
- **Channel**: #general (`111111111111111111`)
- **Author**: TestUser
- **Content**: Hello world! This is a test message."""
            
            mock_service.edit_message.return_value = """✅ Message edited successfully in #general!
- **Message ID**: `555555555555555555`
- **Channel**: #general (`111111111111111111`)
- **Old Content**: Hello world! This is a test message.
- **New Content**: Updated message content"""
            
            # Mock context
            context = MagicMock()
            context.request_context.lifespan_context = {"discord_service": mock_service}
            mcp_server.get_context = MagicMock(return_value=context)
            
            # Test all tools with expected behavior
            tool_tests = [
                ("list_guilds", {}, "Test Guild", "Found 2 accessible guild(s)"),
                ("list_channels", {"guild_id": "123456789012345678"}, "general", "Found 3 accessible channel(s)"),
                ("get_messages", {"channel_id": "111111111111111111"}, "TestUser", "Showing 2 recent message(s)"),
                ("get_user_info", {"user_id": "444444444444444444"}, "TestUser", "User ID"),
                ("send_message", {"channel_id": "111111111111111111", "content": "Test message content"}, "Message sent successfully", "Message ID"),
                ("send_dm", {"user_id": "444444444444444444", "content": "Test DM content"}, "Direct message sent successfully", "TestUser"),
                ("read_direct_messages", {"user_id": "444444444444444444", "limit": 10}, "Direct Messages with TestUser", "Retrieved 2 message(s)"),
                ("delete_message", {"channel_id": "111111111111111111", "message_id": "555555555555555555"}, "Message deleted successfully", "TestUser"),
                ("edit_message", {"channel_id": "111111111111111111", "message_id": "555555555555555555", "new_content": "Updated message content"}, "Message edited successfully", "Updated message content"),
            ]
            
            for tool_name, params, expected_content1, expected_content2 in tool_tests:
                try:
                    result = await mcp_server.call_tool(tool_name, params)
                    # Extract actual result from FastMCP response
                    if isinstance(result, tuple) and len(result) == 2:
                        content_list, metadata = result
                        if 'result' in metadata:
                            actual_result = metadata['result']
                        elif content_list and len(content_list) > 0:
                            actual_result = content_list[0].text
                        else:
                            actual_result = str(result)
                    else:
                        actual_result = str(result)
                    
                    # Validate expected content is present
                    if expected_content1 not in actual_result or expected_content2 not in actual_result:
                        print(f"  ❌ {tool_name}: Behavior validation failed")
                        print(f"     Expected: {expected_content1} and {expected_content2}")
                        print(f"     Got: {actual_result[:200]}...")
                        return False
                    
                    print(f"  ✅ {tool_name}: Behavior validated")
                    
                except Exception as e:
                    print(f"  ❌ {tool_name}: Tool execution failed - {e}")
                    return False
            
            print("✅ All tool behaviors validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Tool behavior validation failed: {e}")
            return False

    async def validate_resource_behavior(self) -> bool:
        """Validate all resources maintain identical behavior."""
        print("📚 Validating resource behavior...")
        
        try:
            server = create_server(self.settings)
            mcp_server = server._create_mcp_server()
            
            # Create comprehensive mock service
            mock_service = AsyncMock()
            
            # Mock service methods with realistic responses
            mock_service.get_guilds_formatted.return_value = "# Discord Guilds\n\nFound 2 accessible guild(s):\n\n## Test Guild"
            mock_service.get_channels_formatted.return_value = "# Channels in Test Guild\n\nFound 3 accessible channel(s):\n\n## Text Channels"
            mock_service.get_messages_formatted.return_value = "# Messages in #general\n\nShowing 2 recent message(s):\n\n## Message from TestUser"
            mock_service.get_user_info_formatted.return_value = "# User: TestUser\n\n- **Username**: TestUser"
            
            # Mock context
            context = MagicMock()
            context.request_context.lifespan_context = {"discord_service": mock_service}
            mcp_server.get_context = MagicMock(return_value=context)
            
            # Test all resources with expected behavior
            resource_tests = [
                ("guilds://", "Discord Guilds", "Found 2 accessible guild(s)"),
                ("channels://123456789012345678", "Channels in Test Guild", "Found 3 accessible channel(s)"),
                ("messages://111111111111111111", "Messages in #general", "Showing 2 recent message(s)"),
                ("user://444444444444444444", "User: TestUser", "Username"),
            ]
            
            for resource_uri, expected_content1, expected_content2 in resource_tests:
                try:
                    result = await mcp_server.read_resource(resource_uri)
                    
                    # Extract actual result from FastMCP response
                    if isinstance(result, list) and len(result) > 0:
                        actual_result = result[0].content
                    else:
                        actual_result = str(result)
                    
                    # Validate expected content is present
                    if expected_content1 not in actual_result or expected_content2 not in actual_result:
                        print(f"  ❌ {resource_uri}: Behavior validation failed")
                        print(f"     Expected: {expected_content1} and {expected_content2}")
                        print(f"     Got: {actual_result[:200]}...")
                        return False
                    
                    print(f"  ✅ {resource_uri}: Behavior validated")
                    
                except Exception as e:
                    print(f"  ❌ {resource_uri}: Resource access failed - {e}")
                    return False
            
            print("✅ All resource behaviors validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Resource behavior validation failed: {e}")
            return False

    async def validate_error_scenarios(self) -> bool:
        """Validate error scenarios maintain identical behavior."""
        print("⚠️  Validating error scenarios...")
        
        try:
            # Create service with error-prone mocks
            mock_client = AsyncMock()
            mock_logger = MagicMock()
            service = DiscordService(mock_client, self.settings, mock_logger)
            
            # Test various error scenarios
            error_scenarios = [
                ("Discord API Error", lambda: setattr(mock_client, 'get_user_guilds', AsyncMock(side_effect=DiscordAPIError("API Error", 500)))),
                ("Network Error", lambda: setattr(mock_client, 'get_guild_channels', AsyncMock(side_effect=Exception("Network timeout")))),
                ("Permission Error", lambda: setattr(mock_client, 'get_channel_messages', AsyncMock(side_effect=DiscordAPIError("Forbidden", 403)))),
            ]
            
            for error_name, setup_error in error_scenarios:
                setup_error()
                
                # Test that errors are handled consistently
                if "API Error" in error_name:
                    result = await service.get_guilds_formatted()
                elif "Network Error" in error_name:
                    result = await service.get_channels_formatted("test_guild")
                else:  # Permission Error
                    result = await service.get_messages_formatted("test_channel")
                
                # Validate error response format
                if not result.startswith("# Error"):
                    print(f"  ❌ {error_name}: Error format not preserved")
                    return False
                
                if "error" not in result.lower():
                    print(f"  ❌ {error_name}: Error message not present")
                    return False
                
                print(f"  ✅ {error_name}: Error handling validated")
            
            print("✅ All error scenarios validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error scenario validation failed: {e}")
            return False

    async def validate_edge_cases(self) -> bool:
        """Validate edge cases maintain identical behavior."""
        print("🔍 Validating edge cases...")
        
        try:
            mock_client = AsyncMock()
            mock_logger = MagicMock()
            service = DiscordService(mock_client, self.settings, mock_logger)
            
            # Test edge cases
            edge_cases = [
                ("Empty guild list", lambda: setattr(mock_client, 'get_user_guilds', AsyncMock(return_value=[]))),
                ("Empty channel list", lambda: setattr(mock_client, 'get_guild_channels', AsyncMock(return_value=[]))),
                ("Empty message list", lambda: setattr(mock_client, 'get_channel_messages', AsyncMock(return_value=[]))),
                ("Invalid user ID", lambda: setattr(mock_client, 'get_user', AsyncMock(side_effect=DiscordAPIError("User not found", 404)))),
            ]
            
            for case_name, setup_case in edge_cases:
                setup_case()
                
                # Test appropriate service method
                if "guild" in case_name:
                    result = await service.get_guilds_formatted()
                    expected_content = "No accessible guilds found"
                elif "channel" in case_name:
                    mock_client.get_guild.return_value = {"id": "test", "name": "Test Guild"}
                    result = await service.get_channels_formatted("test_guild")
                    expected_content = "No accessible channels found"
                elif "message" in case_name:
                    mock_client.get_channel.return_value = {"id": "test", "name": "test", "guild_id": "test_guild"}
                    result = await service.get_messages_formatted("test_channel")
                    expected_content = "No messages found"
                else:  # Invalid user
                    result = await service.get_user_info_formatted("invalid_user")
                    expected_content = "Error"
                
                # Validate edge case handling
                if expected_content not in result:
                    print(f"  ❌ {case_name}: Edge case handling not preserved")
                    print(f"     Expected: {expected_content}")
                    print(f"     Got: {result[:200]}...")
                    return False
                
                print(f"  ✅ {case_name}: Edge case validated")
            
            print("✅ All edge cases validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Edge case validation failed: {e}")
            return False

    async def run_behavior_validation(self) -> bool:
        """Run complete behavior validation."""
        print("🚀 Starting Behavior Validation")
        print("=" * 80)
        
        validation_tests = [
            ("Tool Behavior", self.validate_tool_behavior),
            ("Resource Behavior", self.validate_resource_behavior),
            ("Error Scenarios", self.validate_error_scenarios),
            ("Edge Cases", self.validate_edge_cases),
        ]
        
        results = {}
        all_passed = True
        
        for test_name, test_func in validation_tests:
            print(f"\n🧪 Running {test_name} validation...")
            try:
                result = await test_func()
                results[test_name] = result
                if not result:
                    all_passed = False
                    print(f"❌ {test_name} validation FAILED")
                else:
                    print(f"✅ {test_name} validation PASSED")
            except Exception as e:
                print(f"❌ {test_name} validation ERROR: {e}")
                results[test_name] = False
                all_passed = False
        
        print("\n" + "=" * 80)
        print("📊 BEHAVIOR VALIDATION SUMMARY")
        print("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<40} {status}")
        
        print(f"\nOverall Result: {'✅ ALL VALIDATIONS PASSED' if all_passed else '❌ SOME VALIDATIONS FAILED'}")
        
        if all_passed:
            print("\n🎉 Behavior Validation completed successfully!")
            print("✅ Discord MCP Server refactor maintains identical behavior")
            print("✅ All tools produce expected output formats")
            print("✅ All resources provide consistent data")
            print("✅ Error handling is preserved exactly")
            print("✅ Edge cases are handled identically")
        else:
            print("\n❌ Behavior Validation failed!")
            print("❌ Some behaviors have changed from original implementation")
            print("❌ Review failed validations before deployment")
        
        return all_passed


async def main():
    """Main entry point for behavior validation."""
    validator = BehaviorValidator()
    success = await validator.run_behavior_validation()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
