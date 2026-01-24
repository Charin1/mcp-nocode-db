
import asyncio
import os
import sys

# Ensure we can import services
sys.path.append(os.getcwd())

from services.mcp_client import McpClientService

async def test_real_mcp():
    print("--- Testing Real MCP Connection to https://mimilabs.ai/api/mcp ---")
    
    url = "https://mimilabs.ai/api/mcp"
    client = McpClientService()
    
    try:
        # 1. Fetch Tools
        print("Fetching tools...")
        tools = await client.get_tools(
            connection_config={"type": "sse", "url": url},
            headers={"User-Agent": "MCP-Test-Client"}
        )
        
        print(f"Success! Found {len(tools)} tools.")
        for t in tools:
            print(f"- Name: {t['name']}")
            print(f"  Description: {t.get('description', 'No description')}")
            # print(f"  Schema: {t.get('inputSchema')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_mcp())
