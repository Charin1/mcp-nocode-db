from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base

class MCPConnection(Base):
    __tablename__ = "mcp_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False) # Maps to User.username
    name = Column(String, nullable=False)
    # connection_type: 'sse' or 'stdio'
    connection_type = Column(String, default="sse", nullable=False) 
    # url is deprecated but kept for compatibility, sync with configuration['url'] if type is sse
    url = Column(String, nullable=True) 
    # configuration: JSON blob for type-specific settings (e.g. command, args, env, or url)
    configuration = Column(JSON, default={}) 
    headers = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MCPConnection(name={self.name}, url={self.url})>"
