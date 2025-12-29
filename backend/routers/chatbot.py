from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from models.auth import User
from models.query import ChatRequest, ChatMessage
from services.llm_service import LLMService
from services.db_manager import DbManager
from services.security import get_current_user
from services.visualization_service import VisualizationService

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


@router.post("/message", response_model=ChatMessage)
async def handle_chat_message(
    request: ChatRequest, current_user: User = Depends(get_current_user)
):
    llm_service = LLMService()
    db_manager = DbManager()

    try:
        # For now, we'll just get the schema and pass it to the LLM service.
        # The conversational logic will be in the LLM service.
        schema = await db_manager.get_schema_for_prompt(request.db_id)
        db_engine = db_manager.get_db_engine(request.db_id)

        # We'll need to update the LLM service to handle a list of messages.
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
    
    This endpoint analyzes the query results and determines the best chart type
    and configuration for visualization. Optionally accepts a user request
    to specify chart type preferences.
    """
    viz_service = VisualizationService()

    try:
        if request.user_request:
            # Use user's natural language request to determine chart type
            chart_config = viz_service.generate_chart_config_from_intent(
                user_request=request.user_request,
                columns=request.columns,
                rows=request.rows
            )
        else:
            # Auto-detect best chart configuration
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

