import asyncio
from typing import Any, Dict, List
from fastapi import APIRouter, Request, Response
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

from services.db_manager import DbManager

router = APIRouter()

# Initialize MCP Server
mcp_server = Server("mcp-nocode-db")

# --- Tool Definitions ---

@mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="list_tables",
            description="List all tables in the specified database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "db_id": {"type": "string", "description": "Database ID (e.g. 'postgres')"}
                },
                "required": ["db_id"]
            }
        ),
        types.Tool(
            name="get_schema",
            description="Get the full schema for the specified database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "db_id": {"type": "string", "description": "Database ID"}
                },
                "required": ["db_id"]
            }
        ),
        types.Tool(
            name="execute_query",
            description="Execute a raw SQL query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "db_id": {"type": "string", "description": "Database ID"},
                    "query": {"type": "string", "description": "SQL query"}
                },
                "required": ["db_id", "query"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    manager = DbManager()
    
    if name == "list_tables":
        db_id = arguments.get("db_id")
        try:
            schema = await manager.get_schema(db_id)
            tables = [table.name for table in schema]
            return [types.TextContent(type="text", text=str(tables))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "get_schema":
        db_id = arguments.get("db_id")
        try:
            schema = await manager.get_schema(db_id)
            # Convert to a friendly string or JSON
            return [types.TextContent(type="text", text=str([t.dict() for t in schema]))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "execute_query":
        db_id = arguments.get("db_id")
        query = arguments.get("query")
        try:
            result = await manager.execute_query(db_id, query)
            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
            
    raise ValueError(f"Unknown tool: {name}")


# --- Resource Definitions ---

@mcp_server.list_resources()
async def list_resources() -> List[types.Resource]:
    # In a real app, we might dynamically list resources based on available DBs
    return [
        types.Resource(
            uri=types.AnyUrl("postgres://postgres/schema"),
            name="PostgreSQL Schema",
            description="Schema of the postgres database",
            mimeType="text/plain"
        )
    ]

@mcp_server.read_resource()
async def read_resource(uri: types.AnyUrl) -> str | bytes:
    if str(uri) == "postgres://postgres/schema":
        manager = DbManager()
        try:
            schema = await manager.get_schema("postgres")
            schema_str = "Schema:\n"
            for table in schema:
                schema_str += f"- {table.name}\n"
            return schema_str
        except Exception as e:
            return f"Error: {str(e)}"
    raise ValueError(f"Unknown resource: {uri}")


# --- SSE Endpoints ---

# Store active transport
sse_transport = None

@router.get("/sse")
async def handle_sse(request: Request):
    global sse_transport
    
    async def event_generator():
        global sse_transport
        # Create a new transport for this connection
        # Note: In a real multi-user app, we'd need to manage multiple transports
        # For simplicity here, we're assuming single client or just demonstrating the pattern
        transport = SseServerTransport("/api/mcp/messages")
        sse_transport = transport
        
        async with mcp_server.run(transport.read_incoming(), transport.write_outgoing()) as runner:
             async for message in transport.outgoing_messages():
                 yield message

    return EventSourceResponse(event_generator())

@router.post("/messages")
async def handle_messages(request: Request):
    global sse_transport
    if sse_transport:
        await sse_transport.handle_post_message(request)
        return Response(status_code=200)
    else:
        return Response(status_code=400, content="No active SSE connection")
