
import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Base, ChatSession, ChatMessage
from models.auth import User
from models.chat import ChatMessageDB
from services.chat_service import ChatService

# Use an in-memory SQLite DB for testing logic independent of file permissions
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def verify_persistence():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        chat_service = ChatService(db)
        user_id = "test_user"
        
        # 1. Create Session
        print("Creating session...")
        session = await chat_service.create_session(user_id=user_id, db_id="test_db")
        print(f"Session created: {session.id}")

        # 2. Add Message
        print("Adding message...")
        msg = await chat_service.add_message(
            session_id=session.id,
            role="assistant",
            content="Run this query",
            query="SELECT * FROM users"
        )
        print(f"Message added: {msg.id}")

        # 3. Update Message (Simulate PATCH)
        print("Updating message with results...")
        dummy_results = {"columns": ["id", "name"], "rows": [{"id": 1, "name": "Alice"}]}
        dummy_chart = {"type": "bar", "title": "Test Chart"}
        
        success = await chat_service.update_message(
            message_id=msg.id,
            results=dummy_results,
            chart_config=dummy_chart
        )
        print(f"Update success: {success}")

        # 4. Verify Persistence
        print("Fetching messages...")
        messages = await chat_service.get_session_messages(session_id=session.id)
        saved_msg = messages[0]
        
        print(f"Saved Results: {saved_msg.results}")
        
        try:
            results_json = json.loads(saved_msg.results)
            chart_json = json.loads(saved_msg.chart_config)
            
            assert results_json == dummy_results
            assert chart_json == dummy_chart
            print("✅ VERIFICATION PASSED: Results and Chart Config persisted correctly.")
        except Exception as e:
            print(f"❌ VERIFICATION FAILED: {e}")
            sys.exit(1)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_persistence())
