import asyncio
import json
from arq import Worker
from typing import Dict, Any

from db.session import engine, Base, AsyncSessionLocal
from services.llm_service import LLMService
from services.chat_service import ChatService
from services.db_manager import DbManager
from models.chat import ChatMessage # Pydantic model
from db.models import ChatMessage as ChatMessageORM
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup(ctx):
    logger.info("Worker starting up...")
    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Worker started, DB initialized.")

async def shutdown(ctx):
    logger.info("Worker shutting down...")
    await engine.dispose()

async def generate_response_task(ctx, session_id: int, user_message_content: str, db_id: str, provider: str):
    """
    Background task to generate LLM response and save it.
    """
    logger.info(f"Processing task for session {session_id}")
    
    async with AsyncSessionLocal() as session:
        chat_service = ChatService(session)
        llm_service = LLMService()
        db_manager = DbManager()

        try:
            # 1. Retrieve Context
            # We need to fetch messages again to provide context
            db_messages = await chat_service.get_session_messages(session_id=session_id)
            
            context_messages = []
            for db_msg in db_messages:
                context_messages.append(ChatMessage(
                    role=db_msg.role,
                    content=db_msg.content,
                    query=db_msg.query
                ))
            
            # 2. Add the user message if it wasn't already added (Caller might have added it)
            # Strategy: Caller adds user message, then calls worker.
            # So context_messages should already include it if ChatService.get_session_messages works correctly.
            
            # 3. Generate Response
            schema = await db_manager.get_schema_for_prompt(db_id)
            db_engine = db_manager.get_db_engine(db_id)
            
            response_message = await llm_service.generate_response_from_messages(
                db_id=db_id,
                provider=provider,
                messages=context_messages,
                schema=schema,
                engine=db_engine,
            )
            
            # 4. Save Assistant Response
            await chat_service.add_message(
                session_id=session_id,
                role=response_message.role,
                content=response_message.content,
                query=response_message.query
            )
            
            logger.info(f"Finished generating response for session {session_id}")
            return {"status": "completed", "session_id": session_id}

        except Exception as e:
            logger.error(f"Error acting on session {session_id}: {e}")
            # Ensure we log the error to the chat so the user isn't stuck waiting
            try:
                await chat_service.add_message(
                    session_id=session_id, 
                    role="assistant", 
                    content=f"Error generating response: {str(e)}"
                )
            except Exception as write_error:
                logger.error(f"Failed to write error message to DB: {write_error}")
            
            # We don't raise here if we want to avoid infinite retries of a bad prompt,
            # but for intermittent errors, raising triggers arq retry.
            # Since LLMService has its own retry (tenacity), we assume failures here are likely non-retriable (like config error)
            # or catastrophic networking.
            # Best practice: retry a few times then fail. Arq handles this via max_tries.
            raise e

# Define the worker settings
class WorkerSettings:
    functions = [generate_response_task]
    redis_settings = "redis://redis:6379"
    on_startup = startup
    on_shutdown = shutdown
    max_tries = 3
