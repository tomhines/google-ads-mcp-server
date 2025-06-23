#!/usr/bin/env python3
"""
Minimal MCP server for testing Claude Desktop connection
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create simple test server
server = Server("test-google-ads")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="test_connection",
            description="Test if Claude can see this tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Test message"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def test_connection(message: str) -> list[TextContent]:
    return [TextContent(
        type="text", 
        text=f"✅ Connection working! You said: {message}"
    )]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())