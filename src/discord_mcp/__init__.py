"""
Discord MCP Server

A Model Context Protocol (MCP) server for Discord integration.
Enables AI assistants to interact with Discord servers through reading channels,
sending messages, and managing direct messages.
"""

__version__ = "0.1.0"
__author__ = "Discord MCP Team"
__description__ = "MCP server for Discord integration"

from .server import create_server, main

__all__ = ["create_server", "main"]
