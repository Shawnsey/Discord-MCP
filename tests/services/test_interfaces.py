"""
Interface compliance tests for Discord services.

This module tests that the DiscordService properly implements the IDiscordService
interface and that the abstract base class behavior works correctly.
"""

import inspect
from abc import ABC
from typing import get_type_hints

import pytest

from src.discord_mcp.services.discord_service import DiscordService
from src.discord_mcp.services.interfaces import IDiscordService


class TestIDiscordServiceInterface:
    """Test the IDiscordService interface definition."""

    def test_interface_is_abstract_base_class(self):
        """Test that IDiscordService is an abstract base class."""
        assert issubclass(IDiscordService, ABC)
        assert IDiscordService.__abstractmethods__

    def test_interface_has_all_required_methods(self):
        """Test that IDiscordService defines all required abstract methods."""
        expected_methods = {
            "get_guilds_formatted",
            "get_channels_formatted",
            "get_messages_formatted",
            "get_user_info_formatted",
            "send_message",
            "send_direct_message",
            "read_direct_messages",
            "delete_message",
            "edit_message",
            "timeout_user",
            "untimeout_user",
            "kick_user",
            "ban_user",
        }

        abstract_methods = IDiscordService.__abstractmethods__
        assert abstract_methods == expected_methods

    def test_interface_cannot_be_instantiated(self):
        """Test that IDiscordService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IDiscordService()

    def test_interface_method_signatures(self):
        """Test that interface methods have correct signatures."""
        # Test get_guilds_formatted
        sig = inspect.signature(IDiscordService.get_guilds_formatted)
        assert len(sig.parameters) == 1  # self only
        assert sig.return_annotation == str

        # Test get_channels_formatted
        sig = inspect.signature(IDiscordService.get_channels_formatted)
        assert len(sig.parameters) == 2  # self, guild_id
        assert "guild_id" in sig.parameters
        assert sig.parameters["guild_id"].annotation == str
        assert sig.return_annotation == str

        # Test get_messages_formatted
        sig = inspect.signature(IDiscordService.get_messages_formatted)
        assert len(sig.parameters) == 3  # self, channel_id, limit
        assert "channel_id" in sig.parameters
        assert "limit" in sig.parameters
        assert sig.parameters["channel_id"].annotation == str
        assert sig.parameters["limit"].annotation == int
        assert sig.parameters["limit"].default == 50
        assert sig.return_annotation == str

        # Test send_message
        sig = inspect.signature(IDiscordService.send_message)
        assert (
            len(sig.parameters) == 4
        )  # self, channel_id, content, reply_to_message_id
        assert "channel_id" in sig.parameters
        assert "content" in sig.parameters
        assert "reply_to_message_id" in sig.parameters
        assert sig.return_annotation == str

    def test_interface_docstrings(self):
        """Test that interface methods have proper docstrings."""
        assert IDiscordService.get_guilds_formatted.__doc__ is not None
        assert IDiscordService.get_channels_formatted.__doc__ is not None
        assert IDiscordService.get_messages_formatted.__doc__ is not None
        assert IDiscordService.get_user_info_formatted.__doc__ is not None
        assert IDiscordService.send_message.__doc__ is not None
        assert IDiscordService.send_direct_message.__doc__ is not None
        assert IDiscordService.read_direct_messages.__doc__ is not None
        assert IDiscordService.delete_message.__doc__ is not None
        assert IDiscordService.edit_message.__doc__ is not None


class TestDiscordServiceInterfaceCompliance:
    """Test that DiscordService properly implements IDiscordService."""

    @pytest.fixture
    def mock_dependencies(self, mock_discord_client, mock_settings, mock_logger):
        """Provide mock dependencies for DiscordService."""
        return mock_discord_client, mock_settings, mock_logger

    def test_discord_service_implements_interface(self, mock_dependencies):
        """Test that DiscordService implements IDiscordService."""
        discord_client, settings, logger = mock_dependencies
        service = DiscordService(discord_client, settings, logger)

        assert isinstance(service, IDiscordService)
        assert issubclass(DiscordService, IDiscordService)

    def test_discord_service_has_all_interface_methods(self, mock_dependencies):
        """Test that DiscordService implements all interface methods."""
        discord_client, settings, logger = mock_dependencies
        service = DiscordService(discord_client, settings, logger)

        # Check that all abstract methods are implemented
        for method_name in IDiscordService.__abstractmethods__:
            assert hasattr(service, method_name)
            method = getattr(service, method_name)
            assert callable(method)

    def test_discord_service_method_signatures_match_interface(self, mock_dependencies):
        """Test that DiscordService method signatures match the interface."""
        discord_client, settings, logger = mock_dependencies
        service = DiscordService(discord_client, settings, logger)

        for method_name in IDiscordService.__abstractmethods__:
            interface_method = getattr(IDiscordService, method_name)
            service_method = getattr(service, method_name)

            interface_sig = inspect.signature(interface_method)
            service_sig = inspect.signature(service_method)

            # Compare parameter names and types (excluding 'self')
            interface_params = list(interface_sig.parameters.keys())[1:]  # Skip 'self'
            service_params = list(service_sig.parameters.keys())

            assert interface_params == service_params

            # Compare return annotations
            assert interface_sig.return_annotation == service_sig.return_annotation

    def test_discord_service_can_be_instantiated(
        self, mock_discord_client, mock_settings, mock_logger
    ):
        """Test that DiscordService can be instantiated (not abstract)."""
        # Should not raise TypeError about abstract methods
        service = DiscordService(mock_discord_client, mock_settings, mock_logger)
        assert service is not None

    def test_discord_service_method_docstrings(
        self, mock_discord_client, mock_settings, mock_logger
    ):
        """Test that DiscordService methods have docstrings."""
        service = DiscordService(mock_discord_client, mock_settings, mock_logger)

        for method_name in IDiscordService.__abstractmethods__:
            method = getattr(service, method_name)
            assert method.__doc__ is not None
            assert len(method.__doc__.strip()) > 0


class TestAbstractBaseClassBehavior:
    """Test abstract base class behavior and inheritance."""

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """Test that incomplete implementations cannot be instantiated."""

        class IncompleteService(IDiscordService):
            """Incomplete service implementation for testing."""

            async def get_guilds_formatted(self) -> str:
                return "test"

            # Missing other required methods

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteService()

    def test_complete_implementation_can_be_instantiated(
        self, mock_discord_client, mock_settings, mock_logger
    ):
        """Test that complete implementations can be instantiated."""

        class CompleteService(IDiscordService):
            """Complete service implementation for testing."""

            def __init__(self, discord_client, settings, logger):
                pass

            async def get_guilds_formatted(self) -> str:
                return "test"

            async def get_channels_formatted(self, guild_id: str) -> str:
                return "test"

            async def get_messages_formatted(
                self, channel_id: str, limit: int = 50
            ) -> str:
                return "test"

            async def get_user_info_formatted(self, user_id: str) -> str:
                return "test"

            async def send_message(
                self, channel_id: str, content: str, reply_to_message_id=None
            ) -> str:
                return "test"

            async def send_direct_message(self, user_id: str, content: str) -> str:
                return "test"

            async def read_direct_messages(self, user_id: str, limit: int = 10) -> str:
                return "test"

            async def delete_message(self, channel_id: str, message_id: str) -> str:
                return "test"

            async def edit_message(
                self, channel_id: str, message_id: str, new_content: str
            ) -> str:
                return "test"

            async def timeout_user(
                self, guild_id: str, user_id: str, duration_minutes: int, reason=None
            ) -> str:
                return "test"

            async def untimeout_user(
                self, guild_id: str, user_id: str, reason=None
            ) -> str:
                return "test"

            async def kick_user(self, guild_id: str, user_id: str, reason=None) -> str:
                return "test"

            async def ban_user(
                self, guild_id: str, user_id: str, reason=None, delete_message_days=0
            ) -> str:
                return "test"

        # Should not raise TypeError
        service = CompleteService(mock_discord_client, mock_settings, mock_logger)
        assert service is not None
        assert isinstance(service, IDiscordService)

    def test_interface_inheritance_chain(self):
        """Test the inheritance chain of the interface."""
        assert issubclass(IDiscordService, ABC)
        assert issubclass(DiscordService, IDiscordService)
        assert issubclass(DiscordService, ABC)

    def test_method_resolution_order(
        self, mock_discord_client, mock_settings, mock_logger
    ):
        """Test method resolution order for DiscordService."""
        service = DiscordService(mock_discord_client, mock_settings, mock_logger)

        mro = DiscordService.__mro__
        assert IDiscordService in mro
        assert ABC in mro
        assert object in mro
