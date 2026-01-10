from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any
from datetime import datetime

from db.models import AuditLog, SavedQuery


# Since I am replacing the file, I need to redefine the Pydantic models or import them.
# The previous file defined them. I will keep them here.
from pydantic import BaseModel

class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    username: str
    db_id: str
    natural_query: Optional[str] = None
    generated_query: Optional[str] = None
    executed: bool
    success: bool
    error: Optional[str] = None
    rows_returned: Optional[int] = None
    
    class Config:
        from_attributes = True

class SavedQueryEntry(BaseModel):
    id: int
    username: str
    db_id: str
    name: str
    natural_language_query: Optional[str] = None
    raw_query: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Remove initialize class method as we use dependency injection

    async def log(self, **kwargs):
        # kwargs match AuditLog model fields
        log_entry = AuditLog(**kwargs)
        self.db.add(log_entry)
        await self.db.commit()

    async def get_logs(self, limit: int = 100) -> List[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        )
        return result.scalars().all()

    async def save_query(self, username: str, db_id: str, name: str, natural_query: str, raw_query: str):
        saved_query = SavedQuery(
            username=username,
            db_id=db_id,
            name=name,
            natural_language_query=natural_query,
            raw_query=raw_query
        )
        self.db.add(saved_query)
        await self.db.commit()

    async def get_saved_queries(self, username: str) -> List[SavedQuery]:
        result = await self.db.execute(
            select(SavedQuery).where(SavedQuery.username == username).order_by(SavedQuery.created_at.desc())
        )
        return result.scalars().all()

    async def delete_saved_query(self, query_id: int, username: str):
        result = await self.db.execute(
            select(SavedQuery).where(SavedQuery.id == query_id, SavedQuery.username == username)
        )
        query = result.scalars().first()
        if query:
            await self.db.delete(query)
            await self.db.commit()
