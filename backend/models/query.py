from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class QueryRequest(BaseModel):
    db_id: str
    model_provider: str
    natural_language_query: str
    raw_query: Optional[str] = None
    # Flags from UI
    preview_only: bool = True
    confirm_execute: bool = False
    allow_mutations: bool = False  # This must be explicitly passed from the UI


class GeneratedQuery(BaseModel):
    raw_query: str
    params: Optional[Dict[str, Any]] = None  # For parameterized SQL
    query_type: str  # 'sql', 'mongo_json', 'redis_cli', etc.
    error: Optional[str] = None


class QueryResult(BaseModel):
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    json_result: Optional[Any] = None
    error: Optional[str] = None
    rows_affected: Optional[int] = None
    query_executed: str


class SavedQuery(BaseModel):
    id: Optional[int] = None
    username: str
    db_id: str
    name: str
    natural_language_query: Optional[str] = None
    raw_query: str
