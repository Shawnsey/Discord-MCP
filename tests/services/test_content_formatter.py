"""
Unit tests for ContentFormatter implementation.

This module contains comprehensive unit tests for the ContentFormatter class,
testing all formatting methods with various data scenarios and edge cases.
"""

from unittest.mock import Mock

import pytest

from src.discord_mcp.config import Settings
from src.discord_mcp.services.content_formatter import ContentFormatter


class TestContentFormatter:
    """Test suite for ContentFormatter implementation."""

    @pytest.fixture
    def content_formatter(self):
        """Create a ContentFormatter instance for testing."""
        return ContentFormatter()

    @pytest.fixture
    def content_formatter_with_settings(self, mock_settings):
        """Create a ContentFormatter instance with settings for testing."""
        return ContentFormatter(mock_settings)

    def test_content_formatter_initialization_without_settings(self):
        """Test ContentFormatter initialization without settings."""
        formatter = ContentFormatter()
        assert formatter._settings is None

    def test_content_formatter_initialization_with_settings(self, mock_settings):
        """Test ContentFormatter initialization with settings."""
        formatter = ContentFormatter(mock_settings)
        assert formatter._settings is mock_settings

    # Guild formatting tests
    def test_format_guild_info_with_empty_list(self, content_formatter):
        """Test guild formatting with empty guild list."""
        result = content_formatter.format_guild_info([])
        
        expected = "# Discord Guilds\n\nNo guilds found or bot has no access to any guilds."
        assert result == expected

    def test_format_guild_info_with_single_guild(self, content_formatter):
        """Test guild formatting with single guild data."""
        guilds = [
            {
                "id": "123456789012345678",
                "name": "Test Guild",
                "approximate_member_count": 150,
                "owner": True,
                "permissions": "8",
                "features": ["COMMUNITY", "NEWS"]
            }
        ]
        
        result = content_formatter.format_guild_info(guilds)
        
        assert "# Discord Guilds" in result
        assert "Found 1 guild(s):" in result
        assert "## 1. Test Guild" in result
        assert "**Guild ID**: `123456789012345678`" in result
        assert "**Members**: 150" in result
        assert "**Bot is Owner**: Yes" in result
        assert "**Permissions**: `8`" in result
        assert "**Features**: COMMUNITY, NEWS" in result

    def test_format_guild_info_with_multiple_guilds(self, content_formatter):
        """Test guild formatting with multiple guild data."""
        guilds = [
            {
                "id": "123456789012345678",
                "name": "Test Guild 1",
                "approximate_member_count": 150,
                "owner": True,
                "permissions": "8"
            },
            {
                "id": "987654321098765432",
                "name": "Test Guild 2",
                "approximate_member_count": 300,
                "owner": False,
                "permissions": "104324161"
            }
        ]
        
        result = content_formatter.format_guild_info(guilds)
        
        assert "# Discord Guilds" in result
        assert "Found 2 guild(s):" in result
        assert "## 1. Test Guild 1" in result
        assert "## 2. Test Guild 2" in result
        assert "**Bot is Owner**: Yes" in result
        assert "**Bot is Owner**: No" in result

    def test_format_guild_info_with_missing_fields(self, content_formatter):
        """Test guild formatting handles missing optional fields."""
        guilds = [
            {
                "id": "123456789012345678",
                "name": "Test Guild"
                # Missing approximate_member_count, owner, permissions, features
            }
        ]
        
        result = content_formatter.format_guild_info(guilds)
        
        assert "## 1. Test Guild" in result
        assert "**Guild ID**: `123456789012345678`" in result
        assert "**Members**: Unknown" in result
        assert "**Bot is Owner**: No" in result
        assert "**Permissions**: `0`" in result
        assert "**Features**" not in result

    def test_format_guild_info_with_many_features(self, content_formatter):
        """Test guild formatting with many features (truncation)."""
        guilds = [
            {
                "id": "123456789012345678",
                "name": "Test Guild",
                "features": ["COMMUNITY", "NEWS", "THREADS", "WELCOME_SCREEN", "MEMBER_VERIFICATION", "PREVIEW", "INVITE_SPLASH"]
            }
        ]
        
        result = content_formatter.format_guild_info(guilds)
        
        assert "**Features**: COMMUNITY, NEWS, THREADS, WELCOME_SCREEN, MEMBER_VERIFICATION" in result
        assert "(and 2 more)" in result

    def test_format_guild_info_with_unknown_guild_name(self, content_formatter):
        """Test guild formatting with missing guild name."""
        guilds = [
            {
                "id": "123456789012345678"
                # Missing name field
            }
        ]
        
        result = content_formatter.format_guild_info(guilds)
        
        assert "## 1. Unknown Guild" in result

    # Channel formatting tests
    def test_format_channel_info_with_empty_list(self, content_formatter):
        """Test channel formatting with empty channel list."""
        result = content_formatter.format_channel_info([], "Test Guild")
        
        expected = "# Channels in Test Guild\n\nNo accessible channels found in this guild."
        assert result == expected

    def test_format_channel_info_with_text_channels(self, content_formatter):
        """Test channel formatting with text channels."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "general",
                "type": 0,
                "topic": "General discussion",
                "nsfw": False
            },
            {
                "id": "222222222222222222",
                "name": "random",
                "type": 0,
                "topic": "",
                "nsfw": True
            }
        ]
        
        result = content_formatter.format_channel_info(channels, "Test Guild")
        
        assert "# Channels in Test Guild" in result
        assert "Found 2 channel(s):" in result
        assert "## Text Channels" in result
        assert "**#general** (`111111111111111111`)" in result
        assert "Topic: General discussion" in result
        assert "**#random** (`222222222222222222`)" in result
        assert "🔞 NSFW Channel" in result

    def test_format_channel_info_with_different_channel_types(self, content_formatter):
        """Test channel formatting with different channel types."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "general",
                "type": 0,  # Text channel
                "topic": "General discussion"
            },
            {
                "id": "222222222222222222",
                "name": "voice-chat",
                "type": 2  # Voice channel
            },
            {
                "id": "333333333333333333",
                "name": "announcements",
                "type": 5,  # Announcement channel
                "topic": "Important updates"
            },
            {
                "id": "444444444444444444",
                "name": "General Category",
                "type": 4  # Category
            }
        ]
        
        result = content_formatter.format_channel_info(channels, "Test Guild")
        
        assert "## Text Channels" in result
        assert "## Voice Channels" in result
        assert "## Announcement Channels" in result
        assert "## Categories" in result
        assert "**#general**" in result
        assert "**#voice-chat**" in result
        assert "**#announcements**" in result
        assert "**#General Category**" in result

    def test_format_channel_info_with_long_topic(self, content_formatter):
        """Test channel formatting with long topic that needs truncation."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "general",
                "type": 0,
                "topic": "This is a very long channel topic that should be truncated because it exceeds the maximum length limit for display purposes in the formatted output"
            }
        ]
        
        result = content_formatter.format_channel_info(channels, "Test Guild")
        
        # The actual truncation includes "length ..." not "maximum..."
        assert "Topic: This is a very long channel topic that should be truncated because it exceeds the maximum length ..." in result

    def test_format_channel_info_with_missing_fields(self, content_formatter):
        """Test channel formatting handles missing optional fields."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "general"
                # Missing type, topic, nsfw
            }
        ]
        
        result = content_formatter.format_channel_info(channels, "Test Guild")
        
        # Missing type defaults to 0 (text channel), so it goes under Text Channels
        assert "## Text Channels" in result
        assert "**#general** (`111111111111111111`)" in result
        assert "Topic:" not in result
        assert "🔞 NSFW Channel" not in result

    def test_format_channel_info_with_unknown_channel_type(self, content_formatter):
        """Test channel formatting with unknown channel type."""
        channels = [
            {
                "id": "111111111111111111",
                "name": "unknown-channel",
                "type": 99  # Unknown type
            }
        ]
        
        result = content_formatter.format_channel_info(channels, "Test Guild")
        
        assert "## Other Channels" in result
        assert "**#unknown-channel**" in result

    # Message formatting tests
    def test_format_message_info_with_empty_list(self, content_formatter):
        """Test message formatting with empty message list."""
        result = content_formatter.format_message_info([], "general")
        
        expected = "# Messages in #general\n\nNo messages found in this channel."
        assert result == expected

    def test_format_message_info_with_basic_messages(self, content_formatter):
        """Test message formatting with basic message data."""
        messages = [
            {
                "id": "msg1",
                "content": "Hello, world!",
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:00:00Z"
            },
            {
                "id": "msg2",
                "content": "How are you doing?",
                "author": {
                    "id": "user2",
                    "username": "testuser2",
                    "discriminator": "0"
                },
                "timestamp": "2023-01-01T12:01:00Z"
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        assert "# Messages in #general" in result
        assert "Retrieved 2 message(s):" in result
        assert "** 1.** [2023-01-01 12:00:00 UTC] testuser1#1234" in result
        assert "Message ID: `msg1`" in result
        assert "💬 Hello, world!" in result
        assert "** 2.** [2023-01-01 12:01:00 UTC] @testuser2" in result
        assert "Message ID: `msg2`" in result
        assert "💬 How are you doing?" in result

    def test_format_message_info_with_attachments_and_embeds(self, content_formatter):
        """Test message formatting with messages containing attachments and embeds."""
        messages = [
            {
                "id": "msg1",
                "content": "Check out this image!",
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [
                    {"filename": "image.png", "url": "https://example.com/image.png"}
                ],
                "embeds": [
                    {"title": "Test Embed", "description": "This is a test embed"}
                ],
                "reactions": [
                    {"emoji": {"name": "👍"}, "count": 5}
                ]
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        assert "💬 Check out this image!" in result
        assert "📎 1 embed(s)" in result
        assert "📁 1 attachment(s)" in result
        assert "⭐ 1 reaction(s)" in result

    def test_format_message_info_with_no_text_content(self, content_formatter):
        """Test message formatting with messages that have no text content."""
        messages = [
            {
                "id": "msg1",
                "content": "",
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [
                    {"filename": "image.png", "url": "https://example.com/image.png"}
                ]
            },
            {
                "id": "msg2",
                "author": {
                    "id": "user2",
                    "username": "testuser2",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:01:00Z"
                # Missing content field entirely
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        # Both messages should show "(no text content)"
        assert result.count("💬 (no text content)") == 2

    def test_format_message_info_with_long_content(self, content_formatter):
        """Test message formatting with long content that needs truncation."""
        long_content = "This is a very long message content that should be truncated because it exceeds the maximum length limit for display purposes in the formatted output. " * 10
        
        messages = [
            {
                "id": "msg1",
                "content": long_content,
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:00:00Z"
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        # Content should be truncated with ellipsis
        assert "..." in result
        # Should not contain the full long content
        assert len(result.split("💬 ")[1].split("\n")[0]) <= 503  # 500 + "💬 "

    def test_format_message_info_with_missing_author(self, content_formatter):
        """Test message formatting handles missing author information."""
        messages = [
            {
                "id": "msg1",
                "content": "Hello, world!",
                "timestamp": "2023-01-01T12:00:00Z"
                # Missing author field
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        # Should handle missing author gracefully
        assert "Unknown User" in result or "@Unknown User" in result

    def test_format_message_info_with_missing_timestamp(self, content_formatter):
        """Test message formatting handles missing timestamp."""
        messages = [
            {
                "id": "msg1",
                "content": "Hello, world!",
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                }
                # Missing timestamp field
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        # Should handle missing timestamp gracefully
        assert "Unknown time" in result

    def test_format_message_info_with_multiple_attachments_and_embeds(self, content_formatter):
        """Test message formatting with multiple attachments and embeds."""
        messages = [
            {
                "id": "msg1",
                "content": "Multiple files!",
                "author": {
                    "id": "user1",
                    "username": "testuser1",
                    "discriminator": "1234"
                },
                "timestamp": "2023-01-01T12:00:00Z",
                "attachments": [
                    {"filename": "image1.png"},
                    {"filename": "image2.png"},
                    {"filename": "document.pdf"}
                ],
                "embeds": [
                    {"title": "Embed 1"},
                    {"title": "Embed 2"}
                ],
                "reactions": [
                    {"emoji": {"name": "👍"}, "count": 5},
                    {"emoji": {"name": "❤️"}, "count": 3},
                    {"emoji": {"name": "😂"}, "count": 1}
                ]
            }
        ]
        
        result = content_formatter.format_message_info(messages, "general")
        
        assert "📎 2 embed(s)" in result
        assert "📁 3 attachment(s)" in result
        assert "⭐ 3 reaction(s)" in result

    # User formatting tests
    def test_format_user_info_with_complete_data(self, content_formatter):
        """Test user info formatting with complete user data."""
        user = {
            "id": "123456789012345678",
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User",
            "bot": False,
            "system": False,
            "verified": True,
            "avatar": "abc123def456"
        }
        
        result = content_formatter.format_user_info(user)
        
        assert "# User Information: Test User (testuser#1234)" in result
        assert "**User ID**: `123456789012345678`" in result
        assert "**Username**: testuser" in result
        assert "**Discriminator**: #1234" in result
        assert "**Display Name**: Test User" in result
        assert "**Bot Account**: No" in result
        assert "**Verified**: Yes" in result
        assert "**Has Avatar**: Yes" in result
        assert "**Account Created**:" in result

    def test_format_user_info_with_new_username_system(self, content_formatter):
        """Test user info formatting with new Discord username system (no discriminator)."""
        user = {
            "id": "123456789012345678",
            "username": "testuser",
            "discriminator": "0",
            "global_name": "Test User",
            "bot": False
        }
        
        result = content_formatter.format_user_info(user)
        
        assert "# User Information: Test User (@testuser)" in result
        assert "**Username**: testuser" in result
        assert "**Discriminator**: #" not in result  # Should not show discriminator for new system
        assert "**Display Name**: Test User" in result

    def test_format_user_info_with_bot_account(self, content_formatter):
        """Test user info formatting with bot account."""
        user = {
            "id": "123456789012345678",
            "username": "botuser",
            "discriminator": "0000",
            "bot": True,
            "system": False
        }
        
        result = content_formatter.format_user_info(user)
        
        assert "**Bot Account**: Yes" in result
        assert "**System Account**:" not in result  # Should not show system status if False

    def test_format_user_info_with_system_account(self, content_formatter):
        """Test user info formatting with system account."""
        user = {
            "id": "123456789012345678",
            "username": "systemuser",
            "discriminator": "0000",
            "bot": False,
            "system": True
        }
        
        result = content_formatter.format_user_info(user)
        
        assert "**System Account**: Yes" in result

    def test_format_user_info_with_missing_fields(self, content_formatter):
        """Test user info formatting handles missing optional fields."""
        user = {
            "id": "123456789012345678"
            # Missing username, discriminator, global_name, etc.
        }
        
        result = content_formatter.format_user_info(user)
        
        assert "# User Information: @Unknown User" in result
        assert "**User ID**: `123456789012345678`" in result
        assert "**Username**: Unknown User" in result
        assert "**Bot Account**: No" in result

    def test_format_user_info_with_external_user_id(self, content_formatter):
        """Test user info formatting with external user_id parameter."""
        user = {
            "username": "testuser",
            "discriminator": "1234"
            # Missing id field
        }
        
        result = content_formatter.format_user_info(user, user_id="987654321098765432")
        
        assert "**User ID**: `987654321098765432`" in result

    def test_format_user_info_with_invalid_user_id_for_timestamp(self, content_formatter):
        """Test user info formatting with invalid user ID that can't be used for timestamp calculation."""
        user = {
            "id": "invalid_id",
            "username": "testuser",
            "discriminator": "1234"
        }
        
        result = content_formatter.format_user_info(user)
        
        # Should not crash and should not include account creation date
        assert "**User ID**: `invalid_id`" in result
        assert "**Account Created**:" not in result

    def test_format_user_info_with_same_username_and_global_name(self, content_formatter):
        """Test user info formatting when global_name is same as username."""
        user = {
            "id": "123456789012345678",
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "testuser"  # Same as username
        }
        
        result = content_formatter.format_user_info(user)
        
        # Should not show separate display name if it's the same as username
        assert "**Display Name**: testuser" not in result

    def test_format_user_display_name_legacy_system_with_global_name(self, content_formatter):
        """Test user display name formatting with legacy system and global name."""
        user = {
            "username": "testuser",
            "discriminator": "1234",
            "global_name": "Test User"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "Test User (testuser#1234)"

    def test_format_user_display_name_legacy_system_without_global_name(self, content_formatter):
        """Test user display name formatting with legacy system without global name."""
        user = {
            "username": "testuser",
            "discriminator": "1234"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "testuser#1234"

    def test_format_user_display_name_new_system_with_global_name(self, content_formatter):
        """Test user display name formatting with new system and global name."""
        user = {
            "username": "testuser",
            "discriminator": "0",
            "global_name": "Test User"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "Test User (@testuser)"

    def test_format_user_display_name_new_system_without_global_name(self, content_formatter):
        """Test user display name formatting with new system without global name."""
        user = {
            "username": "testuser",
            "discriminator": "0"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "@testuser"

    def test_format_user_display_name_new_system_with_0000_discriminator(self, content_formatter):
        """Test user display name formatting with 0000 discriminator (also new system)."""
        user = {
            "username": "testuser",
            "discriminator": "0000",
            "global_name": "Test User"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "Test User (@testuser)"

    def test_format_user_display_name_with_missing_fields(self, content_formatter):
        """Test user display name formatting handles missing fields."""
        user = {}
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "@Unknown User"

    def test_format_user_display_name_with_same_username_and_global_name(self, content_formatter):
        """Test user display name when global_name is same as username."""
        user = {
            "username": "testuser",
            "discriminator": "0",
            "global_name": "testuser"
        }
        
        result = content_formatter.format_user_display_name(user)
        
        assert result == "@testuser"

    # Timestamp formatting tests
    def test_format_timestamp_with_z_suffix(self, content_formatter):
        """Test timestamp formatting with Z suffix (UTC)."""
        timestamp = "2023-01-01T12:00:00Z"
        
        result = content_formatter.format_timestamp(timestamp)
        
        assert result == "2023-01-01 12:00:00 UTC"

    def test_format_timestamp_with_timezone_offset(self, content_formatter):
        """Test timestamp formatting with timezone offset."""
        timestamp = "2023-01-01T12:00:00+00:00"
        
        result = content_formatter.format_timestamp(timestamp)
        
        assert result == "2023-01-01 12:00:00 UTC"

    def test_format_timestamp_with_utc_suffix(self, content_formatter):
        """Test timestamp formatting with UTC suffix."""
        timestamp = "2023-01-01T12:00:00 UTC"
        
        result = content_formatter.format_timestamp(timestamp)
        
        assert result == "2023-01-01 12:00:00 UTC"

    def test_format_timestamp_without_timezone(self, content_formatter):
        """Test timestamp formatting without timezone info (assumes UTC)."""
        timestamp = "2023-01-01T12:00:00"
        
        result = content_formatter.format_timestamp(timestamp)
        
        assert result == "2023-01-01 12:00:00 UTC"

    def test_format_timestamp_with_empty_string(self, content_formatter):
        """Test timestamp formatting with empty string."""
        result = content_formatter.format_timestamp("")
        
        assert result == "Unknown time"

    def test_format_timestamp_with_none(self, content_formatter):
        """Test timestamp formatting with None value."""
        result = content_formatter.format_timestamp(None)
        
        assert result == "Unknown time"

    def test_format_timestamp_with_invalid_format(self, content_formatter):
        """Test timestamp formatting with invalid timestamp format."""
        timestamp = "invalid-timestamp"
        
        result = content_formatter.format_timestamp(timestamp)
        
        # Should return the original timestamp when parsing fails
        assert result == "invalid-timestamp"

    def test_format_timestamp_with_malformed_iso_format(self, content_formatter):
        """Test timestamp formatting with malformed ISO format."""
        timestamp = "2023-13-01T25:00:00Z"  # Invalid month and hour
        
        result = content_formatter.format_timestamp(timestamp)
        
        # Should return the original timestamp when parsing fails
        assert result == "2023-13-01T25:00:00Z"

    def test_format_timestamp_with_partial_iso_format(self, content_formatter):
        """Test timestamp formatting with partial ISO format."""
        timestamp = "2023-01-01"
        
        result = content_formatter.format_timestamp(timestamp)
        
        # Should handle partial format gracefully
        assert "2023-01-01" in result

    # Content truncation tests
    def test_truncate_content_within_limit(self, content_formatter):
        """Test content truncation when content is within limit."""
        content = "This is a short message"
        
        result = content_formatter.truncate_content(content, 100)
        
        assert result == "This is a short message"

    def test_truncate_content_at_exact_limit(self, content_formatter):
        """Test content truncation when content is exactly at limit."""
        content = "A" * 100
        
        result = content_formatter.truncate_content(content, 100)
        
        assert result == "A" * 100
        assert len(result) == 100

    def test_truncate_content_exceeds_limit(self, content_formatter):
        """Test content truncation when content exceeds limit."""
        content = "This is a very long message that should be truncated because it exceeds the limit"
        
        result = content_formatter.truncate_content(content, 50)
        
        assert result.endswith("...")
        assert len(result) == 50
        assert result == "This is a very long message that should be trun..."

    def test_truncate_content_with_default_limit(self, content_formatter):
        """Test content truncation with default limit (100 characters)."""
        content = "A" * 150
        
        result = content_formatter.truncate_content(content)
        
        assert result.endswith("...")
        assert len(result) == 100
        assert result == "A" * 97 + "..."

    def test_truncate_content_with_empty_string(self, content_formatter):
        """Test content truncation with empty string."""
        result = content_formatter.truncate_content("", 50)
        
        assert result == ""

    def test_truncate_content_with_none(self, content_formatter):
        """Test content truncation with None value."""
        result = content_formatter.truncate_content(None, 50)
        
        assert result == ""

    def test_truncate_content_with_whitespace_only(self, content_formatter):
        """Test content truncation with whitespace-only content."""
        content = "   \n\t   "
        
        result = content_formatter.truncate_content(content, 50)
        
        assert result == ""  # Should be empty after stripping

    def test_truncate_content_with_very_small_limit(self, content_formatter):
        """Test content truncation with very small limit."""
        content = "Hello world"
        
        result = content_formatter.truncate_content(content, 3)
        
        assert result == "..."

    def test_truncate_content_with_limit_smaller_than_ellipsis(self, content_formatter):
        """Test content truncation with limit smaller than ellipsis length."""
        content = "Hello world"
        
        result = content_formatter.truncate_content(content, 2)
        
        assert result == "..."

    def test_truncate_content_with_zero_limit(self, content_formatter):
        """Test content truncation with zero limit."""
        content = "Hello world"
        
        result = content_formatter.truncate_content(content, 0)
        
        assert result == "..."

    def test_truncate_content_with_negative_limit(self, content_formatter):
        """Test content truncation with negative limit."""
        content = "Hello world"
        
        result = content_formatter.truncate_content(content, -5)
        
        assert result == "..."

    def test_truncate_content_preserves_leading_content(self, content_formatter):
        """Test that truncation preserves the beginning of the content."""
        content = "The quick brown fox jumps over the lazy dog"
        
        result = content_formatter.truncate_content(content, 20)
        
        assert result == "The quick brown f..."
        assert result.startswith("The quick")

    def test_truncate_content_with_non_string_input(self, content_formatter):
        """Test content truncation with non-string input (should convert to string)."""
        content = 12345
        
        result = content_formatter.truncate_content(content, 3)
        
        assert result == "..."  # "12345" is 5 chars, limit is 3, so truncated

    def test_truncate_content_with_unicode_characters(self, content_formatter):
        """Test content truncation with unicode characters."""
        content = "Hello 🌍 world with émojis and spëcial chars"
        
        result = content_formatter.truncate_content(content, 20)
        
        assert result.endswith("...")
        assert len(result) == 20
        assert "Hello 🌍" in result

    # Error handling and graceful degradation tests
    def test_format_user_info_error_handling_with_malformed_data(self, content_formatter):
        """Test format_user_info handles malformed data gracefully."""
        # Test with various malformed data scenarios
        malformed_users = [
            {"id": None, "username": None},
            {"id": "", "username": ""},
            {"id": 123, "username": 456},  # Non-string values
            {"discriminator": None, "global_name": None}
        ]
        
        for user in malformed_users:
            result = content_formatter.format_user_info(user)
            # Should not crash and should contain basic structure
            assert "# User Information:" in result
            assert "**User ID**:" in result
            assert "**Username**:" in result
            assert "**Bot Account**:" in result

    def test_format_user_display_name_error_handling(self, content_formatter):
        """Test format_user_display_name handles various error scenarios."""
        error_cases = [
            None,  # None input
            {},    # Empty dict
            {"username": None},  # None username
            {"username": "", "discriminator": None},  # Empty/None values
            {"discriminator": "invalid"},  # Invalid discriminator
        ]
        
        for user in error_cases:
            result = content_formatter.format_user_display_name(user)
            # Should not crash and should return a string
            assert isinstance(result, str)
            assert len(result) > 0

    def test_format_timestamp_error_handling_comprehensive(self, content_formatter):
        """Test format_timestamp handles comprehensive error scenarios."""
        error_cases = [
            None,
            "",
            "not-a-timestamp",
            "2023-99-99T99:99:99Z",  # Invalid date components
            "2023-01-01T12:00:00+99:99",  # Invalid timezone
            123456,  # Non-string input
            [],  # Wrong type
            {"timestamp": "2023-01-01T12:00:00Z"},  # Dict instead of string
        ]
        
        for timestamp in error_cases:
            result = content_formatter.format_timestamp(timestamp)
            # Should not crash and should return a string
            assert isinstance(result, str)
            assert len(result) > 0
            # Should either be "Unknown time" or the original value
            assert result == "Unknown time" or result == str(timestamp)

    def test_truncate_content_error_handling_comprehensive(self, content_formatter):
        """Test truncate_content handles comprehensive error scenarios."""
        error_cases = [
            (None, 50),
            ("", 50),
            ("content", None),  # None max_length - should cause TypeError but be handled
            ("content", "invalid"),  # Invalid max_length type
            ([], 50),  # Wrong content type
            ({"content": "test"}, 50),  # Dict content
        ]
        
        for content, max_length in error_cases:
            try:
                result = content_formatter.truncate_content(content, max_length)
                # Should return a string
                assert isinstance(result, str)
            except TypeError:
                # Some cases might raise TypeError for invalid max_length
                # This is acceptable behavior
                pass

    @pytest.fixture
    def mock_settings(self):
        """Create a mock Settings object for testing."""
        return Mock(spec=Settings)