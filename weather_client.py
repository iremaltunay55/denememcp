#!/usr/bin/env python3
"""
Weather MCP Client - Example client for the Weather MCP
"""

import asyncio
import sys
from fastmcp import Client

async def main():
    # Create a client connected to the Weather MCP via HTTP
    client = Client("http://127.0.0.1:8000/mcp")

    async with client:
        # Get command line arguments
        if len(sys.argv) < 2:
            print("Usage: python weather_client.py <location>")
            return

        location = sys.argv[1]
        print(f"Getting weather for: {location}")

        # Call the get_weather_summary tool
        result = await client.call_tool("get_weather_summary", {"location": location})

        # Print the result
        print(result[0].text)

if __name__ == "__main__":
    asyncio.run(main())
