"""
Example usage scripts for Kali Driver MCP Server.

These examples demonstrate how to use the MCP server programmatically.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def example_driver_development_workflow():
    """
    Example: Complete driver development workflow.

    This demonstrates a typical workflow:
    1. Verify environment
    2. Compile driver
    3. Load driver
    4. Check logs
    5. Unload driver
    """
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "kali_driver_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=== Driver Development Workflow ===\n")

            # Step 1: Check kernel version
            print("Step 1: Checking kernel version...")
            result = await session.call_tool("kernel_info", {"detail_level": "basic"})
            data = json.loads(result.content[0].text)
            print(f"  Kernel: {data.get('version', 'unknown')}\n")

            # Step 2: Verify shared folder
            print("Step 2: Verifying shared folder...")
            result = await session.call_tool("code_sync", {})
            data = json.loads(result.content[0].text)
            if data.get("ready"):
                print(f"  ✓ Shared folder ready: {data['vm_path']}")
                print(f"  Files: {data['files_count']}\n")
            else:
                print(f"  ✗ Shared folder not ready: {data}\n")
                return

            # Step 3: Compile driver
            print("Step 3: Compiling driver...")
            result = await session.call_tool("driver_compile", {
                "clean": True,
                "verbose": False
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ Compilation successful ({data['duration']}s)")
                print(f"  Artifacts: {data.get('artifacts', [])}\n")
            else:
                print(f"  ✗ Compilation failed: {data.get('error', 'unknown error')}\n")
                return

            # Step 4: Load driver (example - replace with your module name)
            module_name = "mydriver"  # Replace with your actual module name
            print(f"Step 4: Loading driver module '{module_name}'...")
            result = await session.call_tool("driver_load", {
                "operation": "load",
                "module_name": module_name,
                "parameters": {"debug": "1"}
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ {data.get('message', 'Module loaded')}\n")
            else:
                print(f"  ✗ Load failed: {data.get('error', 'unknown error')}\n")

            # Step 5: Check kernel logs
            print("Step 5: Checking kernel logs for driver messages...")
            result = await session.call_tool("log_viewer", {
                "source": "dmesg",
                "lines": 20,
                "filter_pattern": module_name
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                entries = data.get("entries", [])
                print(f"  Found {len(entries)} log entries:")
                for entry in entries[:5]:  # Show first 5
                    print(f"    {entry}")
                print()

            # Step 6: Get module info
            print("Step 6: Getting module information...")
            result = await session.call_tool("driver_load", {
                "operation": "info",
                "module_name": module_name
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  Module loaded: {data.get('loaded', False)}")
                print()

            # Step 7: Unload driver
            print(f"Step 7: Unloading driver '{module_name}'...")
            result = await session.call_tool("driver_load", {
                "operation": "unload",
                "module_name": module_name
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ {data.get('message', 'Module unloaded')}\n")

            print("=== Workflow Complete ===")


async def example_wireless_monitoring():
    """
    Example: Wireless network monitoring and packet capture.

    Demonstrates:
    1. Start monitor mode
    2. Capture packets
    3. Stop monitor mode
    """
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "kali_driver_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=== Wireless Monitoring Workflow ===\n")

            # Step 1: Check network interfaces
            print("Step 1: Checking network interfaces...")
            result = await session.call_tool("network_info", {
                "interface": "all",
                "detail_level": "basic"
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                interfaces = data.get("interfaces", [])
                print(f"  Found interfaces: {', '.join(interfaces)}\n")

            # Step 2: Start monitor mode
            print("Step 2: Starting monitor mode on channel 6...")
            result = await session.call_tool("network_monitor", {
                "operation": "start",
                "channel": 6
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ Monitor mode started")
                print(f"  Monitor interface: {data.get('monitor_interface', 'unknown')}\n")
            else:
                print(f"  ✗ Failed to start monitor mode: {data.get('error', 'unknown')}\n")
                return

            # Step 3: Capture packets for 30 seconds
            print("Step 3: Capturing packets for 30 seconds...")
            result = await session.call_tool("packet_capture", {
                "channel": 6,
                "duration": 30,
                "output_prefix": "test_capture"
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ Capture complete")
                print(f"  Packets captured: {data.get('packets_captured', 0)}")
                print(f"  Files: {data.get('capture_files', [])}")
                networks = data.get("networks", [])
                print(f"  Networks found: {len(networks)}")
                for net in networks[:3]:  # Show first 3
                    print(f"    - {net.get('essid', 'Hidden')} ({net.get('bssid', '')})")
                print()
            else:
                print(f"  ✗ Capture failed: {data.get('error', 'unknown')}\n")

            # Step 4: Stop monitor mode
            print("Step 4: Stopping monitor mode...")
            result = await session.call_tool("network_monitor", {
                "operation": "stop"
            })
            data = json.loads(result.content[0].text)
            if data.get("success"):
                print(f"  ✓ Monitor mode stopped\n")

            print("=== Wireless Monitoring Complete ===")


async def example_file_operations():
    """
    Example: File operations in shared folder.
    """
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "kali_driver_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=== File Operations Example ===\n")

            # List C files
            print("1. Listing C source files...")
            result = await session.call_tool("file_ops", {
                "operation": "list",
                "filter_pattern": "*.c"
            })
            data = json.loads(result.content[0].text)
            print(f"  Result: {data.get('output', 'No files found')[:200]}...\n")

            # Search for pattern
            print("2. Searching for 'MODULE_LICENSE' in source files...")
            result = await session.call_tool("file_ops", {
                "operation": "search",
                "search_pattern": "MODULE_LICENSE"
            })
            data = json.loads(result.content[0].text)
            matches = data.get("matches", [])
            print(f"  Found {len(matches)} matches\n")

            print("=== File Operations Complete ===")


if __name__ == "__main__":
    import sys

    print("Kali Driver MCP - Usage Examples\n")
    print("Choose an example to run:")
    print("  1. Driver Development Workflow")
    print("  2. Wireless Monitoring and Capture")
    print("  3. File Operations")
    print()

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        asyncio.run(example_driver_development_workflow())
    elif choice == "2":
        asyncio.run(example_wireless_monitoring())
    elif choice == "3":
        asyncio.run(example_file_operations())
    else:
        print("Invalid choice")
        sys.exit(1)
