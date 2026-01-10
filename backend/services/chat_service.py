from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime

from db.models import Project, ChatSession, ChatMessage, AuditLog, SavedQuery
from models.chat import ChatSession as ChatSessionSchema, ChatMessageDB as ChatMessageSchema, Project as ProjectSchema

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, user_id: str, name: str) -> Project:
        project = Project(user_id=user_id, name=name)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_user_projects(self, user_id: str) -> List[Project]:
        result = await self.db.execute(
            select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
        )
        return result.scalars().all()

    async def delete_project(self, project_id: int, user_id: str) -> bool:
        # Check if exists and belongs to user
        result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalars().first()
        if not project:
            return False
            
        await self.db.delete(project)
        await self.db.commit()
        return True

    async def create_session(self, user_id: str, db_id: str, title: str = None, project_id: int = None) -> ChatSession:
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        session = ChatSession(
            user_id=user_id,
            db_id=db_id,
            title=title,
            project_id=project_id
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_sessions(self, user_id: str, search_query: str = None) -> List[ChatSession]:
        query = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc())
        
        if search_query:
            query = query.where(ChatSession.title.ilike(f"%{search_query}%"))
            
        result = await self.db.execute(query)
        return result.scalars().all()

    async def rename_session(self, session_id: int, user_id: str, new_title: str) -> bool:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalars().first()
        if not session:
            return False
            
        session.title = new_title
        await self.db.commit()
        return True

    async def move_session_to_project(self, session_id: int, user_id: str, project_id: Optional[int]) -> bool:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalars().first()
        if not session:
            return False
            
        session.project_id = project_id
        await self.db.commit()
        return True

    async def delete_session(self, session_id: int, user_id: str) -> bool:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalars().first()
        if not session:
            return False
            
        await self.db.delete(session)
        await self.db.commit()
        return True

    async def get_session(self, session_id: int, user_id: str) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        return result.scalars().first()

    async def add_message(self, session_id: int, role: str, content: str, query: str = None, chart_config: Dict = None) -> ChatMessage:
        # We don't verify session ownership here implicitly, ensuring caller does or FK constraint handles it (if we trust session_id)
        # But for safety/integrity, we assume session_id is valid.
        
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            query=query,
            chart_config=chart_config
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc())
        )
        return result.scalars().all()
