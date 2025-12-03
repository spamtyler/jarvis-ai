import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="/mnt/fast_data/projects/vision_agent/duckduckgo_launcher.sh",
        args=[],
        env=os.environ
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available Tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

if __name__ == "__main__":
    asyncio.run(run())
