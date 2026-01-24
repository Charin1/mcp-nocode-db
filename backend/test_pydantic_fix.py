from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import json

class ChatMessageDB(BaseModel):
    id: int
    session_id: int
    role: Literal["user", "assistant"]
    content: str
    query: Optional[str] = None
    chart_config: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator('chart_config', 'results', mode='before')
    @classmethod
    def parse_json_fields(cls, v: Any) -> Optional[Dict[str, Any]]:
        print(f"Validator called with type: {type(v)} value: {v}")
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                print("JSON decode failed")
                return None
        return v

# Mock ORM object (just a class with attributes)
class MockORMMessage:
    def __init__(self):
        self.id = 1
        self.session_id = 10
        self.role = "assistant"
        self.content = "test"
        self.query = "SELECT 1"
        self.chart_config = '{"type": "bar"}' # String!
        self.results = '{"data": [1, 2, 3]}' # String!
        self.created_at = datetime.now()

def test_validation():
    orm_obj = MockORMMessage()
    try:
        model = ChatMessageDB.model_validate(orm_obj)
        print("Validation Successful!")
        print(f"Chart Config Type: {type(model.chart_config)}")
        print(f"Results Type: {type(model.results)}")
        print(f"Results Content: {model.results}")
    except Exception as e:
        print(f"Validation Failed: {e}")

if __name__ == "__main__":
    test_validation()
