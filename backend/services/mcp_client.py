import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
from typing import List, Dict, Any, Optional
import asyncio

class McpClientService:
    def __init__(self):
        pass

    async def get_tools(self, url: str, headers: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Connects to an MCP server via SSE and fetches the list of available tools.
        """
        headers = headers or {}
        try:
            async with sse_client(url=url, headers=headers) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    # Convert tool objects to dictionary representation
                    return [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in result.tools
                    ]
        except Exception as e:
            print(f"Error fetching tools from {url} via standard SSE: {e}. Trying fallback HTTP...")
            try:
                result = await self._http_mcp_request(url, "tools/list", {}, headers)
                if "tools" in result:
                    return result["tools"]
                return []
            except Exception as e2:
                print(f"Error fetching tools from {url} via fallback: {e2}")
                raise e

    async def call_tool(self, url: str, tool_name: str, arguments: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Any:
        """
        Connects to an MCP server via SSE and executes a specific tool.
        """
        headers = headers or {}
        arguments = arguments or {}
        try:
            async with sse_client(url=url, headers=headers) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    result: CallToolResult = await session.call_tool(name=tool_name, arguments=arguments)
                    
                    # Process result content
                    output = []
                    for content in result.content:
                        if content.type == "text":
                            output.append(content.text)
                        elif content.type == "image":
                            output.append(f"[Image: {content.mimeType}]") # Handle images if needed
                        elif content.type == "resource":
                             output.append(f"[Resource: {content.uri}]")

                    return "\n".join(output)
        except Exception as e:
            print(f"Error calling tool {tool_name} on {url} via standard SSE: {e}. Trying fallback HTTP...")
            try:
                params = {"name": tool_name, "arguments": arguments}
                result = await self._http_mcp_request(url, "tools/call", params, headers)
                
                # Check for content in result (similar to tools/call structure)
                output = []
                if "content" in result:
                    for content in result["content"]:
                         if isinstance(content, dict):
                            c_type = content.get("type")
                            if c_type == "text":
                                output.append(content.get("text", ""))
                            elif c_type == "image":
                                output.append(f"[Image: {content.get('mimeType')}]")
                            elif c_type == "resource":
                                output.append(f"[Resource: {content.get('uri')}]")
                return "\n".join(output)

            except Exception as e2:
                print(f"Error calling tool {tool_name} on {url} via fallback: {e2}")
                raise e

    async def _http_mcp_request(self, url: str, method: str, params: Dict[str, Any], headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fallback method to generic MCP request via stateless HTTP POST (Vercel AI SDK style).
        """
        import json
        
        headers = headers.copy() if headers else {}
        headers["Content-Type"] = "application/json"
        # Ensure Accept header includes text/event-stream as per Vercel AI SDK requirements
        if "Accept" not in headers:
             headers["Accept"] = "application/json, text/event-stream"
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        print(f"DEBUG: Sending fallback request to {url} with headers {headers}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        json_str = line[6:]
                        try:
                            data = json.loads(json_str)
                            if "result" in data:
                                return data["result"]
                            if "error" in data:
                                raise Exception(f"MCP Error: {data['error']}")
                        except json.JSONDecodeError:
                            continue
        raise Exception("Stream ended without valid result")
