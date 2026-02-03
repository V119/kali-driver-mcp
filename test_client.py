"""Simple MCP client for testing the Kali Driver MCP Server."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Run the test client."""
    # Server parameters - adjust path as needed
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "kali_driver_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            print("=== Available Tools ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"\n{tool.name}:")
                print(f"  Description: {tool.description}")

            print("\n" + "="*50)
            print("Running example tool calls...\n")

            # Example 1: Get kernel info
            print("1. Getting kernel information...")
            result = await session.call_tool("kernel_info", {"detail_level": "basic"})
            print(f"Result: {result.content[0].text}\n")

            # Example 2: Verify shared folder
            print("2. Verifying shared folder...")
            result = await session.call_tool("code_sync", {})
            print(f"Result: {result.content[0].text}\n")

            # Example 3: List files
            print("3. Listing files in shared folder...")
            result = await session.call_tool("file_ops", {
                "operation": "list",
                "recursive": False
            })
            print(f"Result: {result.content[0].text}\n")

            # Example 4: Get network info
            print("4. Getting network interface info...")
            result = await session.call_tool("network_info", {
                "interface": "all",
                "detail_level": "basic"
            })
            print(f"Result: {result.content[0].text}\n")

            print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
