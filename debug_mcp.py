import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.mcp_client import McpClientService

async def test_mcp_connection():
    url = "https://mimilabs.ai/api/mcp"
    print(f"Testing connection to {url}...")
    
    client = McpClientService()
    try:
        tools = await client.get_tools(url)
        print(f"Successfully fetched {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"Failed to fetch tools: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
