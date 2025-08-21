from fastapi import APIRouter, Depends, HTTPException
from models.auth import User
from models.query import ChatRequest, ChatMessage
from services.llm_service import LLMService
from services.db_manager import DbManager
from services.security import get_current_user

router = APIRouter()


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
            provider=request.model_provider,
            messages=request.messages,
            schema=schema,
            engine=db_engine,
        )

        return response_message

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
