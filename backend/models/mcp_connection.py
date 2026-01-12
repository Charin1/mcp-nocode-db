from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base

class MCPConnection(Base):
    __tablename__ = "mcp_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False) # Maps to User.username
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    headers = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MCPConnection(name={self.name}, url={self.url})>"
