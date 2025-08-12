"""
Discord API client wrapper.

This module provides an async HTTP client for interacting with the Discord API,
including authentication, rate limiting, and error handling.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
import structlog
from aiohttp import ClientError, ClientSession, ClientTimeout

from .config import Settings

logger = structlog.get_logger(__name__)


class DiscordAPIError(Exception):
    """Base exception for Discord API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimitError(DiscordAPIError):
    """Exception raised when rate limited by Discord API."""

    def __init__(self, retry_after: float, message: str = "Rate limited"):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Simple rate limiter for Discord API requests."""

    def __init__(self, requests_per_second: float, burst_size: int):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token for making a request."""
        async with self._lock:
            now = time.time()
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size, self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return

            # Need to wait
            wait_time = (1 - self.tokens) / self.requests_per_second
            logger.debug("Rate limiting: waiting", wait_time=wait_time)
            await asyncio.sleep(wait_time)
            self.tokens = 0


class DiscordClient:
    """Async Discord API client with rate limiting and error handling."""

    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: Optional[ClientSession] = None
        self.rate_limiter = RateLimiter(
            settings.rate_limit_requests_per_second, settings.rate_limit_burst_size
        )

        # Headers for all requests
        self.headers = {
            "Authorization": f"Bot {settings.discord_bot_token}",
            "Content-Type": "application/json",
            "User-Agent": f"{settings.server_name}/{settings.server_version}",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Initialize the HTTP session."""
        if self.session is None:
            timeout = ClientTimeout(total=30, connect=10)
            self.session = ClientSession(
                timeout=timeout, headers=self.headers, raise_for_status=False
            )
            logger.info("Discord client started")

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Discord client closed")

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an API endpoint."""
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.BASE_URL + endpoint

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response_data = await response.json()
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            response_data = {"message": await response.text()}

        # Handle rate limiting
        if response.status == 429:
            retry_after = float(response.headers.get("Retry-After", 1))
            logger.warning("Rate limited by Discord", retry_after=retry_after)
            raise RateLimitError(retry_after, "Rate limited by Discord API")

        # Handle other client errors
        if 400 <= response.status < 500:
            error_message = response_data.get(
                "message", f"Client error: {response.status}"
            )
            logger.error(
                "Discord API client error",
                status=response.status,
                error=error_message,
                response_data=response_data,
            )
            raise DiscordAPIError(error_message, response.status, response_data)

        # Handle server errors
        if response.status >= 500:
            error_message = f"Discord API server error: {response.status}"
            logger.error("Discord API server error", status=response.status)
            raise DiscordAPIError(error_message, response.status, response_data)

        return response_data

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Make an HTTP request with rate limiting and retries."""
        if not self.session:
            raise RuntimeError(
                "Discord client not started. Use async context manager or call start()."
            )

        url = self._build_url(endpoint)

        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                await self.rate_limiter.acquire()

                # Make request
                kwargs = {"params": params} if params else {}
                if data is not None:
                    kwargs["json"] = data
                if headers:
                    kwargs["headers"] = headers

                logger.debug(
                    "Making Discord API request",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                )

                async with self.session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response)

            except RateLimitError as e:
                if attempt == max_retries:
                    raise
                logger.info(
                    "Rate limited, retrying",
                    retry_after=e.retry_after,
                    attempt=attempt + 1,
                )
                await asyncio.sleep(e.retry_after)

            except (ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries:
                    logger.error("Max retries exceeded", error=str(e))
                    raise DiscordAPIError(
                        f"Network error after {max_retries} retries: {str(e)}"
                    )

                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    "Request failed, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    wait_time=wait_time,
                )
                await asyncio.sleep(wait_time)

        raise DiscordAPIError("Unexpected error in request retry loop")

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params, headers=headers)

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, data=data, headers=headers)

    async def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, data=data, headers=headers)

    async def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", endpoint, data=data, headers=headers)

    async def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint, headers=headers)

    # Discord API specific methods

    async def get_current_user(self) -> Dict[str, Any]:
        """Get information about the current bot user."""
        return await self.get("/users/@me")

    async def get_user_guilds(self) -> List[Dict[str, Any]]:
        """Get guilds the bot is a member of."""
        return await self.get("/users/@me/guilds")

    async def get_guild(self, guild_id: str) -> Dict[str, Any]:
        """Get guild information."""
        return await self.get(f"/guilds/{guild_id}")

    async def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get channels in a guild."""
        return await self.get(f"/guilds/{guild_id}/channels")

    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information."""
        return await self.get(f"/channels/{channel_id}")

    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel."""
        params = {"limit": min(limit, 100)}  # Discord max is 100

        if before:
            params["before"] = before
        elif after:
            params["after"] = after
        elif around:
            params["around"] = around

        return await self.get(f"/channels/{channel_id}/messages", params=params)

    async def get_channel_message(
        self, channel_id: str, message_id: str
    ) -> Dict[str, Any]:
        """Get a specific message."""
        return await self.get(f"/channels/{channel_id}/messages/{message_id}")

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        message_reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a message to a channel."""
        if not content and not embeds:
            raise ValueError("Message must have content or embeds")

        data = {}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if message_reference:
            data["message_reference"] = message_reference

        return await self.post(f"/channels/{channel_id}/messages", data=data)

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        """Delete a message."""
        await self.delete(f"/channels/{channel_id}/messages/{message_id}")

    async def create_dm_channel(self, user_id: str) -> Dict[str, Any]:
        """Create a DM channel with a user."""
        data = {"recipient_id": user_id}
        return await self.post("/users/@me/channels", data=data)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        return await self.get(f"/users/{user_id}")

    async def send_dm(self, user_id: str, content: str) -> Dict[str, Any]:
        """Send a direct message to a user."""
        # First create/get DM channel
        dm_channel = await self.create_dm_channel(user_id)
        channel_id = dm_channel["id"]

        # Send message to DM channel
        return await self.send_message(channel_id, content=content)

    # Moderation API methods

    async def get_guild_member(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get guild member information."""
        return await self.get(f"/guilds/{guild_id}/members/{user_id}")

    async def edit_guild_member(
        self, guild_id: str, user_id: str, reason: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Edit a guild member (used for timeouts and other member modifications)."""
        data = {}
        
        # Add any additional fields from kwargs
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        # Add audit log reason if provided
        headers = {}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        
        return await self.patch(f"/guilds/{guild_id}/members/{user_id}", data=data, headers=headers)

    async def kick_guild_member(
        self, guild_id: str, user_id: str, reason: Optional[str] = None
    ) -> None:
        """Kick a member from a guild."""
        # Add audit log reason if provided
        headers = {}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        
        await self.delete(f"/guilds/{guild_id}/members/{user_id}", headers=headers)

    async def ban_guild_member(
        self, 
        guild_id: str, 
        user_id: str, 
        reason: Optional[str] = None, 
        delete_message_days: int = 0
    ) -> None:
        """Ban a member from a guild with optional message deletion."""
        data = {}
        
        # Add delete_message_days if specified (0-7 days allowed by Discord)
        if delete_message_days > 0:
            data["delete_message_days"] = min(max(delete_message_days, 0), 7)
        
        # Add audit log reason if provided
        headers = {}
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        
        await self.put(f"/guilds/{guild_id}/bans/{user_id}", data=data, headers=headers)
