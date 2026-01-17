from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from db.session import get_db
from models.mcp_connection import MCPConnection
from models.auth import User
from services.security import get_current_user
from pydantic import BaseModel, HttpUrl

router = APIRouter()

# Pydantic models for request/response
class MCPConnectionCreate(BaseModel):
    name: str
    connection_type: str = "sse" # "sse" or "stdio"
    url: str = None # Optional, for SSE backwards compatibility
    configuration: Dict[str, Any] = {}
    headers: Dict[str, Any] = {}

class MCPConnectionOut(BaseModel):
    id: int
    name: str
    connection_type: str
    url: str | None
    configuration: Dict[str, Any]
    headers: Dict[str, Any]
    created_at: Any 

    class Config:
        from_attributes = True

@router.post("/", response_model=MCPConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_mcp_connection(
    connection: MCPConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new MCP connection for the current user."""
    # Logic to populate configuration from deprecated fields if needed
    config = connection.configuration
    if connection.connection_type == "sse" and connection.url and not config.get("url"):
        config["url"] = connection.url

    new_connection = MCPConnection(
        user_id=current_user.username,
        name=connection.name,
        connection_type=connection.connection_type,
        url=connection.url, # Keep storing it alongside config for now
        configuration=config,
        headers=connection.headers
    )
    db.add(new_connection)
    try:
        await db.commit()
        await db.refresh(new_connection)
        return new_connection
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}"
        )

@router.get("/", response_model=List[MCPConnectionOut])
async def list_mcp_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all MCP connections associated with the current user."""
    result = await db.execute(
        select(MCPConnection).where(MCPConnection.user_id == current_user.username)
    )
    connections = result.scalars().all()
    return connections

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific MCP connection."""
    result = await db.execute(
        select(MCPConnection).where(
            MCPConnection.id == connection_id,
            MCPConnection.user_id == current_user.username
        )
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP connection not found"
        )
        
    await db.delete(connection)
    await db.commit()
    return None
