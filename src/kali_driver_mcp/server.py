"""MCP Server for Kali Driver Debugging.

This server provides tools for debugging network card drivers in a Kali Linux VM.
"""

import asyncio
import logging
import sys
import time
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import Config, load_config
from .ssh_manager import SSHManager
from .logging_config import setup_logging, get_tool_logger
from .tools.kernel_info import get_kernel_info
from .tools.file_ops import file_operations
from .tools.code_sync import verify_shared_folder
from .tools.driver_compile import compile_driver
from .tools.driver_load import manage_driver
from .tools.log_viewer import view_logs
from .tools.network_info import get_network_info
from .tools.network_monitor import manage_monitor_mode
from .tools.packet_capture import capture_packets

logger = logging.getLogger(__name__)


class KaliDriverMCPServer:
    """MCP Server for Kali driver debugging."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the server."""
        self.config = load_config(config_path)

        # Setup logging based on configuration
        setup_logging(
            log_level=self.config.logging.level,
            log_file=self.config.logging.file,
            json_format=self.config.logging.json_format,
            enable_console=self.config.logging.enable_console
        )

        self.ssh_manager: Optional[SSHManager] = None
        self.server = Server("kali-driver-mcp")
        self.tool_logger = get_tool_logger() if self.config.logging.log_tools else None

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="kernel_info",
                    description="Get kernel version and configuration information from Kali VM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "detail_level": {
                                "type": "string",
                                "enum": ["basic", "full"],
                                "description": "Level of detail to return",
                                "default": "basic"
                            }
                        }
                    }
                ),
                Tool(
                    name="file_ops",
                    description="List and browse files in the VM shared folder",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["list", "read", "stat", "search"],
                                "description": "Operation to perform",
                                "default": "list"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to file or directory (defaults to shared folder)"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Recursive listing",
                                "default": False
                            },
                            "filter_pattern": {
                                "type": "string",
                                "description": "File pattern filter (e.g., '*.c')"
                            },
                            "search_pattern": {
                                "type": "string",
                                "description": "Pattern for content search (required for search operation)"
                            }
                        },
                        "required": ["operation"]
                    }
                ),
                Tool(
                    name="code_sync",
                    description="Verify shared folder is mounted and accessible in the VM",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="driver_compile",
                    description="Compile kernel driver modules using make",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Specific make target (default: all)"
                            },
                            "clean": {
                                "type": "boolean",
                                "description": "Force clean build",
                                "default": False
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Verbose build output",
                                "default": False
                            },
                            "directory": {
                                "type": "string",
                                "description": "Subdirectory to compile in (relative to vm_path)"
                            }
                        }
                    }
                ),
                Tool(
                    name="driver_load",
                    description="Load, unload, or get info about kernel modules",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["load", "unload", "reload", "info", "list"],
                                "description": "Operation to perform"
                            },
                            "module_name": {
                                "type": "string",
                                "description": "Module name (without .ko extension)"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Module parameters (key=value pairs)",
                                "additionalProperties": {"type": "string"}
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force unload",
                                "default": False
                            }
                        },
                        "required": ["operation"]
                    }
                ),
                Tool(
                    name="log_viewer",
                    description="View kernel and system logs (dmesg, syslog, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "enum": ["dmesg", "syslog", "kern", "journal"],
                                "description": "Log source to view"
                            },
                            "lines": {
                                "type": "integer",
                                "description": "Number of lines to retrieve",
                                "minimum": 1
                            },
                            "filter_pattern": {
                                "type": "string",
                                "description": "Regex pattern to filter logs"
                            },
                            "level": {
                                "type": "string",
                                "enum": ["error", "warn", "info", "debug"],
                                "description": "Log level filter"
                            },
                            "since": {
                                "type": "string",
                                "description": "Time filter (e.g., '5 min ago')"
                            }
                        }
                    }
                ),
                Tool(
                    name="network_info",
                    description="Get network interface information and statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interface": {
                                "type": "string",
                                "description": "Interface name or 'all'",
                                "default": "all"
                            },
                            "detail_level": {
                                "type": "string",
                                "enum": ["basic", "detailed", "statistics"],
                                "description": "Level of detail",
                                "default": "basic"
                            },
                            "info_type": {
                                "type": "string",
                                "enum": ["status", "driver", "settings", "stats"],
                                "description": "Type of information",
                                "default": "status"
                            }
                        }
                    }
                ),
                Tool(
                    name="network_monitor",
                    description="Start/stop wireless monitor mode using airmon-ng",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["start", "stop", "status"],
                                "description": "Operation to perform"
                            },
                            "channel": {
                                "type": "integer",
                                "description": "Channel number (for start operation)",
                                "minimum": 1,
                                "maximum": 165
                            }
                        },
                        "required": ["operation"]
                    }
                ),
                Tool(
                    name="packet_capture",
                    description="Capture wireless packets using airodump-ng",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "integer",
                                "description": "Channel to monitor",
                                "minimum": 1,
                                "maximum": 165
                            },
                            "bssid": {
                                "type": "string",
                                "description": "Specific AP MAC address to capture",
                                "pattern": "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Capture duration in seconds",
                                "minimum": 1,
                                "maximum": 3600
                            },
                            "output_prefix": {
                                "type": "string",
                                "description": "Filename prefix for capture files",
                                "default": "capture"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")

            # Log tool start
            tool_id = None
            if self.tool_logger:
                tool_id = self.tool_logger.log_tool_start(name, arguments or {})

            start_time = time.time()
            success = False

            try:
                # Ensure SSH connection is established
                if not self.ssh_manager:
                    self.ssh_manager = SSHManager(self.config)
                    await self.ssh_manager.connect()

                # Route to appropriate tool
                result = None

                if name == "kernel_info":
                    result = await get_kernel_info(
                        self.config,
                        self.ssh_manager,
                        detail_level=arguments.get("detail_level", "basic")
                    )

                elif name == "file_ops":
                    result = await file_operations(
                        self.config,
                        self.ssh_manager,
                        operation=arguments.get("operation", "list"),
                        path=arguments.get("path"),
                        recursive=arguments.get("recursive", False),
                        filter_pattern=arguments.get("filter_pattern"),
                        search_pattern=arguments.get("search_pattern")
                    )

                elif name == "code_sync":
                    result = await verify_shared_folder(
                        self.config,
                        self.ssh_manager
                    )

                elif name == "driver_compile":
                    result = await compile_driver(
                        self.config,
                        self.ssh_manager,
                        target=arguments.get("target"),
                        clean=arguments.get("clean", False),
                        verbose=arguments.get("verbose", False),
                        directory=arguments.get("directory")
                    )

                elif name == "driver_load":
                    result = await manage_driver(
                        self.config,
                        self.ssh_manager,
                        operation=arguments["operation"],
                        module_name=arguments.get("module_name", ""),
                        parameters=arguments.get("parameters"),
                        force=arguments.get("force", False)
                    )

                elif name == "log_viewer":
                    result = await view_logs(
                        self.config,
                        self.ssh_manager,
                        source=arguments.get("source"),
                        lines=arguments.get("lines"),
                        filter_pattern=arguments.get("filter_pattern"),
                        level=arguments.get("level"),
                        since=arguments.get("since")
                    )

                elif name == "network_info":
                    result = await get_network_info(
                        self.config,
                        self.ssh_manager,
                        interface=arguments.get("interface", "all"),
                        detail_level=arguments.get("detail_level", "basic"),
                        info_type=arguments.get("info_type", "status")
                    )

                elif name == "network_monitor":
                    result = await manage_monitor_mode(
                        self.config,
                        self.ssh_manager,
                        operation=arguments["operation"],
                        channel=arguments.get("channel")
                    )

                elif name == "packet_capture":
                    result = await capture_packets(
                        self.config,
                        self.ssh_manager,
                        channel=arguments.get("channel"),
                        bssid=arguments.get("bssid"),
                        duration=arguments.get("duration"),
                        output_prefix=arguments.get("output_prefix", "capture")
                    )

                else:
                    raise ValueError(f"Unknown tool: {name}")

                # Mark as successful
                success = True
                duration = time.time() - start_time

                # Log tool completion
                if self.tool_logger and tool_id is not None:
                    self.tool_logger.log_tool_end(
                        tool_id=tool_id,
                        tool_name=name,
                        result=result,
                        duration=duration,
                        success=success
                    )

                # Format result as text
                import json
                result_text = json.dumps(result, indent=2, ensure_ascii=False)

                return [TextContent(type="text", text=result_text)]

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)

                # Log tool error
                if self.tool_logger and tool_id is not None:
                    self.tool_logger.log_tool_error(
                        tool_id=tool_id,
                        tool_name=name,
                        error=e
                    )

                error_msg = f"Error executing {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Kali Driver MCP Server...")

        try:
            # Initialize SSH connection
            self.ssh_manager = SSHManager(self.config)
            logger.info(f"Connecting to VM at {self.config.vm.host}:{self.config.vm.port}")

            # Verify shared folder if configured
            if self.config.shared_folder.verify_mount:
                logger.info("Verifying shared folder mount...")
                sync_result = await verify_shared_folder(self.config, self.ssh_manager)
                if sync_result.get("ready"):
                    logger.info(f"Shared folder ready: {sync_result['vm_path']}")
                else:
                    logger.warning(f"Shared folder not ready: {sync_result}")

            # Run the server
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP Server is running. Waiting for requests...")
                await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise
        finally:
            # Clean up
            if self.ssh_manager:
                logger.info("Closing SSH connection...")
                await self.ssh_manager.close()
            logger.info("Server stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Kali Driver MCP Server")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    args = parser.parse_args()

    try:
        server = KaliDriverMCPServer(config_path=args.config)
        asyncio.run(server.run())
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
