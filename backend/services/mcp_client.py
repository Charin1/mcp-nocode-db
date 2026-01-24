import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
from typing import List, Dict, Any, Optional
import asyncio

class McpClientService:
    def __init__(self):
        pass

    async def get_tools(self, connection_config: Dict[str, Any], headers: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Connects to an MCP server and fetches the list of available tools.
        Args:
            connection_config: Dict containing 'type' ('sse' or 'stdio') and 'configuration'.
        """
        conn_type = connection_config.get("type", "sse")
        config = connection_config.get("configuration", {})
        headers = headers or {}
        
        if conn_type == "stdio":
            return await self._get_tools_stdio(config)
        else:
            # Default to SSE
            url = config.get("url") or connection_config.get("url") # Fallback to top-level url if in config
            if not url:
                 raise ValueError("URL is required for SSE connections")
            
            try:
                # SSE Implementation
                async with sse_client(url=url, headers=headers) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema
                            }
                            for tool in result.tools
                        ]
            except BaseException as e:
                # Catch ExceptionGroup or other async errors to ensure fallback runs
                # Also catch explicit 405 from underlying libs if they bubble up differently
                print(f"Error fetching tools from {url} via standard SSE: {e}. Broad fallback initiated...")
                
                # Generic Fallback: If SSE fails (e.g. 405 Method Not Allowed), try stateless HTTP POST
                try:
                    result = await self._http_mcp_request(url, "tools/list", {}, headers)
                    if "tools" in result:
                        return result["tools"]
                    return []
                except Exception as e2:
                    print(f"Error fetching tools from {url} via fallback: {e2}")
                    # If fallback also fails, raise the original error or the new one
                    raise e2 from e

    async def _get_tools_stdio(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        from mcp.client.stdio import stdio_client
        
        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})
        
        server_params = StdioServerParameters(command=command, args=args, env=env)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in result.tools
                ]

    async def call_tool(self, connection_config: Dict[str, Any], tool_name: str, arguments: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Any:
        conn_type = connection_config.get("type", "sse")
        config = connection_config.get("configuration", {})
        headers = headers or {}
        arguments = arguments or {}

        if conn_type == "stdio":
            return await self._call_tool_stdio(config, tool_name, arguments)
        else:
            url = config.get("url") or connection_config.get("url")
            if not url:
                 raise ValueError("URL is required for SSE connections")

            try:
                async with sse_client(url=url, headers=headers) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        result: CallToolResult = await session.call_tool(name=tool_name, arguments=arguments)
                        processed_res = self._process_tool_result(result)
                        print(f"DEBUG: MCP Tool '{tool_name}' SSE Success. Output Snippet: {processed_res[:200]}...")
                        return processed_res
            except BaseException as e:
                 print(f"Error calling tool {tool_name} on {url} via standard SSE: {e}. Trying fallback HTTP...")
                 try:
                    params = {"name": tool_name, "arguments": arguments}
                    result = await self._http_mcp_request(url, "tools/call", params, headers)
                    
                    # Manual processing since http fallback returns raw dict
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
                                    output.append(f"[Resource: {content.get('uri')}]")
                    final_res = "\n".join(output)
                    print(f"DEBUG: MCP Tool '{tool_name}' HTTP Fallback Success. Output Snippet: {final_res[:200]}...")
                    return final_res

                 except Exception as e2:
                    print(f"Error calling tool {tool_name} on {url} via fallback: {e2}")
                    raise e

    async def _call_tool_stdio(self, config: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> str:
        from mcp.client.stdio import stdio_client
        
        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})
        
        server_params = StdioServerParameters(command=command, args=args, env=env)
        
        async with stdio_client(server_params) as (read, write):
             async with ClientSession(read, write) as session:
                await session.initialize()
                result: CallToolResult = await session.call_tool(name=tool_name, arguments=arguments)
                return self._process_tool_result(result)

    def _process_tool_result(self, result: CallToolResult) -> str:
        output = []
        for content in result.content:
            if content.type == "text":
                output.append(content.text)
            elif content.type == "image":
                output.append(f"[Image: {content.mimeType}]") 
            elif content.type == "resource":
                    output.append(f"[Resource: {content.uri}]")
        return "\n".join(output)

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
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    print(f"DEBUG: HTTP {response.status_code} Error Body: {body.decode('utf-8')}")
                
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
