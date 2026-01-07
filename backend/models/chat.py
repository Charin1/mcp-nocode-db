from pydantic import BaseModel
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatSession(BaseModel):
    id: int
    user_id: str  # We store email/username as ID in this system currently
    db_id: str
    title: Optional[str] = "New Chat"
    project_id: Optional[int] = None
    created_at: str

class ChatMessageDB(BaseModel):
    id: int
    session_id: int
    role: Literal["user", "assistant"]
    content: str
    query: Optional[str] = None
    chart_config: Optional[Dict[str, Any]] = None
    created_at: str

class CreateSessionRequest(BaseModel):
    db_id: str
    title: Optional[str] = None
    project_id: Optional[int] = None

class Project(BaseModel):
    id: int
    user_id: str
    name: str
    created_at: str

class CreateProjectRequest(BaseModel):
    name: str

class InitialChatResponse(BaseModel):
    session: ChatSession
    messages: List[ChatMessageDB]
