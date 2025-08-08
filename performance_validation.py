#!/usr/bin/env python3
"""
Performance validation script for Discord MCP Server refactor.

This script measures response times and memory usage to ensure the service layer
refactor doesn't introduce performance regression.
"""

import asyncio
import gc
import sys
import time
import tracemalloc
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord_mcp.config import Settings
from discord_mcp.discord_client import DiscordClient
from discord_mcp.server import create_server
from discord_mcp.services import DiscordService, IDiscordService


class PerformanceValidator:
    """Performance validation for Discord MCP Server."""

    def __init__(self):
        self.settings = Settings(
            discord_bot_token="FAKE_BOT_TOKEN_FOR_TESTING_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            discord_application_id="123456789012345678",
        )
        self.results = {}

    async def measure_service_instantiation(self) -> Dict[str, float]:
        """Measure service instantiation performance."""
        print("📊 Measuring service instantiation performance...")
        
        # Create mock dependencies
        mock_client = AsyncMock(spec=DiscordClient)
        mock_logger = MagicMock()
        
        # Measure memory before
        tracemalloc.start()
        gc.collect()
        
        # Measure instantiation time
        times = []
        for i in range(100):
            start_time = time.perf_counter()
            service = DiscordService(mock_client, self.settings, mock_logger)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            # Clean up
            del service
            if i % 10 == 0:
                gc.collect()
        
        # Measure memory after
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        avg_time = mean(times)
        std_time = stdev(times) if len(times) > 1 else 0
        
        print(f"✅ Service instantiation: {avg_time:.3f}ms ± {std_time:.3f}ms")
        print(f"✅ Memory usage: {current / 1024 / 1024:.2f}MB current, {peak / 1024 / 1024:.2f}MB peak")
        
        return {
            "avg_time_ms": avg_time,
            "std_time_ms": std_time,
            "memory_current_mb": current / 1024 / 1024,
            "memory_peak_mb": peak / 1024 / 1024,
        }

    async def measure_service_method_performance(self) -> Dict[str, Dict[str, float]]:
        """Measure service method call performance."""
        print("📊 Measuring service method performance...")
        
        # Create service with mocked dependencies
        mock_client = AsyncMock(spec=DiscordClient)
        mock_logger = MagicMock()
        service = DiscordService(mock_client, self.settings, mock_logger)
        
        # Mock Discord API responses
        mock_client.get_user_guilds.return_value = [
            {"id": "guild123", "name": "Test Guild", "owner": True}
        ]
        mock_client.get_guild.return_value = {
            "approximate_member_count": 100,
            "description": "Test guild",
            "features": [],
        }
        mock_client.get_guild_channels.return_value = [
            {"id": "channel123", "name": "general", "type": 0}
        ]
        mock_client.get_channel.return_value = {
            "id": "channel123", 
            "name": "general", 
            "guild_id": "guild123"
        }
        mock_client.get_channel_messages.return_value = [
            {
                "id": "msg123",
                "content": "Hello world",
                "author": {"username": "TestUser", "id": "user123"},
                "timestamp": "2023-01-01T12:00:00Z",
            }
        ]
        mock_client.get_user.return_value = {
            "id": "user123",
            "username": "TestUser",
            "avatar": "avatar123",
        }
        
        # Test methods
        methods_to_test = [
            ("get_guilds_formatted", lambda: service.get_guilds_formatted()),
            ("get_channels_formatted", lambda: service.get_channels_formatted("guild123")),
            ("get_messages_formatted", lambda: service.get_messages_formatted("channel123")),
            ("get_user_info_formatted", lambda: service.get_user_info_formatted("user123")),
        ]
        
        results = {}
        
        for method_name, method_call in methods_to_test:
            print(f"  Testing {method_name}...")
            times = []
            
            # Warm up
            for _ in range(5):
                await method_call()
            
            # Measure performance
            for _ in range(50):
                start_time = time.perf_counter()
                await method_call()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            avg_time = mean(times)
            std_time = stdev(times) if len(times) > 1 else 0
            min_time = min(times)
            max_time = max(times)
            
            results[method_name] = {
                "avg_time_ms": avg_time,
                "std_time_ms": std_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
            }
            
            print(f"    ✅ {method_name}: {avg_time:.3f}ms ± {std_time:.3f}ms (min: {min_time:.3f}ms, max: {max_time:.3f}ms)")
        
        return results

    async def measure_server_startup_time(self) -> Dict[str, float]:
        """Measure server startup time."""
        print("📊 Measuring server startup time...")
        
        times = []
        
        for i in range(10):
            start_time = time.perf_counter()
            
            # Create server (this includes service registration)
            server = create_server(self.settings)
            mcp_server = server._create_mcp_server()
            
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            # Clean up
            del server, mcp_server
            gc.collect()
        
        avg_time = mean(times)
        std_time = stdev(times) if len(times) > 1 else 0
        
        print(f"✅ Server startup: {avg_time:.3f}ms ± {std_time:.3f}ms")
        
        return {
            "avg_time_ms": avg_time,
            "std_time_ms": std_time,
        }

    async def measure_fastmcp_integration_performance(self) -> Dict[str, Dict[str, float]]:
        """Measure FastMCP integration performance."""
        print("📊 Measuring FastMCP integration performance...")
        
        # Create server
        server = create_server(self.settings)
        mcp_server = server._create_mcp_server()
        
        # Mock the service in context
        mock_service = AsyncMock(spec=IDiscordService)
        mock_service.get_guilds_formatted.return_value = "# Discord Guilds\n\nTest response"
        mock_service.get_channels_formatted.return_value = "# Channels\n\nTest response"
        mock_service.get_messages_formatted.return_value = "# Messages\n\nTest response"
        mock_service.get_user_info_formatted.return_value = "# User\n\nTest response"
        
        # Mock context
        context = MagicMock()
        context.request_context.lifespan_context = {"discord_service": mock_service}
        mcp_server.get_context = MagicMock(return_value=context)
        
        # Test tool calls
        tool_tests = [
            ("list_guilds", {}),
            ("list_channels", {"guild_id": "guild123"}),
            ("get_messages", {"channel_id": "channel123"}),
            ("get_user_info", {"user_id": "user123"}),
        ]
        
        results = {}
        
        for tool_name, params in tool_tests:
            print(f"  Testing {tool_name} tool...")
            times = []
            
            # Warm up
            for _ in range(5):
                await mcp_server.call_tool(tool_name, params)
            
            # Measure performance
            for _ in range(30):
                start_time = time.perf_counter()
                await mcp_server.call_tool(tool_name, params)
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            avg_time = mean(times)
            std_time = stdev(times) if len(times) > 1 else 0
            
            results[tool_name] = {
                "avg_time_ms": avg_time,
                "std_time_ms": std_time,
            }
            
            print(f"    ✅ {tool_name}: {avg_time:.3f}ms ± {std_time:.3f}ms")
        
        return results

    def validate_performance_regression(self, results: Dict) -> bool:
        """Validate that performance is within acceptable bounds."""
        print("📊 Validating performance regression...")
        
        # Define acceptable performance thresholds
        thresholds = {
            "service_instantiation_ms": 10.0,  # Service should instantiate in < 10ms
            "service_method_avg_ms": 5.0,      # Service methods should run in < 5ms
            "server_startup_ms": 1000.0,       # Server startup should be < 1s
            "tool_call_avg_ms": 10.0,          # Tool calls should complete in < 10ms
        }
        
        issues = []
        
        # Check service instantiation
        if results["service_instantiation"]["avg_time_ms"] > thresholds["service_instantiation_ms"]:
            issues.append(f"Service instantiation too slow: {results['service_instantiation']['avg_time_ms']:.3f}ms > {thresholds['service_instantiation_ms']}ms")
        
        # Check service methods
        for method_name, method_results in results["service_methods"].items():
            if method_results["avg_time_ms"] > thresholds["service_method_avg_ms"]:
                issues.append(f"{method_name} too slow: {method_results['avg_time_ms']:.3f}ms > {thresholds['service_method_avg_ms']}ms")
        
        # Check server startup
        if results["server_startup"]["avg_time_ms"] > thresholds["server_startup_ms"]:
            issues.append(f"Server startup too slow: {results['server_startup']['avg_time_ms']:.3f}ms > {thresholds['server_startup_ms']}ms")
        
        # Check tool calls
        for tool_name, tool_results in results["fastmcp_integration"].items():
            if tool_results["avg_time_ms"] > thresholds["tool_call_avg_ms"]:
                issues.append(f"{tool_name} tool too slow: {tool_results['avg_time_ms']:.3f}ms > {thresholds['tool_call_avg_ms']}ms")
        
        if issues:
            print("❌ Performance regression detected:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ No performance regression detected - all metrics within acceptable bounds")
            return True

    async def run_validation(self) -> bool:
        """Run complete performance validation."""
        print("🚀 Starting Performance Validation")
        print("=" * 80)
        
        try:
            # Measure service instantiation
            service_instantiation = await self.measure_service_instantiation()
            
            # Measure service method performance
            service_methods = await self.measure_service_method_performance()
            
            # Measure server startup time
            server_startup = await self.measure_server_startup_time()
            
            # Measure FastMCP integration performance
            fastmcp_integration = await self.measure_fastmcp_integration_performance()
            
            # Compile results
            results = {
                "service_instantiation": service_instantiation,
                "service_methods": service_methods,
                "server_startup": server_startup,
                "fastmcp_integration": fastmcp_integration,
            }
            
            # Validate performance
            performance_ok = self.validate_performance_regression(results)
            
            print("\n" + "=" * 80)
            print("📊 PERFORMANCE VALIDATION SUMMARY")
            print("=" * 80)
            
            print(f"Service Instantiation: {service_instantiation['avg_time_ms']:.3f}ms ± {service_instantiation['std_time_ms']:.3f}ms")
            print(f"Memory Usage: {service_instantiation['memory_current_mb']:.2f}MB current, {service_instantiation['memory_peak_mb']:.2f}MB peak")
            print(f"Server Startup: {server_startup['avg_time_ms']:.3f}ms ± {server_startup['std_time_ms']:.3f}ms")
            
            print("\nService Method Performance:")
            for method_name, method_results in service_methods.items():
                print(f"  {method_name}: {method_results['avg_time_ms']:.3f}ms ± {method_results['std_time_ms']:.3f}ms")
            
            print("\nFastMCP Integration Performance:")
            for tool_name, tool_results in fastmcp_integration.items():
                print(f"  {tool_name}: {tool_results['avg_time_ms']:.3f}ms ± {tool_results['std_time_ms']:.3f}ms")
            
            print(f"\nOverall Performance: {'✅ PASSED' if performance_ok else '❌ FAILED'}")
            
            return performance_ok
            
        except Exception as e:
            print(f"❌ Performance validation failed with error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False


async def main():
    """Main entry point for performance validation."""
    validator = PerformanceValidator()
    success = await validator.run_validation()
    
    if success:
        print("\n🎉 Performance validation completed successfully!")
        print("✅ No performance regression detected")
        print("✅ Service layer refactor maintains excellent performance")
        return 0
    else:
        print("\n❌ Performance validation failed!")
        print("❌ Performance regression detected or validation error occurred")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
