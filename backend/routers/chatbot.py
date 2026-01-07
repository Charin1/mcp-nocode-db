from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from models.auth import User
from models.query import ChatRequest, ChatMessage
from models.chat import ChatSession, ChatMessageDB, CreateSessionRequest, InitialChatResponse
from services.llm_service import LLMService
from services.db_manager import DbManager
from services.security import get_current_user
from services.visualization_service import VisualizationService
from services.chat_service import ChatService

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


# --- Session Management Endpoints ---

@router.post("/sessions", response_model=ChatSession)
async def create_session(
    request: CreateSessionRequest, current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        session = ChatService.create_session(
            user_id=current_user.username,
            db_id=request.db_id,
            title=request.title
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """List all chat sessions for the current user."""
    try:
        return ChatService.get_user_sessions(user_id=current_user.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=InitialChatResponse)
async def get_session(
    session_id: int, current_user: User = Depends(get_current_user)
):
    """Get a specific session and its messages."""
    session = ChatService.get_session(session_id=session_id, user_id=current_user.username)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = ChatService.get_session_messages(session_id=session_id)
    return InitialChatResponse(session=session, messages=messages)


@router.post("/sessions/{session_id}/message", response_model=List[ChatMessageDB])
async def send_message(
    session_id: int, 
    message: ChatMessage, 
    model_provider: str = "gemini",
    current_user: User = Depends(get_current_user)
):
    """Send a message to a session and get a response."""
    
    # 1. Verify Session Ownership
    session = ChatService.get_session(session_id=session_id, user_id=current_user.username)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    llm_service = LLMService()
    db_manager = DbManager()
    
    try:
        # 2. Save User Message
        ChatService.add_message(
            session_id=session_id,
            role="user",
            content=message.content
        )
        
        # 3. Retrieve Context (All messages for now, could apply limit)
        db_messages = ChatService.get_session_messages(session_id=session_id)
        
        # Convert DB messages to ChatMessage objects for LLM service
        # Note: ChatMessageDB -> ChatMessage conversion
        # We need to map role, content, and query if present
        context_messages = []
        for db_msg in db_messages:
            context_messages.append(ChatMessage(
                role=db_msg.role,
                content=db_msg.content,
                query=db_msg.query
            ))
            
        # 4. Generate Response
        schema = await db_manager.get_schema_for_prompt(session.db_id)
        db_engine = db_manager.get_db_engine(session.db_id)
        
        response_message = await llm_service.generate_response_from_messages(
            db_id=session.db_id,
            provider=model_provider,
            messages=context_messages,
            schema=schema,
            engine=db_engine,
        )
        
        # 5. Save Assistant Response
        saved_response = ChatService.add_message(
            session_id=session_id,
            role=response_message.role,
            content=response_message.content,
            query=response_message.query
        )
        
        # Return the saved assistant message as a list
        return [saved_response]

    except Exception as e:
        # Log error in chat?
        ChatService.add_message(session_id=session_id, role="assistant", content=f"Error: {str(e)}")
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

