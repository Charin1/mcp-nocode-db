import asyncio
import os
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from services.db_manager import DbManager

# Initialize FastMCP server
mcp = FastMCP("mcp-nocode-db")

@mcp.tool()
async def list_tables(db_id: str) -> List[str]:
    """
    List all tables in the specified database.
    
    Args:
        db_id: The ID of the database to query (e.g., "postgres").
    """
    manager = DbManager()
    try:
        schema = await manager.get_schema(db_id)
        return [table["name"] for table in schema]
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp.tool()
async def get_schema(db_id: str) -> List[Dict[str, Any]]:
    """
    Get the full schema (tables and columns) for the specified database.
    
    Args:
        db_id: The ID of the database to query.
    """
    manager = DbManager()
    try:
        schema = await manager.get_schema(db_id)
        # Schema is already a list of dicts
        return schema
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
async def execute_query(db_id: str, query: str) -> str:
    """
    Execute a raw SQL query against the database.
    
    Args:
        db_id: The ID of the database to query.
        query: The raw SQL query to execute.
    """
    manager = DbManager()
    try:
        # Check for mutations if necessary, though DbManager might handle some safety
        # For this MCP tool, we'll rely on the underlying DbManager's execute_query
        result = await manager.execute_query(db_id, query)
        return str(result)
    except Exception as e:
        return f"Error executing query: {str(e)}"

# Resource to expose schema as a text resource
@mcp.resource("postgres://{db_id}/schema")
async def get_schema_resource(db_id: str) -> str:
    """
    Get the database schema as a formatted string.
    """
    manager = DbManager()
    try:
        schema = await manager.get_schema(db_id)
        schema_str = f"Schema for {db_id}:\n"
        for table in schema:
            schema_str += f"- {table['name']}\n"
            for col in table['columns']:
                schema_str += f"  - {col['name']} ({col['type']})\n"
        return schema_str
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

if __name__ == "__main__":
    # This allows running the MCP server directly via stdio
    mcp.run()
