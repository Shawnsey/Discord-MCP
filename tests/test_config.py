"""
Tests for configuration management.
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from discord_mcp.config import (
    Settings,
    load_settings
)


class TestSettings:
    """Test main settings class."""
    
    @patch.dict(os.environ, {
        'DISCORD_BOT_TOKEN': 'FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
        'DISCORD_APPLICATION_ID': '123456789012345678',
        'ALLOWED_GUILDS': '111,222,333',
        'LOG_LEVEL': 'DEBUG',
        'DEBUG': 'true'
    })
    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        settings = Settings()
        assert settings.discord_bot_token == 'FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50
        assert settings.discord_application_id == '123456789012345678'
        assert settings.allowed_guilds == '111,222,333'
        assert settings.log_level == 'DEBUG'
        assert settings.debug is True
    
    def test_get_allowed_guilds_list(self):
        """Test getting allowed guilds as list."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678',
            allowed_guilds='111,222,333'
        )
        guilds = settings.get_allowed_guilds_list()
        assert guilds == ['111', '222', '333']
    
    def test_get_allowed_guilds_list_none(self):
        """Test getting allowed guilds when none set."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678'
        )
        guilds = settings.get_allowed_guilds_list()
        assert guilds is None
    
    def test_get_allowed_channels_list(self):
        """Test getting allowed channels as list."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678',
            allowed_channels='111,222,333'
        )
        channels = settings.get_allowed_channels_list()
        assert channels == ['111', '222', '333']
    
    def test_is_guild_allowed_no_restrictions(self):
        """Test guild access with no restrictions."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678'
        )
        assert settings.is_guild_allowed("any_guild_id") is True
    
    def test_is_guild_allowed_with_restrictions(self):
        """Test guild access with restrictions."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678',
            allowed_guilds='123,456'
        )
        assert settings.is_guild_allowed("123") is True
        assert settings.is_guild_allowed("789") is False
    
    def test_is_channel_allowed_no_restrictions(self):
        """Test channel access with no restrictions."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678'
        )
        assert settings.is_channel_allowed("any_channel_id") is True
    
    def test_is_channel_allowed_with_restrictions(self):
        """Test channel access with restrictions."""
        settings = Settings(
            discord_bot_token='FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
            discord_application_id='123456789012345678',
            allowed_channels='111,222'
        )
        assert settings.is_channel_allowed("111") is True
        assert settings.is_channel_allowed("333") is False
    
    def test_invalid_bot_token(self):
        """Test invalid bot token validation."""
        with pytest.raises(ValidationError):
            Settings(
                discord_bot_token="short",  # Too short
                discord_application_id="123456789012345678"
            )
    
    def test_invalid_application_id(self):
        """Test invalid application ID validation."""
        with pytest.raises(ValidationError):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_" + "x" * 50,
                discord_application_id="123"  # Too short
            )
    
    def test_invalid_log_level(self):
        """Test invalid log level validation."""
        with pytest.raises(ValidationError):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_" + "x" * 50,
                discord_application_id="123456789012345678",
                log_level="INVALID"
            )
    
    def test_invalid_log_format(self):
        """Test invalid log format validation."""
        with pytest.raises(ValidationError):
            Settings(
                discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_" + "x" * 50,
                discord_application_id="123456789012345678",
                log_format="invalid"
            )


@patch.dict(os.environ, {
    'DISCORD_BOT_TOKEN': 'FAKE_BOT_TOKEN_FOR_TESTING_' + 'x' * 50,
    'DISCORD_APPLICATION_ID': '123456789012345678'
})
def test_load_settings():
    """Test loading settings function."""
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.discord_bot_token is not None
