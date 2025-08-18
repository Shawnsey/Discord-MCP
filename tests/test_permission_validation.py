"""
Unit tests for centralized permission validation system.

This module tests the new centralized permission validation methods
to ensure they provide consistent behavior and eliminate code duplication.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.discord_mcp.services.validation import (
    ValidationMixin,
    ValidationResult,
    ValidationErrorType,
)
from src.discord_mcp.discord_client import DiscordAPIError


class MockDiscordService(ValidationMixin):
    """Mock service class for testing ValidationMixin methods."""
    
    def __init__(self, settings=None, discord_client=None, logger=None):
        if settings is None:
            self._settings = None
        else:
            self._settings = settings or MagicMock()
        self._discord_client = discord_client or AsyncMock()
        self._logger = logger or MagicMock()


class TestValidatePermissions:
    """Test cases for the _validate_permissions method."""
    
    def test_validate_permissions_no_ids_provided(self):
        """Test validation passes when no IDs are provided."""
        service = MockDiscordService()
        result = service._validate_permissions()
        assert result is None
    
    def test_validate_permissions_guild_allowed(self):
        """Test validation passes when guild is allowed."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(guild_id="123456789")
        assert result is None
        settings.is_guild_allowed.assert_called_once_with("123456789")
    
    def test_validate_permissions_guild_denied(self):
        """Test validation fails when guild is not allowed."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = False
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(guild_id="123456789")
        assert result == "❌ Error: Access to guild `123456789` is not permitted."
        settings.is_guild_allowed.assert_called_once_with("123456789")
    
    def test_validate_permissions_channel_allowed(self):
        """Test validation passes when channel is allowed."""
        settings = MagicMock()
        settings.is_channel_allowed.return_value = True
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(channel_id="987654321")
        assert result is None
        settings.is_channel_allowed.assert_called_once_with("987654321")
    
    def test_validate_permissions_channel_denied(self):
        """Test validation fails when channel is not allowed."""
        settings = MagicMock()
        settings.is_channel_allowed.return_value = False
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(channel_id="987654321")
        assert result == "❌ Error: Access to channel `987654321` is not permitted."
        settings.is_channel_allowed.assert_called_once_with("987654321")
    
    def test_validate_permissions_both_allowed(self):
        """Test validation passes when both guild and channel are allowed."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        settings.is_channel_allowed.return_value = True
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(guild_id="123456789", channel_id="987654321")
        assert result is None
        settings.is_guild_allowed.assert_called_once_with("123456789")
        settings.is_channel_allowed.assert_called_once_with("987654321")
    
    def test_validate_permissions_guild_denied_channel_allowed(self):
        """Test validation fails when guild is denied even if channel is allowed."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = False
        settings.is_channel_allowed.return_value = True
        service = MockDiscordService(settings=settings)
        
        result = service._validate_permissions(guild_id="123456789", channel_id="987654321")
        assert result == "❌ Error: Access to guild `123456789` is not permitted."
        settings.is_guild_allowed.assert_called_once_with("123456789")
        # Channel validation should not be called if guild validation fails
        settings.is_channel_allowed.assert_not_called()
    
    def test_validate_permissions_no_settings(self):
        """Test validation fails gracefully when settings are not available."""
        service = MockDiscordService()
        delattr(service, '_settings')  # Remove the settings attribute entirely
        
        result = service._validate_permissions(guild_id="123456789")
        assert result == "❌ Error: Access to guild `123456789` is not permitted."
    
    def test_validate_permissions_none_settings(self):
        """Test validation fails gracefully when settings are None."""
        service = MockDiscordService(settings=None)
        
        result = service._validate_permissions(guild_id="123456789")
        assert result == "❌ Error: Access to guild `123456789` is not permitted."


class TestValidateModerationPermissions:
    """Test cases for the _validate_moderation_permissions method."""
    
    @pytest.mark.asyncio
    async def test_validate_moderation_permissions_success(self):
        """Test successful moderation permission validation."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        
        discord_client = AsyncMock()
        discord_client.get_guild.return_value = {"name": "Test Guild"}
        discord_client.get_user.return_value = {"username": "TestUser"}
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        discord_client.get_guild_roles.return_value = [
            {"id": "role1", "name": "Bot Role", "position": 10},
            {"id": "role2", "name": "User Role", "position": 5}
        ]
        
        service = MockDiscordService(settings=settings, discord_client=discord_client)
        
        result = await service._validate_moderation_permissions("123456789012345678", "987654321012345678")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_moderation_permissions_guild_denied(self):
        """Test moderation permission validation fails when guild access is denied."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = False
        
        service = MockDiscordService(settings=settings)
        
        result = await service._validate_moderation_permissions("123456789012345678", "987654321012345678")
        assert result == "❌ Error: Access to guild `123456789012345678` is not permitted."
    
    @pytest.mark.asyncio
    async def test_validate_moderation_permissions_hierarchy_violation(self):
        """Test moderation permission validation fails due to role hierarchy."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        
        discord_client = AsyncMock()
        discord_client.get_guild.return_value = {"name": "Test Guild"}
        discord_client.get_user.return_value = {"username": "TestUser"}
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        discord_client.get_guild_roles.return_value = [
            {"id": "role1", "name": "Bot Role", "position": 5},   # Lower position
            {"id": "role2", "name": "User Role", "position": 10}  # Higher position
        ]
        
        service = MockDiscordService(settings=settings, discord_client=discord_client)
        
        result = await service._validate_moderation_permissions("123456789012345678", "987654321012345678")
        assert "Cannot moderate `TestUser` due to role hierarchy restrictions" in result
        assert "Bot's highest role**: Bot Role (position 5)" in result
        assert "Target user's highest role**: User Role (position 10)" in result
    
    @pytest.mark.asyncio
    async def test_validate_moderation_permissions_user_not_member(self):
        """Test moderation permission validation fails when user is not a guild member."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        
        discord_client = AsyncMock()
        discord_client.get_guild.return_value = {"name": "Test Guild"}
        discord_client.get_user.return_value = {"username": "TestUser"}
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            DiscordAPIError("Not Found", 404)  # Target member not found
        ]
        
        service = MockDiscordService(settings=settings, discord_client=discord_client)
        
        result = await service._validate_moderation_permissions("123456789012345678", "987654321012345678")
        assert "User `987654321012345678` is not a member of Test Guild" in result
    
    @pytest.mark.asyncio
    async def test_validate_moderation_permissions_no_discord_client(self):
        """Test moderation permission validation handles missing Discord client."""
        settings = MagicMock()
        settings.is_guild_allowed.return_value = True
        
        service = MockDiscordService(settings=settings, discord_client=None)
        delattr(service, '_discord_client')
        
        result = await service._validate_moderation_permissions("123456789012345678", "987654321012345678")
        # Should still pass basic guild validation but skip hierarchy validation
        assert result is None


class TestValidateRoleHierarchy:
    """Test cases for the _validate_role_hierarchy method."""
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_success(self):
        """Test successful role hierarchy validation."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        discord_client.get_guild_roles.return_value = [
            {"id": "role1", "name": "Bot Role", "position": 10},
            {"id": "role2", "name": "User Role", "position": 5}
        ]
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_violation(self):
        """Test role hierarchy validation failure."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        discord_client.get_guild_roles.return_value = [
            {"id": "role1", "name": "Bot Role", "position": 5},   # Lower position
            {"id": "role2", "name": "Admin Role", "position": 10}  # Higher position
        ]
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "Cannot moderate `TestUser` due to role hierarchy restrictions" in result
        assert "Bot's highest role**: Bot Role (position 5)" in result
        assert "Target user's highest role**: Admin Role (position 10)" in result
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_equal_positions(self):
        """Test role hierarchy validation fails when positions are equal."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            {"roles": ["role2"]}   # Target member
        ]
        discord_client.get_guild_roles.return_value = [
            {"id": "role1", "name": "Bot Role", "position": 5},
            {"id": "role2", "name": "User Role", "position": 5}  # Same position
        ]
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "Cannot moderate `TestUser` due to role hierarchy restrictions" in result
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_no_roles(self):
        """Test role hierarchy validation with users having no roles (everyone role)."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": []},  # Bot member with no roles
            {"roles": []}   # Target member with no roles
        ]
        discord_client.get_guild_roles.return_value = []
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "Cannot moderate `TestUser` due to role hierarchy restrictions" in result
        assert "@everyone" in result
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_target_not_member(self):
        """Test role hierarchy validation when target user is not a guild member."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = [
            {"roles": ["role1"]},  # Bot member
            DiscordAPIError("Not Found", 404)  # Target member not found
        ]
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "User `987654321` is not a member of Test Guild" in result
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_no_discord_client(self):
        """Test role hierarchy validation handles missing Discord client."""
        service = MockDiscordService(discord_client=None)
        delattr(service, '_discord_client')
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "Cannot validate role hierarchy - Discord client not available" in result
    
    @pytest.mark.asyncio
    async def test_validate_role_hierarchy_api_error(self):
        """Test role hierarchy validation handles Discord API errors."""
        discord_client = AsyncMock()
        discord_client.get_current_user.return_value = {"id": "bot_id"}
        discord_client.get_guild_member.side_effect = DiscordAPIError("Forbidden", 403)
        
        service = MockDiscordService(discord_client=discord_client)
        
        result = await service._validate_role_hierarchy("123456789", "987654321", "Test Guild", "TestUser")
        assert "Could not validate role hierarchy in Test Guild" in result


class TestPermissionDeniedFormatting:
    """Test cases for consistent permission denied error message formatting."""
    
    def test_create_permission_denied_response(self):
        """Test creation of permission denied responses."""
        service = MockDiscordService()
        
        result = service._create_permission_denied_response("guild", "123456789")
        assert not result.is_valid
        assert result.error_type == ValidationErrorType.PERMISSION_DENIED
        assert "Access to guild `123456789` is not permitted" in result.error_message
        assert result.data["resource_type"] == "guild"
        assert result.data["resource_id"] == "123456789"
    
    def test_create_permission_denied_response_with_additional_info(self):
        """Test creation of permission denied responses with additional information."""
        service = MockDiscordService()
        
        result = service._create_permission_denied_response(
            "channel", "987654321", "Bot lacks required permissions."
        )
        assert not result.is_valid
        assert result.error_type == ValidationErrorType.PERMISSION_DENIED
        assert "Access to channel `987654321` is not permitted" in result.error_message
        assert "Bot lacks required permissions" in result.error_message
    
    def test_create_not_found_response(self):
        """Test creation of not found responses."""
        service = MockDiscordService()
        
        result = service._create_not_found_response("user", "555666777")
        assert not result.is_valid
        assert result.error_type == ValidationErrorType.NOT_FOUND
        assert "User `555666777` was not found or bot has no access" in result.error_message
        assert result.data["resource_type"] == "user"
        assert result.data["resource_id"] == "555666777"


if __name__ == "__main__":
    pytest.main([__file__])