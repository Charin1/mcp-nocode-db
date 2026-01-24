from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from services.mcp_client import McpClientService

from models.auth import User
from models.query import ChatRequest, ChatMessage
from models.chat import ChatSession, ChatMessageDB, CreateSessionRequest, InitialChatResponse, Project, CreateProjectRequest
from services.llm_service import LLMService
from services.db_manager import DbManager
from services.security import get_current_user
from services.visualization_service import VisualizationService
from services.chat_service import ChatService
from db.session import get_db

router = APIRouter()


class VisualizationRequest(BaseModel):
    """Request model for generating chart visualization from query results."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    user_request: Optional[str] = None  # Optional natural language request for chart type


class VisualizationResponse(BaseModel):
    """Response model containing chart configuration."""
    chart_config: Dict[str, Any]
    message: str

# --- Project Management Endpoints ---

@router.post("/projects", response_model=Project)
async def create_project(
    request: CreateProjectRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project folder."""
    chat_service = ChatService(db)
    try:
        project = await chat_service.create_project(
            user_id=current_user.username,
            name=request.name
        )
        return project # ORM model compatible with Pydantic mode=True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[Project])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for the current user."""
    chat_service = ChatService(db)
    try:
        projects = await chat_service.get_user_projects(user_id=current_user.username)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and unlink its sessions."""
    chat_service = ChatService(db)
    success = await chat_service.delete_project(project_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"status": "success", "message": "Project deleted"}


# --- Session Management Endpoints ---

@router.post("/sessions", response_model=ChatSession)
async def create_session(
    request: CreateSessionRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    chat_service = ChatService(db)
    try:
        session = await chat_service.create_session(
            user_id=current_user.username,
            db_id=request.db_id,
            title=request.title,
            project_id=request.project_id
        )
        return session
    except Exception as e:
        print(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the current user, optionally filtered by title."""
    chat_service = ChatService(db)
    try:
        sessions = await chat_service.get_user_sessions(user_id=current_user.username, search_query=q)
        return sessions
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=InitialChatResponse)
async def get_session(
    session_id: int, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific session and its messages."""
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id=session_id, user_id=current_user.username)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await chat_service.get_session_messages(session_id=session_id)
    return InitialChatResponse(session=session, messages=messages)


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: int, 
    request: Dict[str, Any], 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rename a chat session or move it to a project."""
    chat_service = ChatService(db)
    
    # Handle Rename
    if "title" in request:
        new_title = request.get("title")
        if not new_title:
             raise HTTPException(status_code=400, detail="Title cannot be empty")
        success = await chat_service.rename_session(session_id, current_user.username, new_title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

    # Handle Move to Project
    if "project_id" in request:
        project_id = request.get("project_id") 
        success = await chat_service.move_session_to_project(session_id, current_user.username, project_id)
        if not success:
             raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "success", "message": "Session updated"}



@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session."""
    chat_service = ChatService(db)
    success = await chat_service.delete_session(session_id, current_user.username)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "success", "message": "Session deleted"}



@router.post("/sessions/{session_id}/message", response_model=List[ChatMessageDB])
async def send_message(
    session_id: int, 
    message: ChatMessage, 
    model_provider: str = "gemini",
    active_mcp_ids: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a session and get a response."""
    
    chat_service = ChatService(db)

    # 1. Verify Session Ownership
    session = await chat_service.get_session(session_id=session_id, user_id=current_user.username)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    llm_service = LLMService()
    db_manager = DbManager()
    mcp_client = McpClientService()
    
    try:
        # 2. Save User Message
        await chat_service.add_message(
            session_id=session_id,
            role="user",
            content=message.content
        )
        
        # 3. Fetch Active MCP Tools
        tools = []
        active_connections = []
        if active_mcp_ids:
            # Parse IDs if they came as a single comma-separated string (frontend quirk handling)
            # But normally List[str] handling depends on client. We'll assume List.
            # Handle potential case where it's a single string of comma separated values
            ids_to_fetch = []
            for id_val in active_mcp_ids:
                if "," in id_val:
                    ids_to_fetch.extend(id_val.split(","))
                else:
                    ids_to_fetch.append(id_val)
            
            # Fetch connections from DB
            from models.mcp_connection import MCPConnection
            from sqlalchemy.future import select
            
            stmt = select(MCPConnection).where(MCPConnection.id.in_(ids_to_fetch), MCPConnection.user_id == current_user.username)
            result = await db.execute(stmt)
            active_connections = result.scalars().all()
            
            for conn in active_connections:
                try:
                    conn_tools = await mcp_client.get_tools(
                        connection_config={
                            "type": conn.connection_type,
                            "url": conn.url,
                            "configuration": conn.configuration or {}
                        },
                        headers=conn.headers
                    )
                    # Namespace tools to avoid collision? For now, raw.
                    tools.extend(conn_tools)
                except Exception as e:
                    print(f"Failed to fetch tools from {conn.name}: {e}")

        # 4. ReAct Loop (Max depth 5)
        max_turns = 5
        current_turn = 0
        final_response_message = None
        
        while current_turn < max_turns:
            current_turn += 1
            print(f"--- Turn {current_turn}/{max_turns} ---")
            
            # Retrieve Context (Refresh each turn as we might add tool outputs)
            db_messages = await chat_service.get_session_messages(session_id=session_id)
            context_messages = []
            for db_msg in db_messages:
                context_messages.append(ChatMessage(
                    role=db_msg.role,
                    content=db_msg.content,
                    query=db_msg.query
                ))
                
            schema = await db_manager.get_schema_for_prompt(session.db_id)
            db_engine = db_manager.get_db_engine(session.db_id)
            
            # Generate Response
            print(f"Calling LLM: {model_provider} with {len(context_messages)} messages...")
            response_message = await llm_service.generate_response_from_messages(
                db_id=session.db_id,
                provider=model_provider,
                messages=context_messages,
                schema=schema,
                engine=db_engine,
                tools=tools if tools else None
            )
            print(f"LLM Response Received. Content len: {len(response_message.content) if response_message.content else 0}")
            
            if response_message.query and response_message.query.startswith("__TOOL_CALL__:"):
                # It's a tool call
                import json
                try:
                    payload = json.loads(response_message.query[len("__TOOL_CALL__:") :])
                    tool_name = payload["tool"]
                    tool_args = payload["args"]
                    
                    print(f"Model executing MCP Tool: {tool_name} with args: {tool_args}")

                    # Save the "Thought/Action" from assistant
                    await chat_service.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=response_message.content,
                        query=f"Executing tool: {tool_name}"
                    )
                    
                    # Find which connection has this tool
                    tool_result = f"Error: Tool {tool_name} not found or failed execution."
                    
                    for conn in active_connections:
                         try:
                             # TODO: Improve efficient tool routing.
                             print(f"Sending tool call to connection: {conn.name} ({conn.url})")
                             res = await mcp_client.call_tool(
                                 connection_config={
                                     "type": conn.connection_type,
                                     "url": conn.url,
                                     "configuration": conn.configuration or {}
                                 }, 
                                 tool_name=tool_name, 
                                 arguments=tool_args, 
                                 headers=conn.headers
                             )
                             tool_result = f"Tool Output: {res}"
                             print(f"Tool executed successfully. Output len: {len(str(res))}")
                             break # Success
                         except Exception as exc:
                             print(f"Tool execution failed on {conn.name}: {exc}")
                             continue
                    
                    # Save Tool Result
                    await chat_service.add_message(
                        session_id=session_id,
                        role="user",
                        content=f"Observation: {tool_result}"
                    )
                    
                    # Loop continues
                    continue
                    
                except Exception as e:
                    print(f"Error parsing/executing tool call: {e}")
                    await chat_service.add_message(
                        session_id=session_id,
                        role="user",
                        content=f"Observation: Error executing tool: {str(e)}"
                    )
                    continue
            else:
                # Final response (or just a question/SQL query)
                print("Model provided final response or SQL.")
                if response_message.query:
                     print(f"Generated SQL/Command: {response_message.query}")
                final_response_message = response_message
                break
        
        if not final_response_message:
            final_response_message = ChatMessage(role="assistant", content="I stopped processing after too many tool calls.")
            
        # 5. Save Final Assistant Response
        saved_response = await chat_service.add_message(
            session_id=session_id,
            role=final_response_message.role,
            content=final_response_message.content,
            query=final_response_message.query
        )
        
        return [saved_response]

    except Exception as e:
        # Log error in chat?
        print(f"Critical Error in chat loop: {e}")
        await chat_service.add_message(session_id=session_id, role="assistant", content=f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Legacy / Stateless Endpoint (Optional: Keep or Deprecate) ---

@router.post("/message", response_model=ChatMessage)
async def handle_chat_message(
    request: ChatRequest, current_user: User = Depends(get_current_user)
):
    # ... Keeps existing logic if needed for stateless testing ...
    llm_service = LLMService()
    db_manager = DbManager()

    try:
        schema = await db_manager.get_schema_for_prompt(request.db_id)
        db_engine = db_manager.get_db_engine(request.db_id)

        response_message = await llm_service.generate_response_from_messages(
            db_id=request.db_id,
            provider=request.model_provider,
            messages=request.messages,
            schema=schema,
            engine=db_engine,
        )

        return response_message

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize", response_model=VisualizationResponse)
async def generate_visualization(
    request: VisualizationRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate chart configuration from query results.
    """
    viz_service = VisualizationService()

    try:
        if request.user_request:
            chart_config = viz_service.generate_chart_config_from_intent(
                user_request=request.user_request,
                columns=request.columns,
                rows=request.rows
            )
        else:
            chart_config = viz_service.analyze_data_for_chart(
                columns=request.columns,
                rows=request.rows
            )

        if not chart_config:
            raise HTTPException(
                status_code=400, 
                detail="Unable to generate visualization for this data. Ensure the data contains numeric columns."
            )

        return VisualizationResponse(
            chart_config=chart_config,
            message="Chart configuration generated successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
