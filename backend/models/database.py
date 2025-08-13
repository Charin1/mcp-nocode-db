from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DBConnection(BaseModel):
    id: str
    name: str
    engine: str
    allow_mutations: bool

class AppConfig(BaseModel):
    databases: List[DBConnection]
    llm_providers: List[str]

class Schema(BaseModel):
    name: str # Table, collection, or index name
    type: str # 'table', 'view', 'collection', 'index'
    columns: Optional[List[Dict[str, Any]]] = None # For SQL
    fields: Optional[List[str]] = None # For NoSQL
    # Add other metadata as needed