"""
Tests for Discord API client.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError, ClientResponse

from discord_mcp.config import Settings
from discord_mcp.discord_client import (DiscordAPIError, DiscordClient,
                                        RateLimiter, RateLimitError)


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        discord_application_id="123456789012345678",
    )


@pytest.fixture
def discord_client(settings):
    """Create Discord client for testing."""
    return DiscordClient(settings)


class TestRateLimiter:
    """Test rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within the limit."""
        limiter = RateLimiter(requests_per_second=10, burst_size=5)

        # Should allow immediate requests up to burst size
        for _ in range(5):
            await limiter.acquire()  # Should not block

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_exceeded(self):
        """Test that rate limiter blocks when limit is exceeded."""
        limiter = RateLimiter(requests_per_second=1, burst_size=1)

        # First request should be immediate
        await limiter.acquire()

        # Second request should be delayed
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()

        # Should have waited approximately 1 second
        assert end_time - start_time >= 0.9  # Allow some tolerance


class TestDiscordClient:
    """Test Discord client functionality."""

    def test_client_initialization(self, discord_client, settings):
        """Test client initialization."""
        assert discord_client.settings == settings
        assert discord_client.session is None
        assert "Bot " in discord_client.headers["Authorization"]
        assert discord_client.headers["Content-Type"] == "application/json"

    def test_build_url(self, discord_client):
        """Test URL building."""
        url = discord_client._build_url("/users/@me")
        assert url == "https://discord.com/api/v10/users/@me"

        # Test with leading slash
        url = discord_client._build_url("users/@me")
        assert url == "https://discord.com/api/v10/users/@me"

    @pytest.mark.asyncio
    async def test_context_manager(self, discord_client):
        """Test async context manager."""
        async with discord_client as client:
            assert client.session is not None

        # Session should be closed after context
        assert discord_client.session is None

    @pytest.mark.asyncio
    async def test_start_and_close(self, discord_client):
        """Test manual start and close."""
        await discord_client.start()
        assert discord_client.session is not None

        await discord_client.close()
        assert discord_client.session is None

    @pytest.mark.asyncio
    async def test_handle_response_success(self, discord_client):
        """Test successful response handling."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"id": "123", "username": "test"}

        result = await discord_client._handle_response(mock_response)
        assert result == {"id": "123", "username": "test"}

    @pytest.mark.asyncio
    async def test_handle_response_rate_limit(self, discord_client):
        """Test rate limit response handling."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "2.5"}
        mock_response.json.return_value = {"message": "Rate limited"}

        with pytest.raises(RateLimitError) as exc_info:
            await discord_client._handle_response(mock_response)

        assert exc_info.value.retry_after == 2.5

    @pytest.mark.asyncio
    async def test_handle_response_client_error(self, discord_client):
        """Test client error response handling."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json.return_value = {"message": "Not Found"}

        with pytest.raises(DiscordAPIError) as exc_info:
            await discord_client._handle_response(mock_response)

        assert exc_info.value.status_code == 404
        assert "Not Found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_response_server_error(self, discord_client):
        """Test server error response handling."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json.return_value = {"message": "Internal Server Error"}

        with pytest.raises(DiscordAPIError) as exc_info:
            await discord_client._handle_response(mock_response)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_response_invalid_json(self, discord_client):
        """Test response with invalid JSON."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text.return_value = "Invalid response"

        result = await discord_client._handle_response(mock_response)
        assert result == {"message": "Invalid response"}

    @pytest.mark.asyncio
    async def test_request_without_session(self, discord_client):
        """Test making request without starting session."""
        with pytest.raises(RuntimeError, match="Discord client not started"):
            await discord_client._request("GET", "/users/@me")

    @pytest.mark.asyncio
    async def test_get_request(self, discord_client):
        """Test GET request."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"id": "123"}

        # Properly mock the async context manager
        mock_session.request.return_value = mock_response
        discord_client.session = mock_session

        result = await discord_client.get("/users/@me")

        mock_session.request.assert_called_once_with(
            "GET", "https://discord.com/api/v10/users/@me"
        )
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_post_request(self, discord_client):
        """Test POST request."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"id": "456"}

        # Properly mock the async context manager
        mock_session.request.return_value = mock_response
        discord_client.session = mock_session

        data = {"content": "Hello"}
        result = await discord_client.post("/channels/123/messages", data=data)

        mock_session.request.assert_called_once_with(
            "POST", "https://discord.com/api/v10/channels/123/messages", json=data
        )
        assert result == {"id": "456"}

    @pytest.mark.asyncio
    async def test_request_with_params(self, discord_client):
        """Test request with query parameters."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []

        # Properly mock the async context manager
        mock_session.request.return_value = mock_response
        discord_client.session = mock_session

        params = {"limit": 10, "before": "123"}
        result = await discord_client.get("/channels/123/messages", params=params)

        mock_session.request.assert_called_once_with(
            "GET", "https://discord.com/api/v10/channels/123/messages", params=params
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_request_retry_on_rate_limit(self, discord_client):
        """Test request retry on rate limit."""
        mock_session = AsyncMock()

        # First response: rate limited
        rate_limit_response = AsyncMock()
        rate_limit_response.status = 429
        rate_limit_response.headers = {"Retry-After": "0.1"}
        rate_limit_response.json.return_value = {"message": "Rate limited"}

        # Second response: success
        success_response = AsyncMock()
        success_response.status = 200
        success_response.json.return_value = {"id": "123"}

        # Mock the session to return different responses on each call
        mock_session.request.side_effect = [rate_limit_response, success_response]
        discord_client.session = mock_session

        result = await discord_client.get("/users/@me")

        assert mock_session.request.call_count == 2
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_request_max_retries_exceeded(self, discord_client):
        """Test request when max retries are exceeded."""
        mock_session = AsyncMock()

        # Mock the session to always raise ClientError
        async def mock_request(*args, **kwargs):
            raise ClientError("Network error")

        mock_session.request.side_effect = mock_request
        discord_client.session = mock_session

        with pytest.raises(DiscordAPIError, match="Network error after 3 retries"):
            await discord_client._request("GET", "/users/@me", max_retries=3)

        assert mock_session.request.call_count == 4  # Initial + 3 retries


class TestDiscordAPIMethods:
    """Test Discord API specific methods."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, discord_client):
        """Test getting current user."""
        with patch.object(
            discord_client, "get", return_value={"id": "123"}
        ) as mock_get:
            result = await discord_client.get_current_user()
            mock_get.assert_called_once_with("/users/@me")
            assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_get_user_guilds(self, discord_client):
        """Test getting user guilds."""
        with patch.object(
            discord_client, "get", return_value=[{"id": "456"}]
        ) as mock_get:
            result = await discord_client.get_user_guilds()
            mock_get.assert_called_once_with("/users/@me/guilds")
            assert result == [{"id": "456"}]

    @pytest.mark.asyncio
    async def test_get_guild_channels(self, discord_client):
        """Test getting guild channels."""
        with patch.object(
            discord_client, "get", return_value=[{"id": "789"}]
        ) as mock_get:
            result = await discord_client.get_guild_channels("123")
            mock_get.assert_called_once_with("/guilds/123/channels")
            assert result == [{"id": "789"}]

    @pytest.mark.asyncio
    async def test_get_channel_messages(self, discord_client):
        """Test getting channel messages."""
        with patch.object(
            discord_client, "get", return_value=[{"id": "msg1"}]
        ) as mock_get:
            result = await discord_client.get_channel_messages(
                "123", limit=10, before="456"
            )
            mock_get.assert_called_once_with(
                "/channels/123/messages", params={"limit": 10, "before": "456"}
            )
            assert result == [{"id": "msg1"}]

    @pytest.mark.asyncio
    async def test_send_message(self, discord_client):
        """Test sending a message."""
        with patch.object(
            discord_client, "post", return_value={"id": "msg123"}
        ) as mock_post:
            result = await discord_client.send_message("123", content="Hello")
            mock_post.assert_called_once_with(
                "/channels/123/messages", data={"content": "Hello"}
            )
            assert result == {"id": "msg123"}

    @pytest.mark.asyncio
    async def test_send_message_with_embeds(self, discord_client):
        """Test sending a message with embeds."""
        embeds = [{"title": "Test", "description": "Test embed"}]
        with patch.object(
            discord_client, "post", return_value={"id": "msg123"}
        ) as mock_post:
            result = await discord_client.send_message("123", embeds=embeds)
            mock_post.assert_called_once_with(
                "/channels/123/messages", data={"embeds": embeds}
            )
            assert result == {"id": "msg123"}

    @pytest.mark.asyncio
    async def test_send_message_no_content_or_embeds(self, discord_client):
        """Test sending a message without content or embeds."""
        with pytest.raises(ValueError, match="Message must have content or embeds"):
            await discord_client.send_message("123")

    @pytest.mark.asyncio
    async def test_send_dm(self, discord_client):
        """Test sending a direct message."""
        with patch.object(
            discord_client, "create_dm_channel", return_value={"id": "dm123"}
        ) as mock_create_dm:
            with patch.object(
                discord_client, "send_message", return_value={"id": "msg123"}
            ) as mock_send:
                result = await discord_client.send_dm("user123", "Hello")

                mock_create_dm.assert_called_once_with("user123")
                mock_send.assert_called_once_with("dm123", content="Hello")
                assert result == {"id": "msg123"}

    @pytest.mark.asyncio
    async def test_delete_message(self, discord_client):
        """Test deleting a message."""
        with patch.object(discord_client, "delete", return_value={}) as mock_delete:
            await discord_client.delete_message("123", "456")
            mock_delete.assert_called_once_with("/channels/123/messages/456")


class TestDiscordModerationMethods:
    """Test Discord moderation API methods."""

    @pytest.mark.asyncio
    async def test_get_guild_member_success(self, discord_client):
        """Test getting guild member information successfully."""
        expected_member = {
            "user": {"id": "123456789", "username": "testuser"},
            "nick": "TestNick",
            "roles": ["role1", "role2"],
            "joined_at": "2023-01-01T00:00:00.000000+00:00"
        }
        
        with patch.object(
            discord_client, "get", return_value=expected_member
        ) as mock_get:
            result = await discord_client.get_guild_member("guild123", "user456")
            mock_get.assert_called_once_with("/guilds/guild123/members/user456")
            assert result == expected_member

    @pytest.mark.asyncio
    async def test_get_guild_member_not_found(self, discord_client):
        """Test getting guild member when member not found."""
        with patch.object(
            discord_client, "get", side_effect=DiscordAPIError("Unknown Member", 404)
        ) as mock_get:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.get_guild_member("guild123", "user456")
            
            mock_get.assert_called_once_with("/guilds/guild123/members/user456")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_edit_guild_member_timeout_success(self, discord_client):
        """Test editing guild member to apply timeout successfully."""
        timeout_until = "2024-01-15T14:30:00.000000+00:00"
        expected_response = {
            "user": {"id": "123456789", "username": "testuser"},
            "communication_disabled_until": timeout_until
        }
        
        with patch.object(
            discord_client, "patch", return_value=expected_response
        ) as mock_patch:
            result = await discord_client.edit_guild_member(
                "guild123", 
                "user456", 
                reason="Disruptive behavior",
                communication_disabled_until=timeout_until
            )
            
            mock_patch.assert_called_once_with(
                "/guilds/guild123/members/user456",
                data={"communication_disabled_until": timeout_until},
                headers={"X-Audit-Log-Reason": "Disruptive behavior"}
            )
            assert result == expected_response

    @pytest.mark.asyncio
    async def test_edit_guild_member_remove_timeout_success(self, discord_client):
        """Test editing guild member to remove timeout successfully."""
        expected_response = {
            "user": {"id": "123456789", "username": "testuser"},
            "communication_disabled_until": None
        }
        
        with patch.object(
            discord_client, "patch", return_value=expected_response
        ) as mock_patch:
            result = await discord_client.edit_guild_member(
                "guild123", 
                "user456", 
                reason="Timeout removed",
                communication_disabled_until=None
            )
            
            # None values are filtered out by the implementation
            mock_patch.assert_called_once_with(
                "/guilds/guild123/members/user456",
                data={},
                headers={"X-Audit-Log-Reason": "Timeout removed"}
            )
            assert result == expected_response

    @pytest.mark.asyncio
    async def test_edit_guild_member_without_reason(self, discord_client):
        """Test editing guild member without audit log reason."""
        with patch.object(
            discord_client, "patch", return_value={}
        ) as mock_patch:
            await discord_client.edit_guild_member(
                "guild123", 
                "user456", 
                communication_disabled_until=None
            )
            
            # None values are filtered out by the implementation
            mock_patch.assert_called_once_with(
                "/guilds/guild123/members/user456",
                data={},
                headers={}
            )

    @pytest.mark.asyncio
    async def test_edit_guild_member_with_valid_fields(self, discord_client):
        """Test editing guild member with valid non-None fields."""
        with patch.object(
            discord_client, "patch", return_value={}
        ) as mock_patch:
            await discord_client.edit_guild_member(
                "guild123", 
                "user456", 
                reason="Update nickname",
                nick="NewNickname",
                roles=["role1", "role2"]
            )
            
            # Only non-None values should be included
            mock_patch.assert_called_once_with(
                "/guilds/guild123/members/user456",
                data={"nick": "NewNickname", "roles": ["role1", "role2"]},
                headers={"X-Audit-Log-Reason": "Update nickname"}
            )

    @pytest.mark.asyncio
    async def test_edit_guild_member_insufficient_permissions(self, discord_client):
        """Test editing guild member with insufficient permissions."""
        with patch.object(
            discord_client, "patch", side_effect=DiscordAPIError("Missing Permissions", 403)
        ) as mock_patch:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.edit_guild_member(
                    "guild123", 
                    "user456", 
                    communication_disabled_until=None
                )
            
            assert exc_info.value.status_code == 403
            assert "Missing Permissions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_edit_guild_member_rate_limited(self, discord_client):
        """Test editing guild member when rate limited."""
        with patch.object(
            discord_client, "patch", side_effect=RateLimitError(2.5, "Rate limited")
        ) as mock_patch:
            with pytest.raises(RateLimitError) as exc_info:
                await discord_client.edit_guild_member(
                    "guild123", 
                    "user456", 
                    communication_disabled_until=None
                )
            
            assert exc_info.value.retry_after == 2.5

    @pytest.mark.asyncio
    async def test_kick_guild_member_success(self, discord_client):
        """Test kicking guild member successfully."""
        with patch.object(
            discord_client, "delete", return_value={}
        ) as mock_delete:
            await discord_client.kick_guild_member(
                "guild123", 
                "user456", 
                reason="Violation of rules"
            )
            
            mock_delete.assert_called_once_with(
                "/guilds/guild123/members/user456",
                headers={"X-Audit-Log-Reason": "Violation of rules"}
            )

    @pytest.mark.asyncio
    async def test_kick_guild_member_without_reason(self, discord_client):
        """Test kicking guild member without audit log reason."""
        with patch.object(
            discord_client, "delete", return_value={}
        ) as mock_delete:
            await discord_client.kick_guild_member("guild123", "user456")
            
            mock_delete.assert_called_once_with(
                "/guilds/guild123/members/user456",
                headers={}
            )

    @pytest.mark.asyncio
    async def test_kick_guild_member_not_found(self, discord_client):
        """Test kicking guild member when member not found."""
        with patch.object(
            discord_client, "delete", side_effect=DiscordAPIError("Unknown Member", 404)
        ) as mock_delete:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.kick_guild_member("guild123", "user456")
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_kick_guild_member_insufficient_permissions(self, discord_client):
        """Test kicking guild member with insufficient permissions."""
        with patch.object(
            discord_client, "delete", side_effect=DiscordAPIError("Missing Permissions", 403)
        ) as mock_delete:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.kick_guild_member("guild123", "user456")
            
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_kick_guild_member_rate_limited(self, discord_client):
        """Test kicking guild member when rate limited."""
        with patch.object(
            discord_client, "delete", side_effect=RateLimitError(1.5, "Rate limited")
        ) as mock_delete:
            with pytest.raises(RateLimitError) as exc_info:
                await discord_client.kick_guild_member("guild123", "user456")
            
            assert exc_info.value.retry_after == 1.5

    @pytest.mark.asyncio
    async def test_ban_guild_member_success(self, discord_client):
        """Test banning guild member successfully."""
        with patch.object(
            discord_client, "put", return_value={}
        ) as mock_put:
            await discord_client.ban_guild_member(
                "guild123", 
                "user456", 
                reason="Severe rule violation",
                delete_message_days=7
            )
            
            mock_put.assert_called_once_with(
                "/guilds/guild123/bans/user456",
                data={"delete_message_days": 7},
                headers={"X-Audit-Log-Reason": "Severe rule violation"}
            )

    @pytest.mark.asyncio
    async def test_ban_guild_member_without_message_deletion(self, discord_client):
        """Test banning guild member without message deletion."""
        with patch.object(
            discord_client, "put", return_value={}
        ) as mock_put:
            await discord_client.ban_guild_member(
                "guild123", 
                "user456", 
                reason="Rule violation"
            )
            
            mock_put.assert_called_once_with(
                "/guilds/guild123/bans/user456",
                data={},
                headers={"X-Audit-Log-Reason": "Rule violation"}
            )

    @pytest.mark.asyncio
    async def test_ban_guild_member_without_reason(self, discord_client):
        """Test banning guild member without audit log reason."""
        with patch.object(
            discord_client, "put", return_value={}
        ) as mock_put:
            await discord_client.ban_guild_member("guild123", "user456")
            
            mock_put.assert_called_once_with(
                "/guilds/guild123/bans/user456",
                data={},
                headers={}
            )

    @pytest.mark.asyncio
    async def test_ban_guild_member_delete_message_days_clamped(self, discord_client):
        """Test banning guild member with delete_message_days clamped to valid range."""
        with patch.object(
            discord_client, "put", return_value={}
        ) as mock_put:
            # Test upper bound clamping
            await discord_client.ban_guild_member(
                "guild123", 
                "user456", 
                delete_message_days=10  # Should be clamped to 7
            )
            
            mock_put.assert_called_once_with(
                "/guilds/guild123/bans/user456",
                data={"delete_message_days": 7},
                headers={}
            )

    @pytest.mark.asyncio
    async def test_ban_guild_member_delete_message_days_negative(self, discord_client):
        """Test banning guild member with negative delete_message_days (not added to data)."""
        with patch.object(
            discord_client, "put", return_value={}
        ) as mock_put:
            await discord_client.ban_guild_member(
                "guild123", 
                "user456", 
                delete_message_days=-5  # Negative values don't get added to data
            )
            
            # delete_message_days <= 0 are not added to the data
            mock_put.assert_called_once_with(
                "/guilds/guild123/bans/user456",
                data={},
                headers={}
            )

    @pytest.mark.asyncio
    async def test_ban_guild_member_already_banned(self, discord_client):
        """Test banning guild member when already banned."""
        with patch.object(
            discord_client, "put", side_effect=DiscordAPIError("User is already banned", 400)
        ) as mock_put:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.ban_guild_member("guild123", "user456")
            
            assert exc_info.value.status_code == 400
            assert "already banned" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ban_guild_member_insufficient_permissions(self, discord_client):
        """Test banning guild member with insufficient permissions."""
        with patch.object(
            discord_client, "put", side_effect=DiscordAPIError("Missing Permissions", 403)
        ) as mock_put:
            with pytest.raises(DiscordAPIError) as exc_info:
                await discord_client.ban_guild_member("guild123", "user456")
            
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_ban_guild_member_rate_limited(self, discord_client):
        """Test banning guild member when rate limited."""
        with patch.object(
            discord_client, "put", side_effect=RateLimitError(3.0, "Rate limited")
        ) as mock_put:
            with pytest.raises(RateLimitError) as exc_info:
                await discord_client.ban_guild_member("guild123", "user456")
            
            assert exc_info.value.retry_after == 3.0

    @pytest.mark.asyncio
    async def test_moderation_methods_with_rate_limiter_integration(self, discord_client):
        """Test that moderation methods properly integrate with the rate limiter."""
        # Start the client to initialize session
        await discord_client.start()
        
        try:
            # Mock the rate limiter to track calls
            with patch.object(discord_client.rate_limiter, 'acquire', new_callable=AsyncMock) as mock_acquire:
                # Mock the session to avoid actual HTTP requests
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                
                # Properly mock the async context manager
                mock_context_manager = AsyncMock()
                mock_context_manager.__aenter__.return_value = mock_response
                mock_context_manager.__aexit__.return_value = None
                
                with patch.object(discord_client.session, 'request', return_value=mock_context_manager):
                    await discord_client.edit_guild_member("guild123", "user456", communication_disabled_until=None)
                    await discord_client.kick_guild_member("guild123", "user456")
                    await discord_client.ban_guild_member("guild123", "user456")
            
            # Rate limiter should have been called for each request
            assert mock_acquire.call_count == 3
        finally:
            await discord_client.close()
