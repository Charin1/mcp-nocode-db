from pydantic import BaseModel
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatSession(BaseModel):
    id: int
    user_id: str  # We store email/username as ID in this system currently
    db_id: str
    title: Optional[str] = "New Chat"
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

class InitialChatResponse(BaseModel):
    session: ChatSession
    messages: List[ChatMessageDB]
