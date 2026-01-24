
import asyncio
import os
import sys

# Ensure we can import services
sys.path.append(os.getcwd())

from services.mcp_client import McpClientService

async def test_tool_execution():
    print("--- Testing Real MCP Tool Execution ---")
    
    # Use the non-www URL to test redirect/fallback
    url = "https://mimilabs.ai/api/mcp"
    client = McpClientService()
    
    tool_name = "mimilabs_data" 
    # Mocking arguments based on what the LLM tried to use
    arguments = {"question": "What is the patient count for BCBS?"}
    
    print(f"Calling tool '{tool_name}' on {url}...")
    
    try:
        # We need to Construct the connection_config dict matching what the chatbot uses
        # But we can just use call_tool directly with a mock config
        
        # NOTE: McpClientService.call_tool signature takes connection_config
        conn_config = {
            "type": "sse", # Start with SSE to restart the fallback logic
            "url": url,
            "configuration": {}
        }
        
        # Headers (no auth needed for default 30 rows? User prompt implied just URL)
        # But wait, user provided: "headers": { "Authorization": "Bearer YOUR_API_KEY" } in a previous message.
        # But in the verification script `verify_mcp_real.py` we didn't use headers and it worked for listing.
        # Let's try without first.
        headers = {"User-Agent": "MCP-Test-Client"}
        
        result = await client.call_tool(
            connection_config=conn_config,
            tool_name=tool_name,
            arguments=arguments,
            headers=headers
        )
        
        print(f"\nSuccess! Tool Output:\n{result}")
            
    except Exception as e:
        print(f"\nExecution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_execution())
