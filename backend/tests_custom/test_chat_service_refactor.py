import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.session import Base
from services.chat_service import ChatService
from db.models import Project, ChatSession

# Use in-memory SQLite for testing to avoid messing with real DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_project(db_session):
    chat_service = ChatService(db_session)
    project = await chat_service.create_project(user_id="testuser", name="Test Project")
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.user_id == "testuser"

@pytest.mark.asyncio
async def test_create_session(db_session):
    chat_service = ChatService(db_session)
    session = await chat_service.create_session(
        user_id="testuser", 
        db_id="testdb", 
        title="Test Session"
    )
    assert session.id is not None
    assert session.title == "Test Session"
    assert session.db_id == "testdb"

@pytest.mark.asyncio
async def test_project_session_relationship(db_session):
    chat_service = ChatService(db_session)
    project = await chat_service.create_project(user_id="testuser", name="Test Project")
    session = await chat_service.create_session(
        user_id="testuser", 
        db_id="testdb", 
        project_id=project.id
    )
    assert session.project_id == project.id
