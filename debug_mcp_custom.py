import asyncio
import httpx
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIMILABS_MCP_URL = "https://www.mimilabs.ai/api/mcp"

async def list_mimilabs_tools():
    """
    Calls the Mimilabs MCP endpoint with 'tools/list'.
    """
    logger.info(f"Calling Mimilabs MCP with tools/call...")
    
    # Payload for tools/call (as per user snippet)
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "mimilabs_guide",
            "arguments": {
                "question": "hello"
            }
        },
        "id": 1
    }
    
    # EXACT header required by some Vercel AI SDK implementations
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build request manually to verify headers
            request = client.build_request("POST", MIMILABS_MCP_URL, json=payload, headers=headers)
            logger.info(f"Request Headers: {request.headers}")
            
            response = await client.send(request, stream=True)
            response.raise_for_status()
            
            logger.info(f"Response Status: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    json_str = line[6:]
                    try:
                        data = json.loads(json_str)
                        print(f"Received Data: {json.dumps(data, indent=2)}")
                        
                        if "result" in data:
                            tools = data["result"].get("tools", [])
                            print(f"Tools found: {len(tools)}")
                            for t in tools:
                                print(f"- {t['name']}")
                            return
                            
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        logger.error(f"Failed to call Mimilabs MCP: {e}")
        if isinstance(e, httpx.HTTPStatusError):
             print(f"Response Body: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(list_mimilabs_tools())
