from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatSession(BaseModel):
    id: int
    user_id: str
    db_id: str
    title: Optional[str] = "New Chat"
    project_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageDB(BaseModel):
    id: int
    session_id: int
    role: Literal["user", "assistant"]
    content: str
    query: Optional[str] = None
    chart_config: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    @field_validator('chart_config', 'results', mode='before')
    @classmethod
    def parse_json_fields(cls, v: Any) -> Optional[Dict[str, Any]]:
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v

    model_config = ConfigDict(from_attributes=True)

class CreateSessionRequest(BaseModel):
    db_id: str
    title: Optional[str] = None
    project_id: Optional[int] = None

class Project(BaseModel):
    id: int
    user_id: str
    name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CreateProjectRequest(BaseModel):
    name: str

class InitialChatResponse(BaseModel):
    session: ChatSession
    messages: List[ChatMessageDB]
