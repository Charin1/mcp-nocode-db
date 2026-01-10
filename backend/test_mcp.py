import asyncio
import httpx
import json
import traceback
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.types import CallToolRequest, Tool

async def run_test():
    print("Starting MCP Verification Test...")
    
    # URL of the MCP SSE endpoint
    url = "http://localhost:8000/api/mcp/sse"
    
    try:
        async with sse_client(url) as (read_stream, write_stream):
            print(f"Connected to MCP Server at {url}")
            
            async with ClientSession(read_stream, write_stream) as session:
                print("Initializing session...")
                await session.initialize()
                
                # List tools
                print("\n--- Listing Tools ---")
                response = await session.list_tools()
                tools = response.tools
                for tool in tools:
                    print(f"- {tool.name}: {tool.description}")
                
                # Call list_tables tool
                print("\n--- Calling list_tables ---")
                # Note: We need a valid db_id. Assuming 'postgres' is the default from seed/config.
                # But config.yaml has 'postgres_docker'.
                # Let's check config.yaml again or try 'postgres_docker'.
                # The original test used 'postgres'.
                # Let's try 'postgres_docker' as per config.
                
                db_id = "sqlite"
                try:
                    result = await session.call_tool("list_tables", arguments={"db_id": db_id})
                    print("Result:", result.content)
                except Exception as e:
                    print(f"Call failed for {db_id}: {e}")
                    # Try 'postgres' just in case
                    print("Retrying with 'postgres'...")
                    result = await session.call_tool("list_tables", arguments={"db_id": "postgres"})
                    print("Result:", result.content)
                
                # Call get_schema tool
                print("\n--- Calling get_schema ---")
                result = await session.call_tool("get_schema", arguments={"db_id": db_id})
                # Truncate output for readability
                content = str(result.content)
                print("Result (truncated):", content[:200] + "..." if len(content) > 200 else content)

                print("\nVerification Successful!")
            
    except Exception as e:
        print(f"\nVerification Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
