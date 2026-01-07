import sys
import os
import asyncio
import traceback

# Add generic backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.llm_service import LLMService
from services.db_manager import DbManager
from models.query import ChatMessage

from dotenv import load_dotenv

load_dotenv()

async def test():
    try:
        print(f"DEBUG: GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}, Length: {len(os.environ.get('GROQ_API_KEY', ''))}")
        
        print("Initializing DbManager...")
        db_manager = DbManager()
        print("DbManager initialized.")
        
        print("Initializing LLMService...")
        llm_service = LLMService()
        print("LLMService initialized.")
        
        dbs = db_manager.config.get("databases", {})
        if not dbs:
            print("No databases in config.")
            return

        db_id = "test_db" # Assuming test_db is used in tests, or we pick one
        if db_id not in dbs:
             db_id = list(dbs.keys())[0]
        
        print(f"Using db_id: {db_id}")
        
        print("Fetching schema...")
        schema = await db_manager.get_schema_for_prompt(db_id)
        print("Schema obtained.")
        
        engine = db_manager.get_db_engine(db_id)
        print(f"Engine: {engine}")

        # Test LLM generation mock
        print("Testing LLM generation...")
        messages = [ChatMessage(role="user", content="Show me users")]
        # Note: This requires API keys. If missing, it will fail.
        # But typically local env has them or we skip.
        try:
            response = await llm_service.generate_response_from_messages(
                db_id=db_id,
                provider="groq", # Default
                messages=messages,
                schema=schema,
                engine=engine
            )
            print("LLM Response:", response)
        except Exception as llm_e:
            print(f"LLM Error: {llm_e}")
            traceback.print_exc()

    except Exception as e:
        print(f"Service Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
