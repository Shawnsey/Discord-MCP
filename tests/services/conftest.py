"""
Shared test fixtures for Discord MCP Services tests.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import structlog

from src.discord_mcp.config import Settings
from src.discord_mcp.discord_client import DiscordClient


@pytest.fixture
def mock_discord_client():
    """Create a mock Discord client for testing."""
    client = AsyncMock(spec=DiscordClient)
    return client


@pytest.fixture
def mock_settings():
    """Create a mock Settings instance for testing."""
    settings = Mock(spec=Settings)
    settings.get_allowed_guilds_set.return_value = None
    settings.get_allowed_channels_set.return_value = None
    settings.is_guild_allowed.return_value = True
    settings.is_channel_allowed.return_value = True
    return settings


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=structlog.stdlib.BoundLogger)
    return logger


@pytest.fixture
def sample_guild_data():
    """Sample guild data for testing."""
    return [
        {
            "id": "123456789012345678",
            "name": "Test Guild 1",
            "owner": True,
            "permissions": "8",
        },
        {
            "id": "987654321098765432",
            "name": "Test Guild 2",
            "owner": False,
            "permissions": "104324161",
        },
    ]


@pytest.fixture
def sample_guild_details():
    """Sample guild details data for testing."""
    return {
        "id": "123456789012345678",
        "name": "Test Guild 1",
        "approximate_member_count": 150,
        "description": "A test Discord guild",
        "features": ["COMMUNITY", "NEWS"],
    }


@pytest.fixture
def sample_channel_data():
    """Sample channel data for testing."""
    return [
        {
            "id": "111111111111111111",
            "name": "general",
            "type": 0,
            "topic": "General discussion",
            "position": 0,
            "parent_id": None,
            "nsfw": False,
        },
        {
            "id": "222222222222222222",
            "name": "voice-chat",
            "type": 2,
            "position": 1,
            "parent_id": None,
        },
        {
            "id": "333333333333333333",
            "name": "announcements",
            "type": 5,
            "topic": "Important updates",
            "position": 2,
            "parent_id": None,
            "nsfw": False,
        },
    ]


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return [
        {
            "id": "msg1",
            "content": "Hello, world!",
            "author": {"id": "user1", "username": "testuser1"},
            "timestamp": "2023-01-01T12:00:00Z",
            "attachments": [],
            "embeds": [],
        },
        {
            "id": "msg2",
            "content": "How are you doing?",
            "author": {"id": "user2", "username": "testuser2"},
            "timestamp": "2023-01-01T12:01:00Z",
            "attachments": [
                {"filename": "image.png", "url": "https://example.com/image.png"}
            ],
            "embeds": [],
        },
    ]


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "123456789012345678",
        "username": "testuser",
        "discriminator": "1234",
        "global_name": "Test User",
        "bot": False,
        "avatar": "avatar_hash_123",
        "banner": None,
        "accent_color": None,
        "public_flags": 0,
    }


@pytest.fixture
def sample_guild_member_data():
    """Sample guild member data for testing."""
    return {
        "user": {
            "id": "123456789012345678",
            "username": "testuser",
            "global_name": "Test User",
        },
        "roles": ["role1", "role2"],
        "communication_disabled_until": None,
        "joined_at": "2023-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_guild_roles_data():
    """Sample guild roles data for testing."""
    return [
        {
            "id": "role1",
            "name": "Bot Role",
            "position": 5,
            "permissions": "8",
            "color": 0,
            "hoist": False,
            "managed": True,
        },
        {
            "id": "role2",
            "name": "User Role",
            "position": 3,
            "permissions": "104324161",
            "color": 16711680,
            "hoist": False,
            "managed": False,
        },
        {
            "id": "role3",
            "name": "Admin Role",
            "position": 10,
            "permissions": "8",
            "color": 255,
            "hoist": True,
            "managed": False,
        },
    ]


@pytest.fixture
def sample_bot_user_data():
    """Sample bot user data for testing."""
    return {
        "id": "bot_user_id_123",
        "username": "testbot",
        "discriminator": "0000",
        "bot": True,
        "avatar": "bot_avatar_hash",
    }
